from typing import Tuple
import numpy as np


def calculate_angle(point_a: Tuple[float, float], point_b: Tuple[float, float], point_c: Tuple[float, float]) -> float:
	"""
	Calculate the angle ABC (at point_b) in degrees using arctangent method.
	Returns angle in [0, 180] degrees.
	"""
	a = np.array(point_a)  # First point (e.g., shoulder)
	b = np.array(point_b)  # Mid point (e.g., elbow)
	c = np.array(point_c)  # End point (e.g., wrist)

	radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
	angle = np.abs(radians*180.0/np.pi)

	if angle > 180.0:
		angle = 360 - angle

	return float(angle)


def is_angle_in_range(angle: float, low_high: Tuple[float, float]) -> bool:
	if np.isnan(angle):
		return False
	low, high = low_high
	return low <= angle <= high
