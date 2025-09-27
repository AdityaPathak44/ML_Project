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


def draw_overlay(frame, angles: Dict[str, float], exercise: str, phase: str, ok: bool, msg: str, reps: int) -> None:
	# HUD
	cv2.rectangle(frame, (0, 0), (350, 160), (0, 0, 0), -1)
	cv2.putText(frame, f"Exercise: {exercise}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
	cv2.putText(frame, f"Phase: {phase}", (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
	cv2.putText(frame, f"Reps: {reps}", (10, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
	color = (0, 200, 0) if ok else (0, 0, 255)
	cv2.putText(frame, msg, (10, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
	cv2.putText(frame, "Keys: 1=Squat 2=Push-up 3=Plank 4=Dumbbell Crunch", (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
	# Angle readouts (right side)
	x0 = frame.shape[1] - 220
	cv2.rectangle(frame, (x0 - 10, 0), (frame.shape[1], 170), (0, 0, 0), -1)
	i = 0
	for k in ["Knee", "Hip", "Elbow", "Shoulder", "Back"]:
		ang = angles.get(k, float('nan'))
		cv2.putText(frame, f"{k}: {"%.0f" % ang if ang == ang else "-"}", (x0, 25 + i * 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
		i += 1


def main():
	exercise = "Dumbbell Crunch"  # change to "Squat", "Push-up", or "Plank" as needed
	ref_provider = ReferenceProvider(json_path="references.json")
	refs = ref_provider.data
	engine = FeedbackEngine()
	detector = PoseDetector(model_complexity=1, min_detection_confidence=0.5, min_tracking_confidence=0.5)
	reps = RepCounter(exercise)

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

			# Determine current phase and feedback
			exercise_refs = refs.get(exercise, {})
			if exercise == "Plank":
				phase = "Hold"
				ok, msg = engine.check_feedback(exercise, phase, exercise_refs.get(phase, {}), angles)
				reps.update(ok, phase)
			else:
				phase, ok, msg = choose_phase(exercise, angles, exercise_refs, engine)
				reps.update(ok, phase)
			

			# Draw pose and overlays
			detector.draw(frame, results)
			draw_overlay(frame, angles, exercise, phase, ok, msg, reps.count)

			cv2.imshow(WINDOW_NAME, frame)
			key = cv2.waitKey(30) & 0xFF  # Increased wait time for better key detection
			if key == ord('q'):
				break
			elif key == ord('1'):
				exercise = "Squat"
				reps = RepCounter(exercise)
			elif key == ord('2'):
				exercise = "Push-up"
				reps = RepCounter(exercise)
			elif key == ord('3'):
				exercise = "Plank"
				reps = RepCounter(exercise)
			elif key == ord('4'):
				exercise = "Dumbbell Crunch"
				reps = RepCounter(exercise)

	finally:
		cap.release()
		cv2.destroyAllWindows()


if __name__ == "__main__":
	main()
