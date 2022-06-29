import datetime
import json
import os
import time
from flask import Blueprint, render_template, session, abort, request, Markup

STORE_INFO_FILE = './static/store_info.json'
app_upc_logger = Blueprint('app_upc_logger', __name__)

@app_upc_logger.route("/upc-log")
def my_route1():
    font_size = 18

    if not os.path.isfile(STORE_INFO_FILE):
        return render_template('index.html', font_size=font_size, message=f'Error. No JSON file found. "{os.getcwd()}"')

    with open(STORE_INFO_FILE, 'r', encoding='utf8') as fd:
        stores = json.load(fd)

    upc = request.args.get('upc', default=None, type=str)
    if upc is None or upc == '':
        return render_template('index.html', font_size=font_size, message='Error. No UPC scanned.')

    ts = time.time() - (4 * 3600)
    now = datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d at %I:%M:%S %p')
    # now = datetime.datetime.now().strftime('%Y-%m-%d at %H:%M:%S')
    stores['all'][upc] = now

    with open(STORE_INFO_FILE, 'w', encoding='utf8') as fd:
        json.dump(stores, fd, indent=4)

    return render_template('upc_log_success.html', upc=upc)
