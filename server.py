import json
import logging
import os
import re
from string import Template
from flask import Flask, request, render_template, Markup

from upc_check_minted import upc_check
from upc_logger import upc_logger

app = Flask(__name__)
app.register_blueprint(upc_check)
app.register_blueprint(app_upc_logger)
