from __future__ import print_function
import os
import torch
from enum import Enum
from skimage import io
from skimage import color
import cv2
try:
	import urllib.request as request_file
except BaseException:
	import urllib as request_file

from .models import FAN, ResNetDepth
from .utils import *

appdata_root = os.path.join(appdata_dir('face_alignment'), "data")

class LandmarksType(Enum):
	"""Enum class defining the type of landmarks to detect.

	``_2D`` - the detected points ``(x,y)`` are detected in a 2D space and follow the visible contour of the face
	``_2halfD`` - this points represent the projection of the 3D points into 3D
	``_3D`` - detect the points ``(x,y,z)``` in a 3D space

	"""
	_2D = 1
	_2halfD = 2
	_3D = 3

class NetworkSize(Enum):
	# TINY = 1
	# SMALL = 2
	# MEDIUM = 3
	LARGE = 4

	def __new__(cls, value):
		member = object.__new__(cls)
		member._value_ = value
		return member

	def __int__(self):
		return self.value


class FaceAlignment:
	def __init__(self, landmarks_type, network_size=NetworkSize.LARGE,
				 device='cuda', flip_input=False, face_detector='sfd', base_path = appdata_root, verbose=False, config = None):
		self.device = device
		self.flip_input = flip_input
		self.landmarks_type = landmarks_type
		self.verbose = verbose
		# print('base_path', base_path)
		# base_path = 

		network_size = int(network_size)

		if not os.path.exists(base_path):
			os.makedirs(base_path)

		if 'cuda' in device:
			torch.backends.cudnn.benchmark = True

		path_to_detector = os.path.join(base_path, 's3fd_convert.pth' if face_detector == 'sfd' else 'mmod_human_face_detector.dat')

		# Get the face detector
		face_detector_module = __import__('face_alignment.detection.' + face_detector,
										  globals(), locals(), [face_detector], 0)
		self.face_detector = face_detector_module.FaceDetector(device=device, path_to_detector = path_to_detector, verbose=verbose, config = config)

		# Initialise the face alignemnt networks
		self.face_alignment_net = FAN(network_size)
		if landmarks_type == LandmarksType._2D:
			network_name = '2DFAN-' + str(network_size) + '.pth.tar'
		else:
			network_name = '3DFAN-' + str(network_size) + '.pth.tar'
		fan_path = os.path.join(base_path, network_name)

		if not os.path.isfile(fan_path):
			print("Downloading the Face Alignment Network(FAN). Please wait...")

			fan_temp_path = os.path.join(base_path, network_name + '.download')

			if os.path.isfile(fan_temp_path):
				os.remove(os.path.join(fan_temp_path))

			print('network_name', network_name, fan_temp_path)

			request_file.urlretrieve(
				"https://www.adrianbulat.com/downloads/python-fan/" +
				network_name, os.path.join(fan_temp_path))

			os.rename(os.path.join(fan_temp_path), os.path.join(fan_path))

		fan_weights = torch.load(
			fan_path,
			map_location=lambda storage,
			loc: storage)

		self.face_alignment_net.load_state_dict(fan_weights)

		self.face_alignment_net.to(device)
		self.face_alignment_net.eval()

		# Initialiase the depth prediciton network
		if landmarks_type == LandmarksType._3D:
			self.depth_prediciton_net = ResNetDepth()
			depth_model_path = os.path.join(base_path, 'depth.pth.tar')
			if not os.path.isfile(depth_model_path):
				print(
					"Downloading the Face Alignment depth Network (FAN-D). Please wait...")

				depth_model_temp_path = os.path.join(base_path, 'depth.pth.tar.download')

				if os.path.isfile(depth_model_temp_path):
					os.remove(os.path.join(depth_model_temp_path))

				request_file.urlretrieve(
					"https://www.adrianbulat.com/downloads/python-fan/depth.pth.tar",
					os.path.join(depth_model_temp_path))

				os.rename(os.path.join(depth_model_temp_path), os.path.join(depth_model_path))

			depth_weights = torch.load(
				depth_model_path,
				map_location=lambda storage,
				loc: storage)
			depth_dict = {
				k.replace('module.', ''): v for k,
				v in depth_weights['state_dict'].items()}
			self.depth_prediciton_net.load_state_dict(depth_dict)

			self.depth_prediciton_net.to(device)
			self.depth_prediciton_net.eval()

	def get_landmarks_from_image(self, image_or_path, use_dlib = False):
		if isinstance(image_or_path, str):
			try:
				image = io.imread(image_or_path)
			except IOError:
				print("error opening file :: ", image_or_path)
				return None
		else:
			image = image_or_path

		if image.ndim == 2:
			image = color.gray2rgb(image)
		elif image.ndim == 4:
			image = image[..., :3]
		
		image_data = image[..., ::-1].copy()

		if use_dlib:
			return self.face_detector.predict_from_image(image_data)

		detected_faces = self.face_detector.detect_from_image(image_data)

		if len(detected_faces) == 0:
			print("Warning: No faces were detected.")
			return None
		else:
			print('Detect %d faces', detected_faces)

		torch.set_grad_enabled(False)
		landmarks = []
		for i, d in enumerate(detected_faces):
			center = torch.FloatTensor(
				[d[2] - (d[2] - d[0]) / 2.0, d[3] -
				 (d[3] - d[1]) / 2.0])
			center[1] = center[1] - (d[3] - d[1]) * 0.12
			scale = (d[2] - d[0] +
					 d[3] - d[1]) / self.face_detector.reference_scale

			inp = crop(image, center, scale)
			inp = torch.from_numpy(inp.transpose(
				(2, 0, 1))).float().div(255.0).unsqueeze_(0)

			inp = inp.to(self.device)

			out = self.face_alignment_net(inp)[-1].data.cpu()
			if self.flip_input:
				out += flip(self.face_alignment_net(flip(inp))
							[-1].data.cpu(), is_label=True)

			pts, pts_img = get_preds_fromhm(out, center, scale)
			pts, pts_img = pts.view(68, 2) * 4, pts_img.view(68, 2)

			if self.landmarks_type == LandmarksType._3D:
				heatmaps = np.zeros((68, 256, 256))
				for i in range(68):
					if pts[i, 0] > 0:
						heatmaps[i] = draw_gaussian(
							heatmaps[i], pts[i], 2)
				heatmaps = torch.from_numpy(
					heatmaps).view(1, 68, 256, 256).float()
				heatmaps = heatmaps.to(self.device)
				depth_pred = self.depth_prediciton_net(
					torch.cat((inp, heatmaps), 1)).data.cpu().view(68, 1)
				pts_img = torch.cat(
					(pts_img, depth_pred * (1.0 / (256.0 / (200.0 * scale)))), 1)

			faces = pts_img.numpy().tolist()
			# print('got faces {}', faces)

			landmarks.append({
				'location': {
					'x': int(d[0]),
					'y': int(d[1]),
					'width': int(d[2] - d[0]),
					'height': int(d[3] - d[1])
				},
				'faces': faces
			})

		return landmarks

	def get_landmarks_from_directory(self, path, extensions=['.jpg', '.png'], recursive=True, show_progress_bar=True):
		detected_faces = self.face_detector.detect_from_directory(path, extensions, recursive, show_progress_bar)

		predictions = {}
		for image_path, bounding_boxes in detected_faces.items():
			image = io.imread(image_path)
			preds = self.get_landmarks_from_image(image, bounding_boxes)
			predictions[image_path] = preds

		return predictions

	@staticmethod
	def remove_models(self):
		base_path = os.path.join(appdata_dir('face_alignment'), "data")
		for data_model in os.listdir(base_path):
			file_path = os.path.join(base_path, data_model)
			try:
				if os.path.isfile(file_path):
					print('Removing ' + data_model + ' ...')
					os.unlink(file_path)
			except Exception as e:
				print(e)
