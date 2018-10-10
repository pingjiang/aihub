import os
import skimage
import json
import numpy as np
from mrcnn.config import Config
from mrcnn import model as modellib
from PIL import Image
import base64
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

def alpha_bmp_to_image_base64(arr):
	# W,H,C[ ... ... ... ]
	# TODO(pj) check mask format
	image = Image.fromarray(arr, mode='1')
	buffered = BytesIO()
	image.save(buffered, format="PNG")
	return str(base64.b64encode(buffered.getvalue()), 'utf8')

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

def detect(model, filepath):
	image = load_image(filepath)
	r = model.detect([image], verbose=True)
	ret = []

	if not len(r) or not len(r[0]['class_ids']):
		return ret

	first = r[0]

	for i, v in enumerate(first['class_ids']):
		# [ y1, x1, y2, x2 ]
		loc = first['rois'][i]
		ret.append({
			'class_id': int(v),
			'class_name': class_names[v] if v < class_names_len else None,
			'location': {
				'x': int(loc[1]),
				'y': int(loc[0]),
				'width': int(loc[3] - loc[1]),
				'height': int(loc[2] - loc[0]),
			},
			'score': float(first['scores'][i]),
			'mask': alpha_bmp_to_image_base64(first['masks'][i]),
		})

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

		if image_base64 is None:
			raise TypeError('image_base64 is null')

		return detect(self.model, image_base64)

if __name__ == '__main__':
	s = Service()
	s.init('.')
	r = s.handle({
		'image_base64': 'images/9247489789_132c0d534a_z.jpg'
	})
	with open('ret.json', 'w', encoding='utf8') as f:
		f.write(json.dumps(r))
		