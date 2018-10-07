
import subprocess
import os
import base64
from uuid import uuid4


def uniq_file():
	return './__autosaved_' + str(uuid4()) + '.png'


def read_file_as_base64(filepath):
	with open(filepath, 'rb') as f:
		return base64.b64encode(f.read())


class Service:
	def init(self, base_path, config={}):
		self.matting_bin = '/usr/local/bin/matting'

	def handle(self, data, request=None):
		image_base64 = data.get('image_base64')
		image_base64_trimap = data.get('image_base64_trimap')

		if image_base64 is None or image_base64_trimap is None:
			raise TypeError('image_base64 or image_base64_trimap is null')

		return self.matting(image_base64, image_base64_trimap)

	def matting(self, tmp_filepath, tmp_filepath_trimap):
		tmp_filepath_out = uniq_file()

		cmd = [self.matting_bin, tmp_filepath,
				tmp_filepath_trimap, tmp_filepath_out]

		result = 'error'
		image_base64_result = None

		try:
			print('begin matting')
			run_result = subprocess.run(cmd, stdout=subprocess.PIPE)
			print('end matting')
			result = str(run_result.stdout)
			image_base64_result = read_file_as_base64(tmp_filepath_out)
		except Exception as e:
			print('matting error', e)
			result = 'run exception'
			os.remove(tmp_filepath)
			os.remove(tmp_filepath_trimap)
			os.remove(tmp_filepath_out)

		return {
			"raw_results": result,
			"image_base64": str(image_base64_result, encoding='utf-8')
		}
