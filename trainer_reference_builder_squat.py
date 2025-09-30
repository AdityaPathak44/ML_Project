"""
Trainer Reference Builder for Squat

This script analyzes a trainer squat video to extract reference angle ranges for:
- Knee (HIP-KNEE-ANKLE)
- Hip (SHOULDER-HIP-KNEE)
- Back (prefer SHOULDER-HIP-KNEE; fallback to SHOULDER-HIP-ANKLE; fallback to vertical)

It processes the video, detects pose landmarks via pose_detector.PoseDetector,
calculates angles per frame, smooths with a moving average, segments into reps
using the knee angle curve (down when decreasing, up when increasing), and then
computes overall reference ranges (Min/Max per joint) aggregated across reps.

Results are merged into references.json at the project root.

Usage:
    python trainer_reference_builder_squat.py
"""

import os
import cv2
import json
import math
import numpy as np
from typing import Dict, List, Tuple, Optional

from pose_detector import PoseDetector, LandmarkPoint
from angle_utils import calculate_angle


def moving_average(values: List[float], window: int = 7) -> np.ndarray:
    """Simple centered moving average with reflection padding for stability."""
    if len(values) == 0:
        return np.array([])
    if window < 2:
        return np.asarray(values, dtype=float)
    arr = np.asarray(values, dtype=float)
    pad = window // 2
    # Reflect pad to avoid edge effects
    padded = np.pad(arr, (pad, pad), mode='reflect')
    kernel = np.ones(window, dtype=float) / window
    smoothed = np.convolve(padded, kernel, mode='valid')
    # Ensure same length
    return smoothed[: len(arr)]


def first_existing_path(paths: List[str]) -> Optional[str]:
    for p in paths:
        if os.path.exists(p):
            return p
    return None


def get_point_xy(lms: Dict[str, LandmarkPoint], name: str) -> Optional[Tuple[float, float]]:
    p = lms.get(name)
    if p is None:
        return None
    return (float(p.x), float(p.y))


def compute_knee_angle(lms: Dict[str, LandmarkPoint]) -> float:
    # Try LEFT then RIGHT
    for side in ("LEFT_", "RIGHT_"):
        hip = get_point_xy(lms, side + "HIP")
        knee = get_point_xy(lms, side + "KNEE")
        ankle = get_point_xy(lms, side + "ANKLE")
        if hip and knee and ankle:
            return calculate_angle(hip, knee, ankle)
    return float("nan")


def compute_hip_angle(lms: Dict[str, LandmarkPoint]) -> float:
    # Try LEFT then RIGHT
    for side in ("LEFT_", "RIGHT_"):
        shoulder = get_point_xy(lms, side + "SHOULDER")
        hip = get_point_xy(lms, side + "HIP")
        knee = get_point_xy(lms, side + "KNEE")
        if shoulder and hip and knee:
            return calculate_angle(shoulder, hip, knee)
    return float("nan")


def compute_back_angle(lms: Dict[str, LandmarkPoint]) -> float:
    """Compute back angle at the hip.
    Priority:
      1) SHOULDER-HIP-KNEE (aligns with runtime FeedbackEngine "Back")
      2) SHOULDER-HIP-ANKLE
      3) Angle of vector HIP->SHOULDER relative to vertical (0, -1)
    """
    # Option 1: shoulder-hip-knee
    for side in ("LEFT_", "RIGHT_"):
        shoulder = get_point_xy(lms, side + "SHOULDER")
        hip = get_point_xy(lms, side + "HIP")
        knee = get_point_xy(lms, side + "KNEE")
        if shoulder and hip and knee:
            return calculate_angle(shoulder, hip, knee)

    # Option 2: shoulder-hip-ankle
    for side in ("LEFT_", "RIGHT_"):
        shoulder = get_point_xy(lms, side + "SHOULDER")
        hip = get_point_xy(lms, side + "HIP")
        ankle = get_point_xy(lms, side + "ANKLE")
        if shoulder and hip and ankle:
            return calculate_angle(shoulder, hip, ankle)

    # Option 3: angle to vertical
    for side in ("LEFT_", "RIGHT_"):
        shoulder = get_point_xy(lms, side + "SHOULDER")
        hip = get_point_xy(lms, side + "HIP")
        if shoulder and hip:
            v = np.array([shoulder[0] - hip[0], shoulder[1] - hip[1]], dtype=float)
            if np.linalg.norm(v) < 1e-6:
                return float("nan")
            v = v / (np.linalg.norm(v) + 1e-12)
            vertical = np.array([0.0, -1.0], dtype=float)
            dot = float(np.clip(np.dot(v, vertical), -1.0, 1.0))
            angle = math.degrees(math.acos(dot))
            # Keep within [0, 180]
            return float(angle)

    return float("nan")


