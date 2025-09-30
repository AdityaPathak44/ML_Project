import cv2
import numpy as np
from typing import Dict, Tuple

from pose_detector import PoseDetector
from reference_loader import ReferenceProvider
from feedback import FeedbackEngine
from rep_counter import RepCounter


WINDOW_NAME = "AI Exercise Form Corrector"


def choose_phase(exercise: str, angles: Dict[str, float], refs: Dict[str, Dict[str, Tuple[float, float]]], engine: FeedbackEngine) -> Tuple[str, bool, str]:
	# Determine the most likely phase by checking which phase matches more joints
	best_phase = None
	best_score = -1
	best_ok = False
	best_msg = ""
	for phase, reqs in refs.items():
		score = 0
		ok_all = True
		for joint, rng in reqs.items():
			ang = angles.get(joint, float('nan'))
			if ang != ang:
				ok_all = False
				continue
			lo, hi = rng
			if lo <= ang <= hi:
				score += 1
			else:
				ok_all = False
		is_better = score > best_score or (score == best_score and ok_all and not best_ok)
		if is_better:
			best_phase = phase
			best_score = score
			best_ok, best_msg = engine.check_feedback(exercise, phase, reqs, angles)
	if best_phase is None:
		best_phase = next(iter(refs.keys()))
	return best_phase, best_ok, best_msg


