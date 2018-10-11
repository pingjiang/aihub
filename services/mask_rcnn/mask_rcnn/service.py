import os
import skimage
import json
import numpy as np
from mrcnn.config import Config
from mrcnn import model as modellib
from PIL import Image
import base64
import random
import colorsys
from io import BytesIO

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

def load_image(filepath):
    image = skimage.io.imread(filepath)
    # If grayscale. Convert to RGB for consistency.
    if image.ndim != 3:
        image = skimage.color.gray2rgb(image)
    # If has an alpha channel, remove it for consistency
    if image.shape[-1] == 4:
        image = image[..., :3]
    return image

def image2base64(arr):
	# W,H,C[ ... ... ... ]
	# TODO(pj) check mask format
	tmp = Image.fromarray(arr)
	buffered = BytesIO()
	tmp.save(buffered, format='PNG')
	return str(base64.b64encode(buffered.getvalue()), 'utf8')

def to255(c):
	return [int(v*255) for v in c]

def hexcolor(r, g, b):
	return '#{:02x}{:02x}{:02x}'.format(r, g, b)

def random_colors(N, bright=True):
    brightness = 1.0 if bright else 0.7
    hsv = [(i / N, 1, brightness) for i in range(N)]
    colors = list(map(lambda c: to255(colorsys.hsv_to_rgb(*c)), hsv))
    random.shuffle(colors)
    return colors

class InferenceConfig(Config):
    NAME = 'coco'
    NUM_CLASSES = 1 + 80
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1
    DETECTION_MIN_CONFIDENCE = 0

class_names = ['BG', 'person', 'bicycle', 'car', 'motorcycle', 'airplane',
  'bus', 'train', 'truck', 'boat', 'traffic light',
  'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird',
  'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear',
  'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie',
  'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
  'kite', 'baseball bat', 'baseball glove', 'skateboard',
  'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
  'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
  'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza',
  'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed',
  'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote',
  'keyboard', 'cell phone', 'microwave', 'oven', 'toaster',
  'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors',
  'teddy bear', 'hair drier', 'toothbrush']

class_names_len = len(class_names)

# [255, 0, 0]
COLORS = random_colors(class_names_len)

COLORSMAP = {}
for i, v in enumerate(class_names):
	COLORSMAP[v] = COLORS[i]

def apply_mask(image, mask, color, alpha=1):
    for c in range(3):
        image[:, :, c] = np.where(mask == 1,
                                  image[:, :, c] * (1 - alpha) + alpha * color[c], image[:, :, c])
    return image


def detect(model, filepath, get_color):
	image = load_image(filepath)
	r = model.detect([image], verbose=True)
	ret = []

	if not len(r) or not len(r[0]['class_ids']):
		return ret

	first = r[0]
	masks = first['masks']
	bmask = np.zeros((masks.shape[0], masks.shape[1], 3), np.uint8)
	# image = apply_mask(image, arr.astype(np.uint8), color)

	for i, v in enumerate(first['class_ids']):
		# [ y1, x1, y2, x2 ]
		loc = first['rois'][i]
		class_name = class_names[v] if v < class_names_len else None
		color = get_color(class_name, i)
		bmask = apply_mask(bmask, masks[...,i].astype(np.uint8), color)

		ret.append({
			'class_id': int(v),
			'class_name': class_name,
			'location': {
				'x': int(loc[1]),
				'y': int(loc[0]),
				'width': int(loc[3] - loc[1]),
				'height': int(loc[2] - loc[0]),
			},
			'score': float(first['scores'][i]),
			# 491 H 640 W 19 N
			# 
			'color': hexcolor(*color),
		})

	ret[0]['mask_base64'] = 'data:image/png;base64,' + image2base64(bmask)
	return ret

def get_config(config, key, default):
	if config is None or key not in config or config[key] is None:
		return default
	return config[key]

class Service:
	def init(self, base_path, config = {}):
		model_name = get_config(config, 'model_name', 'mask_rcnn_coco.h5')
		inferConfig = InferenceConfig()

		model_path = os.path.join(base_path, model_name)
		model = modellib.MaskRCNN(mode="inference", config=inferConfig, model_dir='logs')
		print("Loading weights ", model_path)
		model.load_weights(model_path, by_name=True)
		self.model = model

	def handle(self, data, request = None):
		image_base64 = data.get('image_base64')
		colors_map = data.get('colors_map')

		def get_color(name, index):
			ret = COLORS[index]
			if colors_map is not None and name in colors_map:
				ret = colors_map[name]
			return ret

		if image_base64 is None:
			raise TypeError('image_base64 is null')

		return detect(self.model, image_base64, get_color)

if __name__ == '__main__':
	s = Service()
	s.init('models/mask_rcnn')
	r = s.handle({
		'image_base64': 'services/mask_rcnn/src/images/9247489789_132c0d534a_z.jpg',
		'colors_map': COLORSMAP,
	})
	with open('ret.json', 'w', encoding='utf8') as f:
		f.write(json.dumps(r))
		