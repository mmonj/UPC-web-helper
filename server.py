import json
from flask import Flask, request

app = Flask(__name__)
ITEMS_JSON = 'items.json'


@app.route('/locationcheck')
def my_route():
  upc = request.args.get('upc', default = '*', type = str)
  if upc == '*':
  	return 'ERROR. No UPC given'

  name, section, location = _get_item_info(upc)
  if location is None:
  	return 'Item not present'

  return f'{name}\n\n{section}\n\n{location}'


def _get_item_info(upc):
	with open(ITEMS_JSON, 'r', encoding='utf8') as fd:
		items = json.load(fd)

	info = items.get(upc)
	if info is None:
		return None, None, None

	return info['name'], info['section'], info['location']
