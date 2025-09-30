from typing import Dict, Optional


class RepCounter:
	def __init__(self, exercise: str) -> None:
		self.exercise = exercise
		self.count = 0
		self.stage: Optional[str] = None  # Using 'stage' to match reference

	def update_with_angle(self, angle: float) -> None:
		"""Update rep count based on angle measurement (for angle-based exercises)"""
		# Bicep Curl logic (elbow angle)
		if self.exercise == "BicepCurl":
			if angle > 160:  # Down position (arm extended)
				self.stage = "down"
			if angle < 30 and self.stage == 'down':  # Up position (arm curled) and previous stage was down
				self.stage = "up"
				self.count += 1
				print(f"Rep Counter (BicepCurl): Completed rep! Count now: {self.count}")
		# Squat logic (knee angle)
		elif self.exercise == "Squat":
			# Standing (up) when knee angle is large; deep squat (down) when small
			if angle > 165:
				self.stage = "up"
			if angle < 90 and self.stage == 'up':
				self.stage = "down"
				self.count += 1
				print(f"Rep Counter (Squat): Completed rep! Count now: {self.count}")

	def update(self, phase_ok: bool, current_phase: str) -> None:
		"""Legacy update method for phase-based exercises"""
		# For exercises that don't use angle-based counting
		if self.exercise in ["Squat", "Plank"]:
			if phase_ok:
				if self.stage is None:
					self.stage = current_phase
					return
				
				# Transition logic depends on exercise
				if self.exercise == "Squat":
					self._update_squat(current_phase)
				elif self.exercise == "Plank":
					self._update_plank(current_phase)

	@property
	def phase(self):
		"""Compatibility property for old code"""
		return self.stage
	
	@phase.setter
	def phase(self, value):
		"""Compatibility property for old code"""
		self.stage = value

	def _update_squat(self, current_phase: str) -> None:
		# one rep: Down -> Up
		if self.stage == "Down" and current_phase == "Up":
			self.count += 1
			self.stage = "Up"
		elif self.stage == "Up" and current_phase == "Down":
			self.stage = "Down"
		else:
			self.stage = current_phase


	def _update_plank(self, current_phase: str) -> None:
		# Plank reps don't increment; we keep stage for HUD
		self.stage = current_phase
