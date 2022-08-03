import datetime
import json
import logging
import os
import re
import time
import unicodedata
from checkdigit import gs1
from flask import Blueprint, render_template, request, send_file, jsonify, make_response

import upc_logger.pdf_maker as pdf_maker


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
TEST_TEMPLATE = '_test1.html'

PDF_TITLE_STRF = '{client_name} order sheet - Crossmark.pdf'

STORE_INFO_FILE = './static/data/store_info.json'
STORE_INFO_JS_FILE = './static/data/store_info.js'
CATEGORIZED_STORES_FILE = './static/data/stores_list_for_dropdown.json'
CATEGORIZED_STORES_JAVASCRIPT_FILE = './static/data/stores_list_for_dropdown.js'

UNIQUE_UPCS_FILE_PATH = './upc_logger/data - product images/unique_upcs.json'

app_upc_logger = Blueprint('app_upc_logger', __name__)


class SessionTracker:
    grace_period_secs = 5 * 60
    sessions_json_path = './upc_logger/upc_logger_sessions.json'
    sessions = {}
    # Session skeleton
    # SESSION = {
    #     'previous_store': None,
    #     'time_last_processed_secs': 0
    # }

    @classmethod
    def load_sessions(cls):
        if not os.path.isfile(cls.sessions_json_path):
            cls.save_sessions()

        with open(cls.sessions_json_path, 'r', encoding='utf8') as fd:
            cls.sessions = json.load(fd)

    @classmethod
    def save_sessions(cls):
        with open(cls.sessions_json_path, 'w', encoding='utf8') as fd:
            json.dump(cls.sessions, fd, indent=4)

    @classmethod
    def reset_time(cls, ip_address: str):
        session = cls.sessions.get(ip_address, None)
        if session is None:
            cls.sessions[ip_address] = {}

        cls.sessions[ip_address]['time_last_processed_secs'] = 0

    @classmethod
    def update_store(cls, store: str, ip_address: str):
        session = cls.sessions.get(ip_address, None)
        if session is None:
            cls.sessions[ip_address] = {}

        cls.sessions[ip_address]['previous_store'] = store
        cls.sessions[ip_address]['time_last_processed_secs'] = time.time()

    @classmethod
    def get_previous_store(cls, ip_address: str) -> str:
        return cls.sessions.get( ip_address, {} ).get('previous_store', None)

    @classmethod
    def is_continue_previous_store(cls, ip_address: str) -> bool:
        return abs(time.time() - cls.sessions.get( ip_address, {} ).get('time_last_processed_secs', 0) ) < cls.grace_period_secs


def mirror_to_js(obj_: dict):
    output = 'CATEGORIZED_STORES = ' + json.dumps(obj_, indent=4) + ';'

    with open(CATEGORIZED_STORES_JAVASCRIPT_FILE, 'w', encoding='utf8') as fd:
        fd.write(output)


# @app_upc_logger.after_request
# def add_header(r):
#     """
#     Add headers to both force latest IE rendering engine or Chrome Frame,
#     and also to cache the rendered page for 10 minutes.
#     """
#     r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
#     r.headers["Pragma"] = "no-cache"
#     r.headers["Expires"] = "0"
#     return r


# @app_upc_logger.route('/test', methods=["GET"])
# def test():
#     logger.info('\n')
#     logger.info('  >> Route: test <<')
#     SessionTracker.load_sessions()

#     with open(CATEGORIZED_STORES_FILE, 'r', encoding='utf8') as fd:
#         categorized_stores = json.load(fd)

#     mirror_to_js(categorized_stores)

#     upc = request.args.get('upc', '')
#     ip_address = request.headers['X-Real-IP']

#     stores = _get_stores_data()
#     stores_list = [f for f in stores.keys() if f != 'all']

#     SessionTracker.save_sessions()

#     logger.info('Returning with HTML response')
#     return render_template(
#         TEST_TEMPLATE,
#         upc=upc,
#         stores=stores_list,
#         is_continue_previous_store=SessionTracker.is_continue_previous_store(ip_address),
#         previous_store=SessionTracker.get_previous_store(ip_address),
#         categorized_stores=categorized_stores
#     )


@app_upc_logger.route("/upc_log_form")
def log_form_route():
    logger.info('\n')
    logger.info('  >> Route: log_form <<')
    SessionTracker.load_sessions()

    with open(CATEGORIZED_STORES_FILE, 'r', encoding='utf8') as fd:
        categorized_stores = json.load(fd)

    mirror_to_js(categorized_stores)

    upc = request.args.get('upc', '')
    ip_address = request.headers['X-Real-IP']

    stores = _get_stores_data()
    stores_list = [f for f in stores.keys() if f != 'all']

    SessionTracker.save_sessions()

    logger.info('Returning with HTML response')
    return render_template(
        UPC_LOG_FORM_HTML_TEMPLATE,
        upc=upc,
        stores=stores_list,
        is_continue_previous_store=SessionTracker.is_continue_previous_store(ip_address),
        previous_store=SessionTracker.get_previous_store(ip_address),
        categorized_stores=categorized_stores
    )


