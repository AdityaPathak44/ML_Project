"""
Trainer Reference Builder for Push-up

This script analyzes a trainer push-up video to extract reference angle ranges for:
- Elbow (SHOULDER-ELBOW-WRIST)
- Shoulder (HIP-SHOULDER-ELBOW)
- Back (SHOULDER-HIP-ANKLE) — body straightness proxy

It processes the video, detects pose landmarks via pose_detector.PoseDetector,
calculates angles per frame, smooths via moving average, segments reps using the
elbow angle curve (down when decreasing, up when increasing), and computes overall
reference ranges (Min/Max per joint) aggregated across reps.

Results are merged into references.json at the project root under the key "Pushup".

Usage:
    python trainer_reference_builder_pushup.py
"""

import os
import json
from typing import Dict, List, Tuple, Optional

import cv2
import numpy as np
from scipy.signal import find_peaks

from pose_detector import PoseDetector, LandmarkPoint
from angle_utils import calculate_angle


def moving_average(values: List[float], window: int = 7) -> np.ndarray:
    if len(values) == 0:
        return np.array([])
    if window < 2:
        return np.asarray(values, dtype=float)
    arr = np.asarray(values, dtype=float)
    pad = window // 2
    padded = np.pad(arr, (pad, pad), mode='reflect')
    kernel = np.ones(window, dtype=float) / window
    smoothed = np.convolve(padded, kernel, mode='valid')
    return smoothed[: len(arr)]


def first_existing_path(paths: List[str]) -> Optional[str]:
    for p in paths:
        if os.path.exists(p):
            return p
    return None


def get_xy(lms: Dict[str, LandmarkPoint], name: str) -> Optional[Tuple[float, float]]:
    p = lms.get(name)
    if p is None:
        return None
    return (float(p.x), float(p.y))


def compute_elbow_angle(lms: Dict[str, LandmarkPoint]) -> float:
    for side in ("LEFT_", "RIGHT_"):
        a = get_xy(lms, side + "SHOULDER")
        b = get_xy(lms, side + "ELBOW")
        c = get_xy(lms, side + "WRIST")
        if a and b and c:
            return calculate_angle(a, b, c)
    return float('nan')


def compute_shoulder_angle(lms: Dict[str, LandmarkPoint]) -> float:
    for side in ("LEFT_", "RIGHT_"):
        a = get_xy(lms, side + "HIP")
        b = get_xy(lms, side + "SHOULDER")
        c = get_xy(lms, side + "ELBOW")
        if a and b and c:
            return calculate_angle(a, b, c)
    return float('nan')


def compute_back_angle(lms: Dict[str, LandmarkPoint]) -> float:
    for side in ("LEFT_", "RIGHT_"):
        a = get_xy(lms, side + "SHOULDER")
        b = get_xy(lms, side + "HIP")
        c = get_xy(lms, side + "ANKLE")
        if a and b and c:
            return calculate_angle(a, b, c)
    return float('nan')


def detect_repetitions_from_elbow(elbow_sm: np.ndarray) -> List[Tuple[int, int]]:
    """
    Segment repetitions using elbow angle curve.
    A rep is approximated as max (up/extended) -> min (down/bent) -> next max.
    """
    n = len(elbow_sm)
    if n < 10:
        return []

    # Find peaks (extended arms, large elbow angle)
    rng = float(np.nanmax(elbow_sm) - np.nanmin(elbow_sm)) if n > 0 else 0.0
    prominence = max(5.0, 0.15 * rng)
    distance = max(10, n // 30)  # roughly space peaks

    peaks, _ = find_peaks(elbow_sm, prominence=prominence, distance=distance)
    valleys, _ = find_peaks(-elbow_sm, prominence=prominence, distance=distance)

    reps: List[Tuple[int, int]] = []
    if len(peaks) < 2:
        # Fallback: if we see a decent movement range, treat whole sequence as one rep
        if rng >= 15.0:
            reps.append((0, n - 1))
        return reps

    for i in range(len(peaks) - 1):
        start = int(peaks[i])
        end = int(peaks[i + 1])
        if end <= start + 2:
            continue
        mids = [v for v in valleys if start < v < end]
        # Accept if there is a valley in between or if there is significant drop
        if mids or (np.nanmax(elbow_sm[start:end+1]) - np.nanmin(elbow_sm[start:end+1]) >= 10.0):
            reps.append((start, end))

    # De-duplicate or merge overlapping segments
    merged: List[Tuple[int, int]] = []
    for seg in reps:
        if not merged or seg[0] > merged[-1][1]:
            merged.append(seg)
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], seg[1]))
    return merged


