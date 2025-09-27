import cv2
import mediapipe as mp
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class LandmarkPoint:
	x: float
	y: float
	z: float
	visibility: float


class PoseDetector:
	def __init__(self, static_image_mode: bool = False, model_complexity: int = 1,
				 enable_segmentation: bool = False, min_detection_confidence: float = 0.5,
				 min_tracking_confidence: float = 0.5) -> None:
		self._mp_pose = mp.solutions.pose
		self._pose = self._mp_pose.Pose(
			static_image_mode=static_image_mode,
			model_complexity=model_complexity,
			enable_segmentation=enable_segmentation,
			min_detection_confidence=min_detection_confidence,
			min_tracking_confidence=min_tracking_confidence,
		)
		self._mp_drawing = mp.solutions.drawing_utils
		self._mp_styles = mp.solutions.drawing_styles

	def process(self, frame_bgr):
		image_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
		image_rgb.flags.writeable = False
		results = self._pose.process(image_rgb)
		image_rgb.flags.writeable = True
		return results

	def draw(self, frame_bgr, results) -> None:
		if results.pose_landmarks:
			self._mp_drawing.draw_landmarks(
				frame_bgr,
				results.pose_landmarks,
				self._mp_pose.POSE_CONNECTIONS,
				landmark_drawing_spec=self._mp_styles.get_default_pose_landmarks_style(),
				connection_drawing_spec=self._mp_styles.DrawingSpec(color=(0, 255, 0), thickness=2),
			)

	def get_landmarks(self, frame_bgr, results) -> Optional[Dict[str, LandmarkPoint]]:
		if not results.pose_landmarks:
			return None
		h, w = frame_bgr.shape[:2]
		indexed: Dict[str, LandmarkPoint] = {}
		for idx, lm in enumerate(results.pose_landmarks.landmark):
			name = self._mp_pose.PoseLandmark(idx).name
			indexed[name] = LandmarkPoint(
				x=lm.x * w,
				y=lm.y * h,
				z=lm.z,
				visibility=lm.visibility,
			)
		return indexed
