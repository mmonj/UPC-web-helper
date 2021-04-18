import json
from string import Template
from flask import Flask, request

app = Flask(__name__)
ITEMS_JSON_TEMPLATE = Template('items_T$store_number.json')


@app.route('/T2451-loc-check')
def my_route1():
  upc = request.args.get('upc', default=None, type=str)
  if upc if None:
    return 'ERROR. No UPC given'

  info = _get_item_info(upc, '2451')
  if info is None:
    return 'Item not present / Discontinued'

  return '<br/><br/>'.join(info.values())


@app.route('/T3277-loc-check')
def my_route2():
  upc = request.args.get('upc', default=None, type=str)
  if upc is None:
    return 'ERROR. No UPC given'

  info = _get_item_info(upc, '3277')
  if info is None:
    return 'Item not present / Discontinued'

  return '<br/><br/>'.join(info.values())


def _get_item_info(upc, store_number):
    items_json = ITEMS_JSON_TEMPLATE.safe_substitute(store_number=store_number)
    with open(items_json, 'r', encoding='utf8') as fd:
        items = json.load(fd)

    return items.get(upc)
