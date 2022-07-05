import barcode
import datetime
import io
import json
import logging
import os
import re
import requests
import time
import unicodedata
from textwrap import wrap
from flask import Blueprint, render_template, request, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from checkdigit import gs1
from barcode.writer import ImageWriter

##
LOG_FILE_PATH = os.path.join( os.path.dirname(__file__), 'upc_logger.log' )

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('\n%(asctime)s - [MODULE] %(module)s - [LINE] %(lineno)d - [MSG] %(message)s')
file_handler = logging.FileHandler(LOG_FILE_PATH)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
##

INDEX_HTML_TEMPLATE = 'index.html'
UPC_LOG_FORM_HTML_TEMPLATE = 'upc_log_form.html'
UPC_LOG_FINAL_HTML_TEMPLATE = 'upc_log_final.html'

PDF_TITLE_STRF = '{client_name} order sheet - Crossmark.pdf'

STORE_INFO_FILE = './static/store_info.json'
STORE_INFO_JS_FILE = './static/store_info.js'
app_upc_logger = Blueprint('app_upc_logger', __name__)

class SessionTracker:
    grace_period_secs = 5 * 60
    last_processed_secs = 0
    previous_store = None

    @classmethod
    def reset_time(cls):
        cls.last_processed_secs = 0

    @classmethod
    def update_store(cls, store: str):
        cls.previous_store = store
        cls.last_processed_secs = time.time()

    @classmethod
    def get_previous_store(cls) -> str:
        return cls.previous_store

    @classmethod
    def is_continue_previous_store(cls) -> bool:
        return abs(time.time() - cls.last_processed_secs) < cls.grace_period_secs


@app_upc_logger.route("/test1")
def test1_route():
    HTML_TEMPLATE_FILE_PATH = '_test1.html'

    return render_template(HTML_TEMPLATE_FILE_PATH, stores=[1, 2])

@app_upc_logger.route("/upc_log_form")
def route_log():
    _assert_settings(request)
    upc = request.args.get('upc')

    if request.args.get("reset-store", default=False, type=bool):
        SessionTracker.reset_time()
        if request.args.get("remove-upc", default=False, type=bool):
            store_name = request.args.get('store')
            remove_upc(upc, store_name)

    stores = _get_stores()
    stores_list = [f for f in stores.keys() if f != 'all']
    return render_template(
        UPC_LOG_FORM_HTML_TEMPLATE,
        upc=upc,
        stores=stores_list,
        is_continue_previous_store=SessionTracker.is_continue_previous_store(),
        previous_store=SessionTracker.get_previous_store()
    )


@app_upc_logger.route("/upc_log_final")
def route_log_final():
    upc = request.args.get('upc')
    store = request.args.get('store')
    SessionTracker.update_store(store)
    _dump_data(upc, store)

    return render_template(UPC_LOG_FINAL_HTML_TEMPLATE, upc=upc, store=store)


@app_upc_logger.route("/barcode_getter")
def barcode_getter():
    client_name = request.args.get('client-name')
    store_name = request.args.get('store-name')
    product_names = request.args.getlist("product-names")
    product_names = [f.strip() for f in product_names]

    urls = request.args.getlist("urls")
    trunc_upcs = request.args.getlist("upcs")

    pdf_dir = 'upc_logger/generated_pdfs'
    empty_dir(pdf_dir)

    filename = get_filename(client_name, store_name)
    pdf_path = os.path.join(pdf_dir, filename)

    if urls:
        create_pdf_with_imgs(urls, product_names, pdf_path, client_name)
    elif trunc_upcs:
        create_pdf_with_upcs(trunc_upcs, product_names, pdf_path, client_name)

    return send_file(pdf_path, as_attachment=True, cache_timeout=0)


def empty_dir(target_dir: str):
    for f in os.listdir(target_dir):
        file_path = os.path.join(target_dir, f)
        if os.path.isfile(file_path):
            os.unlink(file_path)


def get_filename(client_name: str, store_name: str) -> str:
    ts = time.time() - (4 * 3600)
    now = datetime.datetime.utcfromtimestamp(ts).strftime('%a, %b %-d, %Y')
    store_name = slugify(store_name)

    return f'{client_name.upper()} OOS order sheet - {now} - {store_name}.pdf'


def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value)
    return re.sub(r'[-\s]+', ' ', value).strip('-_')


