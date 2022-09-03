import datetime
import json
import logging
import os
import re
import time
import unicodedata
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


UPC_LOG_FORM_HTML_TEMPLATE = 'upc_log_form.html'
TEST_TEMPLATE = '_test1.html'

STORES_DATA_FILE_PATH = './static/data/stores_data.json'
CATEGORIZED_STORES_FILE = './static/data/categorized_store_listings.json'

app_upc_logger = Blueprint('app_upc_logger', __name__)


@app_upc_logger.route("/managers_form")
def managers_form_route():
    logger.info('\n')
    logger.info('  >> Route: managers_form <<')

    template_path = 'get_managers.html'

    categorized_stores = balance_categorized_stores_info()
    all_stores_data = categorized_stores.pop('All Stores')

    logger.info('Returning with HTML Response')
    return render_template(template_path, categorized_stores=categorized_stores, all_stores_data=all_stores_data)


def balance_categorized_stores_info():
    with open(CATEGORIZED_STORES_FILE, 'r', encoding='utf8') as fd:
        categorized_stores_with_info = json.load(fd)

    for name, data in categorized_stores_with_info.items():
        if name == 'All Stores':
            continue

        for store in data:
            if store not in categorized_stores_with_info['All Stores']:
                logger.info(f'"{store}" not in "All Stores" info')
                categorized_stores_with_info['All Stores'][store] = {
                    "manager_names": [
                        "",
                        ""
                    ]
                }

    with open(CATEGORIZED_STORES_FILE, 'w', encoding='utf8') as fd:
        json.dump(categorized_stores_with_info, fd, indent=4)

    return categorized_stores_with_info


def get_categorized_stores_for_log_form() -> dict:
    with open(CATEGORIZED_STORES_FILE, 'r', encoding='utf8') as fd:
        categorized_stores_with_info = json.load(fd)

    categorized_stores = {}
    for name, data in categorized_stores_with_info.items():
        if name != 'All Stores':
            categorized_stores[name] = data
        else:
            categorized_stores[name] = list(data.keys())

    return categorized_stores


@app_upc_logger.route("/accept_manager_info", methods=['GET', 'POST'])
def accept_manager_info_route():
    if request.method == 'GET':
        return render_template('accept_manager_info.html', history_replace=False)

    logger.info('\n')
    logger.info('  >> Route: accept_manager_info <<')

    with open(CATEGORIZED_STORES_FILE, 'r', encoding='utf8') as fd:
        categorized_stores_with_info = json.load(fd)

    employee_name = request.form['employee-name']

    logger.info('\n')
    for i, first_name_from_form in enumerate(request.form.getlist('first-name')):
        store_name = categorized_stores_with_info[employee_name][i]
        last_name_from_form = request.form.getlist('last-name')[i]

        target_dict = categorized_stores_with_info['All Stores'][store_name]
        original_full_name = target_dict['manager_names'][0] + ' ' + target_dict['manager_names'][1]
        new_full_name = first_name_from_form + ' ' + last_name_from_form

        if original_full_name != new_full_name:
            logger.info( 'Replacing name "{}" with "{}" for store {}'.format(original_full_name, new_full_name, store_name) )

        target_dict['manager_names'][0] = first_name_from_form
        target_dict['manager_names'][1] = last_name_from_form

    with open(CATEGORIZED_STORES_FILE, 'w', encoding='utf8') as fd:
        json.dump(categorized_stores_with_info, fd, indent=4)

    return render_template('accept_manager_info.html', history_replace=True)


@app_upc_logger.route("/upc_log_form")
def log_form_route():
    def get_previous_store_info(cookies) -> tuple:
        grace_period_secs = 5 * 60

        prev_store_from_cookie = cookies.get('previous_store')
        previous_unix_log_time_from_cookie = cookies.get('previous_unix_log_time', 0)
        previous_unix_log_time_from_cookie = int(previous_unix_log_time_from_cookie)
        logger.info(f'Info from cookie: prev store: {repr(prev_store_from_cookie)} - prev time: {repr(previous_unix_log_time_from_cookie)}')

        if prev_store_from_cookie is None:
            return False, 'None'
        elif abs(time.time() - previous_unix_log_time_from_cookie) < grace_period_secs:
            return True, prev_store_from_cookie

        return False, prev_store_from_cookie


    '''
    returns HTML template to receive a UPC from a scan and allow the user to pick their desired store for which to log the UPC
    '''
    logger.info('\n')
    logger.info('  >> Route: log_form <<')

    categorized_stores = get_categorized_stores_for_log_form()
    upc = request.args.get('upc', '')

    is_continue_previous_store, previous_store = get_previous_store_info(request.cookies)
    logger.info(f'Continuing with previous store: {is_continue_previous_store}')

    stores = _get_stores_data()
    stores_list = [f for f in stores.keys() if f != 'all']

    logger.info('Returning with HTML response')
    return render_template(
        UPC_LOG_FORM_HTML_TEMPLATE,
        upc=upc,
        stores=stores_list,
        is_continue_previous_store=is_continue_previous_store,
        previous_store=previous_store,
        categorized_stores=categorized_stores
    )


