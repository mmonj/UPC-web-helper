import json
from string import Template
from flask import Flask, request

app = Flask(__name__)

ITEMS_JSON = 'items.json'

@app.route('/loc-check')
def my_route1():
    upc = request.args.get('upc', default=None, type=str)
    if upc is None:
        return 'ERROR. No UPC given'

    messages = _get_item_info(upc)

    return '<br/><br/><br/><br/>'.join(messages)


def _get_item_info(upc):
    with open(ITEMS_JSON, 'r', encoding='utf8') as fd:
        all_store_items = json.load(fd)

    messages = []
    for store in all_store_items:
        items = all_store_items[store].get(upc)
        if items is None:
            messages.append('Item not present / Discontinued')
            continue

        messages.append(
            '{}  {}'.format(item['name'], item['location'])
        )

    return messages
