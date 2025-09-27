from typing import Dict, Tuple, Optional
from angle_utils import calculate_angle, is_angle_in_range

# Joint definitions mapping to triplets of landmark names from Mediapipe
# Angles are measured at the middle point (B) in A-B-C
JOINT_DEFINITIONS: Dict[str, Tuple[str, str, str]] = {
	"Knee": ("HIP", "KNEE", "ANKLE"),
	"Hip": ("SHOULDER", "HIP", "KNEE"),
	"Elbow": ("SHOULDER", "ELBOW", "WRIST"),
	"Shoulder": ("ELBOW", "SHOULDER", "HIP"),
	"Back": ("SHOULDER", "HIP", "KNEE"),
}

# Map human names to Mediapipe PoseLandmark enum names for left/right selection
LEFT_SUFFIX = "_LEFT"
RIGHT_SUFFIX = "_RIGHT"


class FeedbackEngine:
	def __init__(self) -> None:
		pass

	@staticmethod
	def _get_point(lms: Dict[str, object], name: str) -> Optional[Tuple[float, float]]:
		p = lms.get(name)
		if p is None:
			return None
		return (p.x, p.y)

	def compute_joint_angle(self, lms: Dict[str, object], joint_name: str, side: str = "LEFT") -> float:
		triplet = JOINT_DEFINITIONS.get(joint_name)
		if triplet is None:
			return float('nan')
		suffix = LEFT_SUFFIX if side.upper() == "LEFT" else RIGHT_SUFFIX
		a_name = f"{triplet[0]}{suffix}"
		b_name = f"{triplet[1]}{suffix}"
		c_name = f"{triplet[2]}{suffix}"
		pa = self._get_point(lms, a_name)
		pb = self._get_point(lms, b_name)
		pc = self._get_point(lms, c_name)
		if pa is None or pb is None or pc is None:
			return float('nan')
		return calculate_angle(pa, pb, pc)

	def compute_all_angles(self, lms: Dict[str, object], side_priority: Tuple[str, str] = ("LEFT", "RIGHT")) -> Dict[str, float]:
		angles: Dict[str, float] = {}
		for joint in JOINT_DEFINITIONS.keys():
			angle_val = float('nan')
			for side in side_priority:
				angle_val = self.compute_joint_angle(lms, joint, side)
				if angle_val == angle_val:  # not NaN
					break
			angles[joint] = angle_val
		return angles

	def check_feedback(self, exercise: str, phase: str, ref_ranges: Dict[str, Tuple[float, float]], angles: Dict[str, float]) -> Tuple[bool, str]:
		missing: list[str] = []
		off: list[str] = []
		for joint, rng in ref_ranges.items():
			ang = angles.get(joint, float('nan'))
			if ang != ang:
				missing.append(joint)
				continue
			if not is_angle_in_range(ang, tuple(rng)):
				off.append(f"{joint}")
		if not off and not missing:
			return True, "Good form!"
		if missing:
			return False, f"Move fully visible: {', '.join(missing)}"
		return False, ", ".join([f"Adjust {j}" for j in off])