def detect_repetitions_from_knee(knee_sm: np.ndarray) -> List[Tuple[int, int]]:
    """Segment repetitions using knee angle curve.

    A rep is defined from a top (extended, local max) -> bottom (flexed, local min) -> next top.
    We detect local maxima/minima via derivative sign changes and require a minimum prominence
    relative to the angle range to avoid noise.
    """
    n = len(knee_sm)
    if n < 10:
        return []

    # Compute first derivative
    d = np.diff(knee_sm)
    # Slope threshold to avoid reacting to tiny fluctuations
    slope_eps = max(0.1, 0.01 * (np.nanmax(knee_sm) - np.nanmin(knee_sm)))

    # Identify candidate maxima/minima via sign changes
    maxima: List[int] = []
    minima: List[int] = []

    for i in range(1, n - 1):
        prev_s = d[i - 1]
        next_s = d[i]
        # Local max: slope + -> -
        if prev_s > slope_eps and next_s < -slope_eps:
            maxima.append(i)
        # Local min: slope - -> +
        if prev_s < -slope_eps and next_s > slope_eps:
            minima.append(i)

    if len(maxima) < 2 or len(minima) < 1:
        # Attempt to broaden detection by relaxing slope_eps
        slope_eps *= 0.5
        maxima.clear(); minima.clear()
        for i in range(1, n - 1):
            prev_s = d[i - 1]
            next_s = d[i]
            if prev_s > slope_eps and next_s < -slope_eps:
                maxima.append(i)
            if prev_s < -slope_eps and next_s > slope_eps:
                minima.append(i)

    # Enforce prominence: maxima near global high, minima near global low
    if n >= 3:
        knee_min = float(np.nanmin(knee_sm))
        knee_max = float(np.nanmax(knee_sm))
        rng = max(1.0, knee_max - knee_min)
        min_prom = 0.15 * rng  # 15% of range

        maxima = [i for i in maxima if (knee_sm[i] - knee_min) >= min_prom]
        minima = [i for i in minima if (knee_max - knee_sm[i]) >= min_prom]

    reps: List[Tuple[int, int]] = []
    if len(maxima) < 2:
        # Fallback: a single rep from beginning to end if movement exists
        if (np.nanmax(knee_sm) - np.nanmin(knee_sm)) >= 10.0:
            reps.append((0, n - 1))
        return reps

    # Pair consecutive maxima with at least one minimum in between
    for mi in range(len(maxima) - 1):
        start = maxima[mi]
        end = maxima[mi + 1]
        if end <= start + 2:
            continue
        mids = [v for v in minima if start < v < end]
        if not mids:
            # If no explicit minimum found, still treat as a rep if there is sufficient drop
            if knee_sm[start] - np.min(knee_sm[start:end + 1]) >= 5.0:
                reps.append((start, end))
            continue
        # Use deepest valley between the peaks
        valley = int(min(mids, key=lambda idx: knee_sm[idx]))
        reps.append((start, end))

    return reps


