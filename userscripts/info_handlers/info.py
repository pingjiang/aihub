from PIL import Image
import cv2
from .utils import get_size

def get_info(filepath, data):
	img = Image.open(filepath)

	return {
		**get_size(img.size),
		'data': data,
	}