def create_pdf_with_upcs(trunc_upcs: list, product_names: list, pdf_path: str, client_name: str):
    pdf_canvas = canvas.Canvas(pdf_path)
    pdf_canvas.setFont("Helvetica", 11)
    pdf_canvas.setTitle( PDF_TITLE_STRF.format(client_name=client_name.upper()) )
    start_x, start_y = 10, 720
    x, y = start_x, start_y

    start_digit = '0'
    if client_name == 'yasso':
        start_digit = '8'

    for i, trunc_upc in enumerate(trunc_upcs):
        full_upc = start_digit + trunc_upc
        full_upc = full_upc + gs1.calculate(full_upc)

        upc_obj = barcode.get('upc', full_upc, writer=ImageWriter())
        image = ImageReader( upc_obj.render() )

        max_length = 26
        product_name_split = wrap(product_names[i], max_length)[:3]
        temp_x, temp_y = x, y
        for product_name in product_name_split:
            pdf_canvas.drawString(temp_x + 10, temp_y, product_name.center(max_length))
            temp_y -= 13
        pdf_canvas.drawImage(image, x, y, 6*cm, 4*cm, preserveAspectRatio=True)

        x += 200
        if x >= 600:
            x = start_x
            y -= 160
        if y < 40:
            x = 10
            y = start_y
            pdf_canvas.showPage()

    pdf_canvas.save()


def create_pdf_with_imgs(urls: list, product_names: list, pdf_path: str, client_name: str):
    pdf_canvas = canvas.Canvas(pdf_path)
    pdf_canvas.setTitle( PDF_TITLE_STRF.format(client_name=client_name.upper()) )
    start_x, start_y = 10, 720
    x, y = start_x, start_y

    img_to_text_diff = {'lav': 12}.get(client_name, 0)
    img_to_img_diff = {
        'lav': 180,
        'yasso': 130
    }.get(client_name, 150)

    for i, url in enumerate(urls):
        data = requests.get(url).content
        image = ImageReader(io.BytesIO(data))

        max_length = 24
        product_name_split = wrap(product_names[i], max_length)[:3]
        temp_x, temp_y = x, y
        for product_name in product_name_split:
            pdf_canvas.drawString(temp_x + 4, temp_y - img_to_text_diff, product_name.center(max_length))
            temp_y -= 13

        pdf_canvas.drawImage(image, x, y, 6*cm, 4*cm, preserveAspectRatio=True)

        x += 200
        if x >= 600:
            x = start_x
            y -= img_to_img_diff
        if y < 40:
            x = 10
            y = start_y
            pdf_canvas.showPage()

    pdf_canvas.save()


def remove_upc(upc: str, store_name):
    stores = _get_stores()

    truncated_upc = upc[1:-1]
    popped_item = stores[store_name].pop(truncated_upc, None)
    logger.info(f'Popped {popped_item} from dict')

    _update_stores(stores)


def _get_stores() -> dict:
    with open(STORE_INFO_FILE, 'r', encoding='utf8') as fd:
        return json.load(fd)


def _dump_data(upc: str, store_name: str) -> dict:
    ts = time.time() - (4 * 3600)
    now = datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d at %I:%M:%S %p')
    stores = _get_stores()
    truncated_upc = upc[1:-1]
    surrounding_digits = [upc[0], upc[-1]]

    if stores[store_name].get(truncated_upc) is not None:
        stores[store_name][truncated_upc]['instock'] = True
        stores[store_name][truncated_upc]['time_scanned'] = now
        stores[store_name][truncated_upc]['surrounding_digits'] = surrounding_digits

    else:
        stores[store_name][truncated_upc] = {
            'instock': True,
            'time_scanned': now,
            'surrounding_digits': surrounding_digits
        }

    _update_stores(stores)


def _update_stores(stores: dict):
    with open(STORE_INFO_FILE, 'w', encoding='utf8') as fd:
        json.dump(stores, fd, indent=4)

    data_str = json.dumps(stores, indent=4)
    data_str = 'var STORES = ' + data_str + ';'
    with open(STORE_INFO_JS_FILE, 'w', encoding='utf8') as fd:
        fd.write(data_str)


def _assert_settings(request: object) -> object:
    font_size = 18

    if not os.path.isfile(STORE_INFO_FILE):
        return render_template(INDEX_HTML_TEMPLATE, font_size=font_size, message='Error. No JSON file found.')

    upc = request.args.get('upc', default=None, type=str)
    if upc is None or upc == '':
        return render_template(INDEX_HTML_TEMPLATE, font_size=font_size, message='Error. No UPC scanned.')
