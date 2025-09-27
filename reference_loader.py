import json
from typing import Dict, Any, Optional


def load_reference_from_json(path: str) -> Dict[str, Any]:
	with open(path, 'r', encoding='utf-8') as f:
		return json.load(f)


def get_default_reference() -> Dict[str, Any]:
	return {
		"Squat": {
			"Down": {"Knee": [70, 100], "Hip": [150, 180]},
			"Up": {"Knee": [160, 180], "Hip": [165, 185]},
		},
		"Push-up": {
			"Down": {"Elbow": [70, 100], "Shoulder": [60, 100]},
			"Up": {"Elbow": [160, 185]},
		},
		"Plank": {
			"Hold": {"Back": [170, 185], "Hip": [160, 185]},
		},
	}


class ReferenceProvider:
	def __init__(self, json_path: Optional[str] = None) -> None:
		self._data = load_reference_from_json(json_path) if json_path else get_default_reference()

	@property
	def data(self) -> Dict[str, Any]:
		return self._data

	def get_ranges(self, exercise: str, phase: str) -> Dict[str, Any]:
		return self._data.get(exercise, {}).get(phase, {})