class PushupReferenceTrainer:
    def __init__(self, video_path: Optional[str] = None) -> None:
        default_paths = [
            "Trainer_Videos/pushUps.mp4",  # Correct filename found in directory
            "Trainer_Videos/pushup.mp4",
            "Trainer_Videos/Pushup.mp4",
            "Trainer_videos/pushup.mp4",
            "trainer_videos/pushup.mp4",
        ]
        self.video_path = video_path or first_existing_path(default_paths) or default_paths[0]
        self.detector = PoseDetector(
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    def extract_angles(self) -> Tuple[List[float], List[float], List[float]]:
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video file: {self.video_path}")

        elbow: List[float] = []
        shoulder: List[float] = []
        back: List[float] = []

        total = int(max(1, cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        frame_idx = 0
        print(f"Processing video: {self.video_path}")

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frame_idx += 1
                if frame_idx % 20 == 0:
                    pct = 100.0 * (frame_idx / total)
                    print(f"Processed {frame_idx}/{total} frames ({pct:.1f}%)")

                results = self.detector.process(frame)
                lms = self.detector.get_landmarks(frame, results)
                if not lms:
                    continue

                e = compute_elbow_angle(lms)
                s = compute_shoulder_angle(lms)
                b = compute_back_angle(lms)

                # Keep only frames where all are available for consistent analysis
                if not (np.isnan(e) or np.isnan(s) or np.isnan(b)):
                    elbow.append(e)
                    shoulder.append(s)
                    back.append(b)
        finally:
            cap.release()

        print(f"Collected samples: elbow={len(elbow)}, shoulder={len(shoulder)}, back={len(back)}")
        return elbow, shoulder, back

    @staticmethod
    def smooth_all(elbow: List[float], shoulder: List[float], back: List[float], window: int = 7) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        return moving_average(elbow, window), moving_average(shoulder, window), moving_average(back, window)

    @staticmethod
    def per_rep_stats(elbow: np.ndarray, shoulder: np.ndarray, back: np.ndarray, reps: List[Tuple[int, int]]) -> Dict[str, List[Tuple[float, float]]]:
        stats: Dict[str, List[Tuple[float, float]]] = {"Elbow": [], "Shoulder": [], "Back": []}
        for (start, end) in reps:
            s = max(0, int(start)); e = min(len(elbow) - 1, int(end))
            if e <= s:
                continue
            e_seg = elbow[s:e + 1]
            s_seg = shoulder[s:e + 1]
            b_seg = back[s:e + 1]

            e_min, e_max = float(np.nanmin(e_seg)), float(np.nanmax(e_seg))
            s_min, s_max = float(np.nanmin(s_seg)), float(np.nanmax(s_seg))
            b_min, b_max = float(np.nanmin(b_seg)), float(np.nanmax(b_seg))

            stats["Elbow"].append((e_min, e_max))
            stats["Shoulder"].append((s_min, s_max))
            stats["Back"].append((b_min, b_max))
        return stats

    @staticmethod
    def aggregate_stats(stats: Dict[str, List[Tuple[float, float]]]) -> Dict[str, Dict[str, float]]:
        out: Dict[str, Dict[str, float]] = {}
        for joint, pairs in stats.items():
            if not pairs:
                continue
            mins = [p[0] for p in pairs if not np.isnan(p[0])]
            maxs = [p[1] for p in pairs if not np.isnan(p[1])]
            if not mins or not maxs:
                continue
            jmin = max(0.0, min(mins))
            jmax = min(180.0, max(maxs))
            out[joint] = {"Min": round(jmin, 1), "Max": round(jmax, 1)}
        return out

    @staticmethod
    def save_references(refs: Dict[str, Dict[str, float]], output_path: str = "references.json") -> None:
        data = {"Pushup": refs}
        try:
            existing = {}
            if os.path.exists(output_path):
                with open(output_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            existing.update({"Pushup": refs})
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2)
            print(f"Saved/updated references in {output_path}")
        except Exception as e:
            print(f"Error saving references: {e}")

    def build(self) -> bool:
        # 1) Extract angles per frame
        elbow, shoulder, back = self.extract_angles()
        if len(elbow) < 10:
            print("Not enough samples to detect repetitions.")
            return False

        # 2) Smooth sequences (moving average)
        e_sm, s_sm, b_sm = self.smooth_all(elbow, shoulder, back, window=7)
        print(f"Smoothed ranges: elbow=[{np.nanmin(e_sm):.1f}, {np.nanmax(e_sm):.1f}], "
              f"shoulder=[{np.nanmin(s_sm):.1f}, {np.nanmax(s_sm):.1f}], "
              f"back=[{np.nanmin(b_sm):.1f}, {np.nanmax(b_sm):.1f}]")

        # 3) Detect repetitions using elbow angle curve
        reps = detect_repetitions_from_elbow(e_sm)
        print(f"Detected {len(reps)} repetitions")
        if not reps:
            # Fallback: treat whole sequence as one rep if sufficient movement
            if (np.nanmax(e_sm) - np.nanmin(e_sm)) >= 10.0:
                reps = [(0, len(e_sm) - 1)]
                print("Using entire sequence as a single repetition fallback.")
            else:
                print("Insufficient movement to define a repetition.")
                return False

        # 4) Per-rep stats and aggregate
        stats = self.per_rep_stats(e_sm, s_sm, b_sm, reps)
        agg = self.aggregate_stats(stats)
        if not agg or any(j not in agg for j in ("Elbow", "Shoulder", "Back")):
            print("Could not compute complete aggregate stats for all joints.")
            return False

        # 5) Save to references.json
        self.save_references(agg, output_path="references.json")
        print("Final Pushup reference ranges:")
        print(json.dumps({"Pushup": agg}, indent=2))
        return True


def main() -> int:
    trainer = PushupReferenceTrainer()
    if not os.path.exists(trainer.video_path):
        alt = first_existing_path([
            "Trainer_videos/pushup.mp4",
            "trainer_videos/pushup.mp4",
            "Trainer_Videos/Pushup.mp4",
        ])
        if alt:
            print(f"Warning: Using alternate video path: {alt}")
            trainer.video_path = alt
        else:
            print(f"Error: Trainer video not found at {trainer.video_path}")
            return 1

    ok = trainer.build()
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