@app_upc_logger.route("/direct_update", methods=['GET', 'POST'])
def direct_update_route():
    if request.method != 'POST':
        return jsonify( {'message': 'Received no data'} ), 400

    logger.info('\n')
    logger.info('  >> Route: direct_update <<')

    SessionTracker.load_sessions()
    content = request.json
    logger.info(content)
    ret_data = {'message': 'Internal server did not complete intended action'}
    ret_code = 400

    # if len(content['upc']) != 12:
    #     logger.info(f'Length of "{content["upc"]}" is {len(content["upc"])}, instead of the required 12')
    #     return jsonify( {'message': f'Length of "{content["upc"]}" is {len(content["upc"])}, instead of the required 12'} ), 400

    ip_address = request.headers['X-Real-IP']
    SessionTracker.update_store(content['store'], ip_address)
    if content.get('store_reset') is not None:
        SessionTracker.reset_time(ip_address)

    if content['action'] == 'remove':
        _remove_upc(content['upc'], content['store'])
        ret_data['message'] = f'Removed UPC {content["upc"]}'
        ret_code = 200
    elif content['action'] == 'add':
        _add_upc_from_scan(content['upc'], content['store'])
        ret_data['message'] = f'Added UPC {content["upc"]}'
        ret_code = 200

    SessionTracker.save_sessions()
    return jsonify( ret_data ), ret_code


@app_upc_logger.route("/barcode_getter", methods=["POST", "OPTIONS"])
def get_barcodes_pdf_route():
    logger.info('\n')
    logger.info('  >> Route: get_barcodes_pdf <<')

    if request.method == "OPTIONS": # CORS preflight
        logger.info('Building preflight response')
        return _build_cors_preflight_response()
    elif request.method != 'POST':
        return _corsify_actual_response( jsonify( {'message': 'Invalid request'} ) ), 400

    allowed_authorization_key = 'hello there'
    received_auth_key = request.headers.get("Authorization")
    if received_auth_key is None or received_auth_key != allowed_authorization_key:
        return _corsify_actual_response( jsonify( {'message': 'invalid auth key'} ) ), 401

    request_types_to_templates = {
        'all': '{client_name} item sheet - {item_count} items.pdf',
        'out_of_dist': '{client_name} order sheet - {date} - {store_name}.pdf',
        'in_dist': '{client_name} in-stock sheet - {date} - {store_name}.pdf'
    }

    client_name = request.json['client_name']
    store_name = request.json['store_name']
    shortened_store_name = request.json['shortened_store_name']
    items = request.json['items']

    add_upcs_to_uniques_file(items)
    logger.info('Adding UPCs in bulk to json')
    store_data = _add_items_in_bulk(items.keys(), store_name)
    include_upc_time_added(items, store_data)

    logger.info(f'> Received {len(items)} {client_name} items')

    filename_template = request_types_to_templates[request.json['barcode_request_type']]
    filename = get_filename(client_name, shortened_store_name, len(items), filename_template)
    pdf_path = os.path.join('upc_logger/generated_pdfs', filename)

    logger.info('> Looking up UPC data')
    pdf_maker.lookup_upc_data(items, client_name)
    logger.info('> Logging product names')
    pdf_maker.log_product_names(items, client_name)
    logger.info('> Creating PDF')
    pdf_maker.create_pdf_with_upcs(items, pdf_path, client_name)

    logger.info('> Returning with PDF attachment')
    resp = send_file(pdf_path, as_attachment=True, cache_timeout=0)
    resp.headers.add("filename", filename)
    resp.headers.add('Access-Control-Allow-Origin', '*')
    resp.headers.add("Access-Control-Expose-Headers", 'filename')
    resp.headers.add("Access-Control-Expose-Headers", 'Content-Disposition')
    resp.headers.add('mimetype', 'application/pdf')

    return resp


@app_upc_logger.route("/add_items_in_bulk", methods=["POST", "OPTIONS"])
def add_items_in_bulk_route():
    logger.info('\n')
    logger.info('  >> Route: add_items_in_bulk <<')

    if request.method == "OPTIONS": # CORS preflight
        logger.info('Building preflight response')
        return _build_cors_preflight_response()
    elif request.method != 'POST':
        return _corsify_actual_response( jsonify( {'message': 'Invalid request'} ) ), 400

    store_name = request.json['store_name']
    upcs = request.json['upcs']

    logger.info('Adding UPCs in bulk to json')
    _add_items_in_bulk(upcs, store_name)

    logger.info('Returning with success JSON msg')
    return _corsify_actual_response( jsonify( {"message": f"Success. Received store '{store_name}' and {len(upcs)} UPCs"} ) )


