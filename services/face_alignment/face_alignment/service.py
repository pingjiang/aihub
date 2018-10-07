import face_alignment

def get_config(config, key, default):
	if config is None or key not in config or config[key] is None:
		return default
	return config[key]

class Service:
	def init(self, base_path, config = {}):
		face_detector = get_config(config, 'face_detector', 'sfd')
		self.handler = face_alignment.FaceAlignment(face_alignment.LandmarksType._2D, device='cpu', face_detector=face_detector, base_path = base_path, config = config)

	def handle(self, data, request = None):
		image_base64 = data.get('image_base64')

		if image_base64 is None:
			raise TypeError('image_base64 is null')

		use_dlib = get_config(data, 'use_dlib', False)
		return self.handler.get_landmarks_from_image(image_base64, use_dlib)
