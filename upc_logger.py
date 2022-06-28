import datetime
import json
import os
from flask import Blueprint, render_template, session, abort, request, Markup

STORE_INFO_FILE = 'store_info.json'

app_upc_logger = Blueprint('app_upc_logger',__name__)

@app_upc_logger.route("/upc-log")
def my_route1():
    font_size = 18

    if not os.path.isfile(STORE_INFO_FILE):
        return render_template('index.html', font_size=font_size, message='Error. No JSON file found.')

    with open(STORE_INFO_FILE, 'r', encoding='utf8') as fd:
        stores = json.load(fd)

    upc = request.args.get('upc', default=None, type=str)
    if upc is None or upc == '':
        return render_template('index.html', font_size=font_size, message='Error. No UPC scanned.')

    now = datetime.datetime.now().strftime('%Y-%m-%d at %H:%M:%S')
    stores['all'].append( {upc: now} )


    return render_template('index.html', font_size=font_size, message=Markup('Success'))