def draw_overlay(frame, angles: Dict[str, float], exercise: str, phase: str, ok: bool, msg: str, reps: int, plank_info=None) -> None:
	# HUD - make it taller for plank info
	hud_height = 200 if exercise == "Plank" and plank_info else 160
	cv2.rectangle(frame, (0, 0), (350, hud_height), (0, 0, 0), -1)
	cv2.putText(frame, f"Exercise: {exercise}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
	cv2.putText(frame, f"Phase: {phase}", (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
	
	if exercise == "Plank" and plank_info:
		# Show plank timer information
		elapsed, total, active, left_angle, right_angle = plank_info
		status = "ACTIVE" if active else "WAITING"
		status_color = (0, 255, 0) if active else (0, 215, 255)
		cv2.putText(frame, f"Timer: {elapsed:.1f}s", (10, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
		cv2.putText(frame, f"Status: {status}", (10, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
		cv2.putText(frame, f"Total: {total:.1f}s", (10, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
		# Show hip angles
		if left_angle is not None:
			cv2.putText(frame, f"L Hip: {left_angle:.0f}°", (10, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
		if right_angle is not None:
			cv2.putText(frame, f"R Hip: {right_angle:.0f}°", (150, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
	else:
		cv2.putText(frame, f"Reps: {reps}", (10, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
		color = (0, 200, 0) if ok else (0, 0, 255)
		cv2.putText(frame, msg, (10, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
	
	cv2.putText(frame, "Keys: 1=Squat 2=Plank 3=BicepCurl", (10, hud_height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
	# Angle readouts (right side)
	x0 = frame.shape[1] - 220
	cv2.rectangle(frame, (x0 - 10, 0), (frame.shape[1], 170), (0, 0, 0), -1)
	i = 0
	for k in ["Knee", "Hip", "Elbow", "Shoulder", "Back"]:
		ang = angles.get(k, float('nan'))
		cv2.putText(frame, f"{k}: {"%.0f" % ang if ang == ang else "-"}", (x0, 25 + i * 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
		i += 1


def main():
	global plank_timer_active, plank_start_time, plank_total_time, plank_last_duration
	
	exercise = "Squat"  # change to "Squat", "Plank", or "BicepCurl" as needed
	ref_provider = ReferenceProvider(json_path="references.json")
	refs = ref_provider.data
	engine = FeedbackEngine()
	detector = PoseDetector(model_complexity=1, min_detection_confidence=0.5, min_tracking_confidence=0.5)
	reps = RepCounter(exercise)
	
	# Load trained plank ranges
	load_plank_trained_ranges(ref_provider)

	cap = cv2.VideoCapture(0)
	if not cap.isOpened():
		print("Could not open webcam.")
		return

	try:
		while True:
			ret, frame = cap.read()
			if not ret:
				break
			frame = cv2.flip(frame, 1)

			results = detector.process(frame)
			lms = detector.get_landmarks(frame, results)
			angles: Dict[str, float] = {}
			if lms is not None:
				angles = engine.compute_all_angles(lms)

			# Handle angle-based exercises (BicepCurl and Squat) using direct angle measurement
			if lms is not None and exercise in ["BicepCurl", "Squat"]:
				if exercise == "BicepCurl":
					# Calculate elbow angle for bicep curl using LEFT side (as in your example)
					for side_prefix in ["LEFT_", "RIGHT_"]:
						shoulder_key = side_prefix + "SHOULDER"
						elbow_key = side_prefix + "ELBOW"
						wrist_key = side_prefix + "WRIST"
						if all(key in lms for key in [shoulder_key, elbow_key, wrist_key]):
							shoulder = [lms[shoulder_key].x, lms[shoulder_key].y]
							elbow = [lms[elbow_key].x, lms[elbow_key].y]
							wrist = [lms[wrist_key].x, lms[wrist_key].y]
							
							# Calculate angle using your bicep curl formula
							a = np.array(shoulder)
							b = np.array(elbow)
							c = np.array(wrist)
							radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
							angle = np.abs(radians*180.0/np.pi)
							if angle > 180.0:
								angle = 360 - angle
							
							reps.update_with_angle(angle)
							break
					
				elif exercise == "Squat":
					# Calculate knee angle for squat using RIGHT side (as in your example)
					for side_prefix in ["RIGHT_", "LEFT_"]:
						hip_key = side_prefix + "HIP"
						knee_key = side_prefix + "KNEE"
						ankle_key = side_prefix + "ANKLE"
						if all(key in lms for key in [hip_key, knee_key, ankle_key]):
							hip = [lms[hip_key].x, lms[hip_key].y]
							knee = [lms[knee_key].x, lms[knee_key].y]
							ankle = [lms[ankle_key].x, lms[ankle_key].y]
							
							# Calculate angle using your squat formula (cosine method)
							a = np.array(hip)
							b = np.array(knee)
							c = np.array(ankle)
							ba = a - b
							bc = c - b
							cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
							angle = np.degrees(np.arccos(np.clip(cosine_angle, -1.0, 1.0)))
							
							reps.update_with_angle(angle)
							break
			
			# Handle exercise-specific logic
			exercise_refs = refs.get(exercise, {})
			plank_info = None
			
			if exercise == "Plank":
				# Use trained plank detection
				phase = "Hold"
				if lms is not None:
					is_proper_plank, left_angle, right_angle = check_plank_position(lms)
					update_plank_timer(is_proper_plank)
					ok = is_proper_plank
					msg = "Good plank posture!" if ok else "Adjust your posture"
				else:
					ok = False
					msg = "Position yourself for plank"
					left_angle = right_angle = None
					
				# Prepare plank info for overlay
				elapsed = get_plank_elapsed_time()
				plank_info = (elapsed, plank_total_time, plank_timer_active, left_angle, right_angle)
				
			elif exercise in ["BicepCurl", "Squat"]:
				# For angle-based exercises, use the stage from rep counter
				phase = reps.stage if reps.stage else "up"
				ok = True  # Simplified feedback for angle-based exercises
				if exercise == "BicepCurl":
					msg = f"Bicep Curl - Stage: {phase.title()}"
				else:
					msg = f"Squat - Stage: {phase.title()}"
			else:
				phase, ok, msg = choose_phase(exercise, angles, exercise_refs, engine)
				reps.update(ok, phase)
			

			# Draw pose and overlays
			detector.draw(frame, results)
			draw_overlay(frame, angles, exercise, phase, ok, msg, reps.count, plank_info)

			cv2.imshow(WINDOW_NAME, frame)
			key = cv2.waitKey(30) & 0xFF  # Increased wait time for better key detection
			if key == ord('q'):
				break
			elif key == ord('1'):
				exercise = "Squat"
				reps = RepCounter(exercise)
			elif key == ord('2'):
				exercise = "Plank"
				reps = RepCounter(exercise)
				# Reset plank timer when switching to plank
				plank_timer_active = False
				plank_start_time = None
				plank_total_time = 0.0
				plank_last_duration = 0.0
				print("[Plank] Timer reset for new session")
			elif key == ord('3'):
				exercise = "BicepCurl"
				reps = RepCounter(exercise)

	finally:
		cap.release()
		cv2.destroyAllWindows()


# ---- Plank Timer functionality ----
import os
import time
from datetime import datetime
from angle_utils import calculate_angle


# Plank Timer State
plank_timer_active = False
plank_start_time = None
plank_total_time = 0.0
plank_last_duration = 0.0
plank_trained_ranges = None

def load_plank_trained_ranges(ref_provider):
	"""Load trained plank reference ranges from references.json"""
	global plank_trained_ranges
	try:
		# Access the data directly from the provider
		plank_data = ref_provider.data.get("Plank", {})
		if "Hip" in plank_data:
			hip_ref = plank_data["Hip"]
			if "Min" in hip_ref and "Max" in hip_ref:
				plank_trained_ranges = (hip_ref["Min"], hip_ref["Max"])
				print(f"[Plank] Loaded trained reference ranges: {plank_trained_ranges[0]:.1f}° - {plank_trained_ranges[1]:.1f}°")
				return True
	except Exception as e:
		print(f"[Plank] Could not load trained references: {e}")
	return False

def check_plank_position(lms):
	"""Check if current pose is a proper plank using trained model"""
	global plank_trained_ranges
	
	# Use trained ranges if available, otherwise defaults
	thresh_low, thresh_high = (165.0, 180.0) if plank_trained_ranges is None else plank_trained_ranges
	
	ok_left = ok_right = False
	left_angle = right_angle = None
	
	for side in ["LEFT_", "RIGHT_"]:
		shoulder_key = side + "SHOULDER"
		hip_key = side + "HIP"
		ankle_key = side + "ANKLE"
		if all(k in lms for k in [shoulder_key, hip_key, ankle_key]):
			shoulder = (lms[shoulder_key].x, lms[shoulder_key].y)
			hip = (lms[hip_key].x, lms[hip_key].y)
			ankle = (lms[ankle_key].x, lms[ankle_key].y)
			ang = calculate_angle(shoulder, hip, ankle)
			
			if side == "LEFT_":
				left_angle = ang
				if thresh_low <= ang <= thresh_high:
					ok_left = True
			else:
				right_angle = ang
				if thresh_low <= ang <= thresh_high:
					ok_right = True
	
	return ok_left and ok_right, left_angle, right_angle

def update_plank_timer(is_proper_plank):
	"""Update plank timer based on posture"""
	global plank_timer_active, plank_start_time, plank_total_time, plank_last_duration
	
	if is_proper_plank and not plank_timer_active:
		# Start timer
		plank_timer_active = True
		plank_start_time = time.time()
		print("[Plank] Timer started!")
	elif not is_proper_plank and plank_timer_active:
		# Stop timer and record duration
		end_time = time.time()
		plank_last_duration = end_time - plank_start_time
		plank_total_time += plank_last_duration
		plank_timer_active = False
		plank_start_time = None
		print(f"[Plank] Timer stopped! Duration: {plank_last_duration:.1f}s, Total: {plank_total_time:.1f}s")

def get_plank_elapsed_time():
	"""Get current elapsed time for active plank"""
	if plank_timer_active and plank_start_time:
		return time.time() - plank_start_time
	return 0.0


if __name__ == "__main__":
	main()
