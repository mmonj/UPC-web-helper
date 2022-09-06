from flask import Flask

from upc_check import upc_check
from upc_logger import upc_logger
from __signature_getter import signature_getter

app = Flask(__name__)
app.register_blueprint(upc_check.app_upc_check)
app.register_blueprint(upc_logger.app_upc_logger)
app.register_blueprint(signature_getter.app_signature_getter)
