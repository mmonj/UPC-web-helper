import json
from string import Template
from flask import Flask, request

app = Flask(__name__)
ITEMS_JSON_TEMPLATE = Template('items_T$store_number.json')


@app.route('/T2451_loc_check')
def my_route():
  upc = request.args.get('upc', default = '*', type = str)
  if upc == '*':
    return 'ERROR. No UPC given'

  info = _get_item_info(upc, '2451')
  if info is None:
    return 'Item not present / Discontinued'

  return '<br/><br/>'.join(info)


@app.route('/T3277_loc_check')
def my_route():
  upc = request.args.get('upc', default = '*', type = str)
  if upc == '*':
    return 'ERROR. No UPC given'

  name, section, location = _get_item_info(upc, '3277')
  if location is None:
    return 'Item not present'

  return f'{name}<br/><br/>{section}<br/><br/>{location}'


def _get_item_info(upc, store_number):
    items_json = ITEMS_JSON_TEMPLATE.safe_substitute(store_number=store_number)
    with open(items_json, 'r', encoding='utf8') as fd:
        items = json.load(fd)

    return items.get(upc)
