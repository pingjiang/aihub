import sys
sys.path.insert(0,'/userscripts')
import importlib

def get_config(config, key, default):
	if config is None or key not in config or config[key] is None:
		return default
	return config[key]

class Service:
	def init(self, base_path, config={}):
		pass

	def handle(self, data, request=None):
		filepath = data.get('url')

		if filepath is None:
			raise TypeError('filepath is null')

		entry_name = get_config(data, 'entry', 'info')
		entry = importlib.import_module('info_handlers.' + entry_name)

		return entry.get_info(filepath, data)
