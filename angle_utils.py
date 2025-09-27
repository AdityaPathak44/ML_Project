from typing import Tuple
import numpy as np


def calculate_angle(point_a: Tuple[float, float], point_b: Tuple[float, float], point_c: Tuple[float, float]) -> float:
	"""
	Calculate the angle ABC (at point_b) in degrees between BA and BC using numpy.
	Returns angle in [0, 180].
	"""
	a = np.array(point_a, dtype=float)
	b = np.array(point_b, dtype=float)
	c = np.array(point_c, dtype=float)

	ba = a - b
	bc = c - b

	norm_ba = np.linalg.norm(ba)
	norm_bc = np.linalg.norm(bc)
	if norm_ba == 0 or norm_bc == 0:
		return float('nan')

	cosine_angle = np.dot(ba, bc) / (norm_ba * norm_bc)
	cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
	angle_rad = np.arccos(cosine_angle)
	angle_deg = np.degrees(angle_rad)
	return float(angle_deg)


def is_angle_in_range(angle: float, low_high: Tuple[float, float]) -> bool:
	if np.isnan(angle):
		return False
	low, high = low_high
	return low <= angle <= high