@app_upc_logger.route("/direct_update", methods=['POST'])
def direct_update_route():
    '''
    A POST endpoint which to send UPC data, in order to store the received UPC and associated information to database
    and mark the UPC in database as being carried by the store as indicated in the received JSON object
    '''
    if request.method != 'POST':
        return jsonify( {'message': 'Received no data'} ), 400

    logger.info('\n')
    logger.info('  >> Route: direct_update <<')

    content = request.json
    logger.info(content)
    ret_data = {'message': 'Internal server did not complete intended action'}
    ret_code = 400

    if content['action'] == 'remove':
        _remove_upc(content['upc'], content['store'])
        ret_data['message'] = f'Removed UPC {content["upc"]}'
        ret_code = 200
    elif content['action'] == 'add':
        _add_upc_from_scan(content['upc'], content['store'])
        ret_data['message'] = f'Added UPC {content["upc"]}'
        ret_code = 200

    return jsonify( ret_data ), ret_code


@app_upc_logger.route("/barcode_getter", methods=["POST", "OPTIONS"])
def get_barcodes_pdf_route():
    '''
    A POST endpoint that receives a JSON object of UPC numbers and associated information;
    returns a PDF document as an attachment to download client-side containing product details, barcodes and product images
    '''
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
        'in_dist': '{client_name} in-stock sheet - {date} - {store_name}.pdf',
        'all_no_new_item_icon': '{client_name} item sheet - {item_count} items - {date}.pdf'
    }

    client_name = request.json['client_name']
    store_name = request.json['store_name']
    shortened_store_name = request.json['shortened_store_name']
    items = request.json['items']

    logger.info(f'> Received {len(items)} {client_name} items for store "{store_name}"')
    logger.info('Adding UPCs in bulk to json')
    store_data = _add_items_in_bulk(items.keys(), store_name)
    include_upc_time_added(items, store_data)

    is_include_new_item_icon = True
    if request.json['barcode_request_type'] == 'all_no_new_item_icon':
        is_include_new_item_icon = False
    filename_template = request_types_to_templates[request.json['barcode_request_type']]
    filename = get_filename(client_name, shortened_store_name, len(items), filename_template)
    pdf_path = os.path.join('upc_logger/generated_pdfs', filename)

    logger.info('> Looking up UPC data')
    pdf_maker.lookup_upc_data(items, client_name)
    logger.info('> Logging product names')
    pdf_maker.log_product_names(items, client_name)
    logger.info('> Creating PDF')
    pdf_maker.create_pdf_with_upcs(items, pdf_path, client_name, is_include_new_item_icon)

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
    '''
    A POST endpoint which receives a JSON object containing UPC numbers
    for the purpose of storing all UPCs to database
    '''
    logger.info('\n')
    logger.info('  >> Route: add_items_in_bulk <<')

    if request.method == "OPTIONS": # CORS preflight
        logger.info('Building preflight response')
        return _build_cors_preflight_response()
    elif request.method != 'POST':
        return _corsify_actual_response( jsonify( {'message': 'Invalid request'} ) ), 400

    allowed_authorization_key = 'Resent#Choosy5#Snowless'
    received_auth_key = request.headers.get("Authorization")
    if received_auth_key is None or received_auth_key != allowed_authorization_key:
        return _corsify_actual_response( jsonify( {'message': 'invalid auth key'} ) ), 401

    store_name = request.json['store_name']
    client_name = request.json['client_name']
    upcs_received = request.json['upcs']

    logger.info(f'Processing {len(upcs_received)} {client_name} UPCs for store "{store_name}"')
    this_cycle_half_start_time, next_cycle_half_start_time = pdf_maker.update_cycle_info()

    logger.info('Adding UPCs in bulk to json')
    store_data = _add_items_in_bulk(upcs_received, store_name)

    new_upcs = []
    for upc, upc_data in store_data.items():
        if upc not in upcs_received:
            continue

        time_added = upc_data.get('time_added', 0)
        if this_cycle_half_start_time < time_added and time_added < next_cycle_half_start_time:
            logger.info(f'UPC "{upc}" is new; add time: {time_added}')
            new_upcs.append(upc)

    ret_json = {
        'message': 'Success',
        'data': {
            'new_upcs': new_upcs
        }
    }

    logger.info('Returning with success JSON msg')
    return _corsify_actual_response( jsonify( ret_json ) )


