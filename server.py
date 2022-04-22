import json
import logging
import os
import re
from string import Template
from flask import Flask, request, render_template, Markup

app = Flask(__name__)

#
LOG_FILE_PATH = os.path.join( os.path.dirname(__file__), 'upc_checker.log' )

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('\n%(asctime)s - [MODULE] %(module)s - [LINE] %(lineno)d - [MSG] %(message)s')
file_handler = logging.FileHandler(LOG_FILE_PATH)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
#

ITEMS_JSON = 'items.json'

@app.route('/loc')
def my_route1():
    wanted_stores = ['T2451', 'T3277', 'T1344']
    font_size = 18

    upc = request.args.get('upc', default=None, type=str)
    if upc is None or upc == '':
        return render_template('index.html', font_size=font_size, message='Error. No UPC scanned.')

    message = _get_item_info(upc, wanted_stores)
    # return '<br><br><br><br>'.join(messages)
    return render_template('index.html', font_size=font_size, message=Markup(message))


@app.route('/loc-check')
def my_route2():
    wanted_stores = ['T1344', 'T3230', 'T3280']
    font_size = 26

    upc = request.args.get('upc', default=None, type=str)
    if upc is None or upc == '':
        return render_template('index.html', font_size=font_size, message='Error. No UPC scanned.')

    message = _get_item_info(upc, wanted_stores)
    # return '<br><br><br><br>'.join(messages)
    return render_template('index.html', font_size=font_size, message=Markup(message))


def _get_item_info(upc: str, wanted_stores: list) -> list:
    with open(ITEMS_JSON, 'r', encoding='utf8') as fd:
        all_store_items = json.load(fd)

    messages = []
    for store, items in all_store_items.items():
        if not store.startswith(tuple(wanted_stores)):
            continue

        item = items.get(upc)
        if item is None:
            messages.append(f'<b>{store}</b> - {upc} not on plano <br><br>')
            continue

        messages.append(f'<b>{store}</b> - <b>{item["location"]}</b> - {item["name"]}')

    messages = _organize_message(messages)
    message = '<br><br>'.join(messages)

    if not message:
        message = 'Stores {} not available'.format(', '.join(wanted_stores))
    return message


def _organize_message(messages: list) -> list:
    store_re = r'<b>\w+<b> -'

    temp = []
    for msg in messages:
        logger.info(msg)
        if re.match(store_re, msg):
            temp.append(msg)

    logger.info(f'temp is: {temp}')
    temp.append('<hr class="dashed"><br><br>')

    for msg in messages:
        if not re.match(store_re, msg):
            temp.append(msg)

    return temp
