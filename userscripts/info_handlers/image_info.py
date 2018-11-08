from PIL import Image
import cv2
from .utils import get_size

def get_info(filepath, data):
	img = Image.open(filepath)

	return {
		'format': img.format.lower(),
		**get_size(img.size),
		'data': data,
	}