def add_upcs_to_uniques_file(items: dict):
    with open(UNIQUE_UPCS_FILE_PATH, 'r', encoding='utf8') as fd:
        unique_upcs = json.load(fd)

    for upc in items:
        if upc not in unique_upcs:
            unique_upcs[upc] = {'time_added': time.time()}

    with open(UNIQUE_UPCS_FILE_PATH, 'w', encoding='utf8') as fd:
        json.dump(unique_upcs, fd, indent=4)

    return unique_upcs


def include_upc_time_added(items: dict, store_data: dict):
    for upc, data in items.items():
            data['time_added'] = store_data[upc].get('time_added', 0)


@app_upc_logger.route("/stores_data.json", methods=["GET", "OPTIONS"])
def get_stores_data_route():
    def _corsify_this(response):
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Content-Type', 'application/json')
        response.headers.add("Cache-Control", "no-cache, no-store, must-revalidate, public, max-age=0")
        response.headers.add("Pragma", "no-cache")
        response.headers.add("Expires", "0")
        return response

    logger.info('\n')
    logger.info('  >> Route: stores_data_getter <<')

    if request.method == "OPTIONS": # CORS preflight
        logger.info('Building preflight response')
        return _build_cors_preflight_response()
    elif request.method != 'GET':
        logger.info('Request method is not GET')
        return _corsify_actual_response( jsonify( {'message': 'Invalid request'} ) ), 400

    logger.info('Returning with stores_data')
    stores_data: dict = _get_stores_data()
    return _corsify_this( jsonify(stores_data) )


def _build_cors_preflight_response():
    response = make_response()

    response.headers.add("Access-Control-Allow-Origin", '*')
    response.headers.add('Access-Control-Allow-Headers', "Content-Type")
    response.headers.add('Access-Control-Allow-Headers', "Authorization")
    # response.headers.add('Access-Control-Allow-Methods', "*")

    response.headers.add('Content-Type', 'application/json')
    # response.headers.add('Authorization', allowed_authorization_key)

    return response


def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


def empty_dir(target_dir: str):
    for f in os.listdir(target_dir):
        file_path = os.path.join(target_dir, f)
        if os.path.isfile(file_path):
            os.unlink(file_path)


def get_filename(client_name: str, store_name: str, item_count: int, filename_template: str) -> str:
    ts = time.time() - (4 * 3600)
    now = datetime.datetime.utcfromtimestamp(ts).strftime('%a, %b %-d, %Y')
    store_name = slugify(store_name)

    return filename_template.format(
        client_name=client_name.upper(),
        item_count=item_count,
        date=now,
        store_name=store_name
    )


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


def _remove_upc(upc: str, store_name):
    logger.info('\n')
    logger.info('>> remove_upc <<')
    stores = _get_stores_data()

    popped_item = stores[store_name].pop(upc, None)
    logger.info(f'Popped from dict: key {repr(upc)} == {popped_item}')

    _update_stores_data(stores)


def _add_upc_from_scan(upc: str, store_name: str) -> dict:
    '''
    updates data with upc and store_name passed in
    '''
    logger.info('\n')
    logger.info('>> add_upc <<')

    stores_data: dict = _get_stores_data()
    ts = time.time() - (4 * 3600)
    now: str = datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d at %I:%M:%S %p')

    logger.info(f'Adding {upc} to dict')
    if store_name not in stores_data:
        stores_data[store_name] = {}

    if upc not in stores_data[store_name]:
        stores_data[store_name][upc] = {}
        stores_data[store_name][upc]['time_added'] = time.time()

    stores_data[store_name][upc]['instock'] = True
    stores_data[store_name][upc]['time_scanned'] = now

    logger.info(f'Added to dict: key {repr(upc)}, store: {store_name}')
    _update_stores_data(stores_data)


def _add_items_in_bulk(upcs: list, store_name: str):
    logger.info('\n')
    logger.info('  >> _add_items_in_bulk() <<')

    stores_data = _get_stores_data()

    if stores_data.get(store_name) is None:
        stores_data[store_name] = {}

    is_update_occurred = False
    for upc in upcs:
        if upc not in stores_data[store_name]:
            logger.info(f'Adding "{upc}" to stores data JSON')
            is_update_occurred = True

            stores_data[store_name][upc] = {}
            stores_data[store_name][upc]['instock'] = False
            # stores_data[store_name][upc]['time_added'] = time.time()

    if is_update_occurred:
        _update_stores_data(stores_data)
    else:
        logger.info('Added 0 items to stores data JSON')

    return stores_data[store_name]


def _update_stores_data(stores: dict):
    with open(STORE_INFO_FILE, 'w', encoding='utf8') as fd:
        json.dump(stores, fd, indent=4)

    data_str = json.dumps(stores, indent=4)
    data_str = 'var STORES = ' + data_str + ';'
    with open(STORE_INFO_JS_FILE, 'w', encoding='utf8') as fd:
        fd.write(data_str)


def _get_stores_data() -> dict:
    with open(STORE_INFO_FILE, 'r', encoding='utf8') as fd:
        return json.load(fd)