class SquatReferenceTrainer:
    def __init__(self, video_path: Optional[str] = None) -> None:
        default_paths = [
            "Trainer_Videos/Squat.mp4",
            "Trainer_Videos/Sqaut.mp4",  # Handle typo in filename
            "Trainer_videos/Squat.mp4",
            "Trainer_videos/Sqaut.mp4",
            "trainer_videos/Squat.mp4",
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

        knee_angles: List[float] = []
        hip_angles: List[float] = []
        back_angles: List[float] = []

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

                k = compute_knee_angle(lms)
                if math.isnan(k):
                    continue  # require knee for rep tracking

                h = compute_hip_angle(lms)
                b = compute_back_angle(lms)

                knee_angles.append(k)
                hip_angles.append(h if not math.isnan(h) else float("nan"))
                back_angles.append(b if not math.isnan(b) else float("nan"))
        finally:
            cap.release()

        print(f"Collected {len(knee_angles)} knee samples")
        return knee_angles, hip_angles, back_angles

    @staticmethod
    def smooth_all(knee: List[float], hip: List[float], back: List[float], window: int = 7) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        return moving_average(knee, window), moving_average(hip, window), moving_average(back, window)

    @staticmethod
    def per_rep_stats(knee: np.ndarray, hip: np.ndarray, back: np.ndarray, reps: List[Tuple[int, int]]) -> Dict[str, List[Tuple[float, float]]]:
        stats: Dict[str, List[Tuple[float, float]]] = {"Knee": [], "Hip": [], "Back": []}
        for (start, end) in reps:
            s = max(0, int(start)); e = min(len(knee) - 1, int(end))
            if e <= s:
                continue
            k_seg = knee[s:e + 1]
            h_seg = hip[s:e + 1]
            b_seg = back[s:e + 1]

            # Use nan-aware min/max
            k_min, k_max = float(np.nanmin(k_seg)), float(np.nanmax(k_seg))
            h_min, h_max = float(np.nanmin(h_seg)), float(np.nanmax(h_seg))
            b_min, b_max = float(np.nanmin(b_seg)), float(np.nanmax(b_seg))

            stats["Knee"].append((k_min, k_max))
            stats["Hip"].append((h_min, h_max))
            stats["Back"].append((b_min, b_max))
        return stats

    @staticmethod
    def aggregate_stats(stats: Dict[str, List[Tuple[float, float]]]) -> Dict[str, Dict[str, float]]:
        out: Dict[str, Dict[str, float]] = {}
        for joint, pairs in stats.items():
            if not pairs:
                continue
            mins = [p[0] for p in pairs if not math.isnan(p[0])]
            maxs = [p[1] for p in pairs if not math.isnan(p[1])]
            if not mins or not maxs:
                continue
            jmin = max(0.0, min(mins))
            jmax = min(180.0, max(maxs))
            out[joint] = {"Min": round(jmin, 1), "Max": round(jmax, 1)}
        return out

    @staticmethod
    def save_references(refs: Dict[str, Dict[str, float]], output_path: str = "references.json") -> None:
        data = {"Squat": refs}
        try:
            existing = {}
            if os.path.exists(output_path):
                with open(output_path, "r") as f:
                    existing = json.load(f)
            # Merge
            existing.update({"Squat": refs})
            with open(output_path, "w") as f:
                json.dump(existing, f, indent=2)
            print(f"Saved/updated references in {output_path}")
        except Exception as e:
            print(f"Error saving references: {e}")

    def build(self) -> bool:
        # 1) Extract angles per frame
        knee, hip, back = self.extract_angles()
        if len(knee) < 10:
            print("Not enough knee angle samples to detect repetitions.")
            return False

        # 2) Smooth sequences (moving average)
        knee_sm, hip_sm, back_sm = self.smooth_all(knee, hip, back, window=7)
        print(f"Angle ranges (smoothed): knee=[{np.nanmin(knee_sm):.1f}, {np.nanmax(knee_sm):.1f}], "
              f"hip=[{np.nanmin(hip_sm):.1f}, {np.nanmax(hip_sm):.1f}], "
              f"back=[{np.nanmin(back_sm):.1f}, {np.nanmax(back_sm):.1f}]")

        # 3) Detect repetitions using knee angle curve
        reps = detect_repetitions_from_knee(knee_sm)
        print(f"Detected {len(reps)} repetitions")
        if not reps:
            # Fallback: treat whole sequence as one rep if sufficient movement
            if (np.nanmax(knee_sm) - np.nanmin(knee_sm)) >= 10.0:
                reps = [(0, len(knee_sm) - 1)]
                print("Using entire sequence as a single repetition fallback.")
            else:
                print("Insufficient movement to define a repetition.")
                return False

        # 4) Per-rep stats and aggregate
        stats = self.per_rep_stats(knee_sm, hip_sm, back_sm, reps)
        agg = self.aggregate_stats(stats)
        if not agg or any(j not in agg for j in ("Knee", "Hip", "Back")):
            print("Could not compute complete aggregate stats for all joints.")
            return False

        # 5) Save to references.json
        self.save_references(agg, output_path="references.json")
        print("Final Squat reference ranges:")
        print(json.dumps({"Squat": agg}, indent=2))
        return True


def main() -> int:
    trainer = SquatReferenceTrainer()
    # Normalize path resolution, try alternates if default missing
    if not os.path.exists(trainer.video_path):
        alt = first_existing_path([
            "Trainer_videos/Squat.mp4",
            "trainer_videos/Squat.mp4",
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

