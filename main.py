from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def main_page():
	return 'the main page'

@app.route('/locationcheck')
def my_route():
  upc = request.args.get('upc', default = '123', type = str)
  return upc
