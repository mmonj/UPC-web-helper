import json
from string import Template
from flask import Flask, request, render_template, Markup

app = Flask(__name__)

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
    temp = []
    for msg in messages:
        if ' ' not in msg:
            temp.append(msg)

    temp.append('<hr class="dashed"><br><br>')

    for msg in messages:
        if ' ' in msg:
            temp.append(msg)

    return temp
