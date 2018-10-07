import time
import os
from flask import Flask
from flask import request
from flask import jsonify
# from flask import abort, redirect, url_for
application = Flask(__name__)

@application.route('/api/services', methods=['GET'])
def list_services():
	pass

@application.route('/api/services/<name>', methods=['DELETE'])
def delete_services(name):
	pass

@application.route('/api/<name>', methods=['POST'])
def handle_api(name):
	pass

if __name__ == '__main__':
	application.run(debug = True, host = '0.0.0.0')
