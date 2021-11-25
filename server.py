import json
from string import Template
from flask import Flask, request, render_template, Markup

app = Flask(__name__)

ITEMS_JSON = 'items.json'

@app.route('/loc')
def my_route1():
    wanted_stores = ['T2451', 'T3277']

    upc = request.args.get('upc', default=None, type=str)
    if upc is None or upc == '':
        return 'ERROR. No UPC given'

    message = _get_item_info(upc, wanted_stores)
    # return '<br><br><br><br>'.join(messages)
    return render_template('index.html', font_size=14, message=Markup(message))


@app.route('/loc-check')
def my_route2():
    wanted_stores = ['T1344']

    upc = request.args.get('upc', default=None, type=str)
    if upc is None or upc == '':
        return 'ERROR. No UPC given'

    message = _get_item_info(upc, wanted_stores)
    # return '<br><br><br><br>'.join(messages)
    return render_template('index.html', font_size=20, message=Markup(message))


def _get_item_info(upc: str, wanted_stores: list) -> list:
    with open(ITEMS_JSON, 'r', encoding='utf8') as fd:
        all_store_items = json.load(fd)

    message = ''
    for store, items in all_store_items.items():
        if store not in wanted_stores:
            continue

        item = items.get(upc)
        if item is None:
            message += f'<b>{store}</b>: <b>{upc}</b> not on plano <br><br>'
            continue

        message += f'<b>{store}</b>: <b>{item["location"]}</b> - {item["name"]} <br><br>'

    if not message:
        message = 'Error with store number.'
    return message