def include_upc_time_added(items: dict, store_data: dict):
    '''
    :param items dict: A dict of {upc: {}} data received from client-side containing UPC numbers as keys, and their associated data, which
    includes product name
    :param store_data dict: A dict of {upc: {}} data obtained from database that contains UPC numbers as keys, and
    their associated data, which includes a 'instock' bool attribute, 'time_added' UNIX timestamp, and 'date_scanned', localized to EST timezone
    '''
    for upc, data in items.items():
            data['time_added'] = store_data[upc].get('time_added', 0)


@app_upc_logger.route("/get-json/<filename>", methods=["GET", "OPTIONS"])
def get_json_route(filename):
    def _corsify_this(response):
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Content-Type', 'application/json')
        response.headers.add("Cache-Control", "no-cache, no-store, must-revalidate, public, max-age=0")
        response.headers.add("Pragma", "no-cache")
        response.headers.add("Expires", "0")
        return response

    logger.info('\n')
    logger.info('  >> Route: get_json <<')

    if request.method == "OPTIONS": # CORS preflight
        logger.info('Building preflight response')
        return _build_cors_preflight_response()
    elif request.method != 'GET':
        logger.info('Request method is not GET')
        return _corsify_actual_response( jsonify( {'message': 'Invalid request'} ) ), 400

    logger.info(f'Returning with {filename}')

    file_path = f'static/data/{filename}'
    if not os.path.isfile(file_path):
        return _corsify_actual_response( jsonify( {'message': 'Invalid request. JSON filename not found'} ) ), 400

    with open(file_path, 'r', encoding='utf8') as fd:
        data = json.load(fd)

    return _corsify_this( jsonify(data) )


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


def get_filename(client_name: str, store_name: str, item_count: int, filename_template: str) -> str:
    '''
    Intended to generated a relevant filename in order to return to client-side a PDF attachment of barcodes and other product information
    :param client_name str: Name of brand/account in full uppercase
    :param store_name str: Name of store
    :param item_count int: Number of items (UPCs) received from client-side
    :param filename_template str: a string template to subtitute in the relevant attributes

    '''
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
    '''
    Changes the 'instock' attribute for a particular store in database
    :param upc str: UPC number
    :param store_name str: Name of store from which to change the 'instock' attribute for the UPC indicated
    '''
    logger.info('\n')
    logger.info('>> remove_upc <<')
    stores = _get_stores_data()

    stores[store_name][upc]['instock'] = False
    logger.info(f'Changed "instock" attribute to False for UPC "{upc}" at store "{store_name}"')

    _update_stores_data(stores)


def _add_upc_from_scan(upc: str, store_name: str) -> dict:
    '''
    updates data with upc and store_name passed in
    '''
    logger.info('\n')
    logger.info('>> add_upc <<')

    stores_data: dict = _get_stores_data()
    ts: float = time.time() - (4 * 3600)
    now: str = datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d at %I:%M:%S %p')

    logger.info(f'Adding {upc} to dict')
    if store_name not in stores_data:
        stores_data[store_name] = {}

    if upc not in stores_data[store_name]:
        stores_data[store_name][upc] = {}
        stores_data[store_name][upc]['time_added'] = time.time()

    stores_data[store_name][upc]['instock'] = True
    stores_data[store_name][upc]['date_scanned'] = now

    logger.info(f'Added to dict: key {repr(upc)}, store: {store_name}')
    _update_stores_data(stores_data)


def _add_items_in_bulk(upcs: list, store_name: str):
    logger.info('\n')
    logger.info('  >> _add_items_in_bulk() <<')

    ts: float = time.time() - (4 * 3600)
    now: str = datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d at %I:%M:%S %p')

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
            stores_data[store_name][upc]['time_added'] = time.time()
            stores_data[store_name][upc]['date_added'] = now

    if is_update_occurred:
        _update_stores_data(stores_data)
    else:
        logger.info('Added 0 items to stores data JSON')

    return stores_data[store_name]


def _update_stores_data(stores: dict):
    with open(STORES_DATA_FILE_PATH, 'w', encoding='utf8') as fd:
        json.dump(stores, fd, indent=4)


def _get_stores_data() -> dict:
    with open(STORES_DATA_FILE_PATH, 'r', encoding='utf8') as fd:
        return json.load(fd)

