import datetime
import json
import logging
import os
import time
from flask import Blueprint, render_template, session, abort, request, Markup

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

STORE_INFO_FILE = './static/store_info.json'
STORE_INFO_JS_FILE = './static/store_info.js'
app_upc_logger = Blueprint('app_upc_logger', __name__)

class LastRequest:
    time_secs_before_asking_again = 15
    time_last_processed = 0
    previous_store = None

    @classmethod
    def update_store(store: str):
        cls.previous_store = store
        cls.time_last_processed = time.time()

    @classmethod
    def get_previous_store(cls) -> str:
        if abs(time.time() - cls.time_last_processed) < time_secs_before_asking_again:
            return cls.previous_store
        return None


@app_upc_logger.route("/upc_log_form")
def route_log():
    _assert_settings(request)
    upc = request.args.get('upc')

    if LastRequest.get_previous_store() is not None:
        return(f'{upc}<br><br>{LastRequest.get_previous_store()}')
    else:
        return 'Previous store returned None, choose from the dropdown again'

    stores = get_stores()
    # stores = dump_data(stores)

    stores_list = [f for f in stores.keys() if f != 'all']
    return render_template(UPC_LOG_FORM_HTML_TEMPLATE, upc_scanned=upc, stores=stores_list)


@app_upc_logger.route( "/upc_log_final", methods=['GET', 'POST'] )
def route_log_final():
    if request.method == 'POST':
        upc = request.form.get('upc_value')
        store = request.form.get('store_value')
        LastRequest.update_store(store)

        return(f'"{upc}"<br><br>"{store}"<br><br>') # just to see what select is


def get_stores() -> dict:
    with open(STORE_INFO_FILE, 'r', encoding='utf8') as fd:
        return json.load(fd)


def dump_data() -> dict:
    ts = time.time() - (4 * 3600)
    now = datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d at %I:%M:%S %p')
    stores['all'][upc] = now

    with open(STORE_INFO_FILE, 'w', encoding='utf8') as fd:
        json.dump(stores, fd, indent=4)

    data_str = json.dumps(stores, indent=4)
    data_str = 'var STORES = ' + data_str + ';'
    with open(STORE_INFO_JS_FILE, 'w', encoding='utf8') as fd:
        fd.write(data_str)

    return stores


def _assert_settings(request: object) -> object:
    font_size = 18

    if not os.path.isfile(STORE_INFO_FILE):
        return render_template(INDEX_HTML_TEMPLATE, font_size=font_size, message=f'Error. No JSON file found.')

    upc = request.args.get('upc', default=None, type=str)
    if upc is None or upc == '':
        return render_template(INDEX_HTML_TEMPLATE, font_size=font_size, message='Error. No UPC scanned.')
