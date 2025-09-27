from typing import Dict, Optional


class RepCounter:
	def __init__(self, exercise: str) -> None:
		self.exercise = exercise
		self.count = 0
		self.phase: Optional[str] = None
		self._last_good: Optional[str] = None

	def update(self, phase_ok: bool, current_phase: str) -> None:
		# Start phase tracking when we first see a valid phase
		if phase_ok:
			if self.phase is None:
				self.phase = current_phase
				self._last_good = current_phase
				return
		# Transition logic depends on exercise
		if self.exercise == "Squat":
			self._update_squat(current_phase)
		elif self.exercise == "Push-up":
			self._update_pushup(current_phase)
		elif self.exercise == "Plank":
			self._update_plank(current_phase)
		elif self.exercise == "Dumbbell Crunch":
			self._update_dumbbell_crunch(current_phase)

	def _update_squat(self, current_phase: str) -> None:
		# one rep: Down -> Up
		if self.phase == "Down" and current_phase == "Up":
			self.count += 1
			self.phase = "Up"
		elif self.phase == "Up" and current_phase == "Down":
			self.phase = "Down"
		else:
			self.phase = current_phase

	def _update_pushup(self, current_phase: str) -> None:
		# one rep: Down -> Up
		if self.phase == "Down" and current_phase == "Up":
			self.count += 1
			self.phase = "Up"
		elif self.phase == "Up" and current_phase == "Down":
			self.phase = "Down"
		else:
			self.phase = current_phase

	def _update_plank(self, current_phase: str) -> None:
		# Plank reps don't increment; we keep phase for HUD
		self.phase = current_phase

	def _update_dumbbell_crunch(self, current_phase: str) -> None:
		# one rep: Up -> Down -> Up (bicep curl motion)
		if self.phase == "Up" and current_phase == "Down":
			self.phase = "Down"
		elif self.phase == "Down" and current_phase == "Up":
			self.count += 1
			self.phase = "Up"
		else:
			self.phase = current_phase
