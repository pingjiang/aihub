import importlib
import time
import os
from uuid import uuid4
import traceback
from contextlib import contextmanager
from flask import Flask
from flask import request
from flask import jsonify
# from flask import abort, redirect, url_for
from jpot import transform
import base64
from urllib.parse import urlencode
from urllib.request import urlretrieve

def write_file(filepath, content):
  with open(filepath, 'wb') as f:
    return f.write(content)

def decode_base64_image(base64_string):
  found = str(base64_string).find(',')
  if found != -1:
    base64_string = base64_string[(found + 1):]

  return base64.b64decode(base64_string)

def save_base64_image(filepath, base64_string):
  imgdata = decode_base64_image(base64_string)
  print('save image file length', filepath, len(imgdata))
  write_file(filepath, bytearray(imgdata))

def save_url(filepath, url):
	urlretrieve(url, filepath)

def uniq_file():
  return './__autosaved_' + str(uuid4()) + '.png'

def read_file_as_base64(filepath):
  with open(filepath, 'rb') as f:
    return base64.b64encode(f.read())

def save_files(data, request):
	cleans = []
	for key in request.json.keys():
		if key == 'url':
			url = request.json.get(key)

			if url is not None:
				tmp_filepath = uniq_file()
				save_url(tmp_filepath, url)
				data[key] = tmp_filepath
				cleans.append(tmp_filepath)
		elif 'image_base64' in key:
			image_base64 = request.json.get(key)

			if image_base64 is not None:
				tmp_filepath = uniq_file()
				save_base64_image(tmp_filepath, image_base64)
				data[key] = tmp_filepath
				cleans.append(tmp_filepath)
	return cleans

@contextmanager
def timeit_context(name):
	startTime = time.time()
	yield
	elapsedTime = time.time() - startTime
	print('[{}] finished in {} ms'.format(name, int(elapsedTime * 1000)))

application = Flask(__name__)

models_dir = os.environ.get('AIHUB_MODELS')

if models_dir is None:
	models_dir = os.path.join(application.root_path, '../models')

services = {}

def get_service_key_config(name):
	config = request.args if request.args != None else {}
	if config is None:
		config = {}

	key = name + '?' + urlencode(config)
	return key, config

@application.route('/api/services', methods=['GET'])
def list_services():
	return jsonify({
		'code' : 0,
		'msg': 'success',
		'data': list(services.keys()),
	})

@application.route('/api/services/<name>', methods=['DELETE'])
def delete_services(name):
	key, config = get_service_key_config(name)
	
	if key in services:
		del services[key]

	return jsonify({
		'code' : 0,
		'msg': 'success',
	})

@application.route('/api/<name>', methods=['GET', 'POST'])
def handle_api(name):
	key, config = get_service_key_config(name)

	if key not in services:
		try:
			service = importlib.import_module(name + '.service')
			s = service.Service()

			with timeit_context('service init'):
				models_path = os.path.join(models_dir, name)

				if not os.path.exists(models_path):
					print('WARN: models_path is not exists, please set AIHUB_MODELS')
				
				s.init(models_path, config)

			services[key] = s
			print('load service {}', key)
		except Exception as err:
			traceback.print_exc()
			return jsonify( {
			'code' : 500,
			'msg': 'load service error: ' + str(err),
		})

	cleans = None

	try:
		s = services[key]
		# request .json, .args, .forms, .files
		data = request.json if request.json is not None else {} # { 'img_path': '../assets/aflw-test.jpg' }
		cleans = save_files(data, request)

		startTime = time.time()
		
		results = s.handle(data, request)
		transformer = data.get('transformer')

		if results is not None and transformer is not None:
			results = transform(results, transformer)

		elapsedTime = time.time() - startTime

		return jsonify( {
			'code' : 0,
			'msg': 'success',
			'data': results,
			'elapsed': int(elapsedTime * 1000),
		})
	except Exception as err:
		traceback.print_exc()
		return jsonify( {
			'code' : 400,
			'msg': 'invoke handler error: ' + str(err),
		})
	finally:
		if cleans is not None and len(cleans) > 0:
			for f in cleans:
				os.remove(f)

if __name__ == '__main__':
	application.run(debug = True, host = '0.0.0.0')
