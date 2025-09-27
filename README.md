# AI Exercise Form Corrector

Real-time exercise form feedback using OpenCV, MediaPipe Pose, and NumPy. Supports Squat (with rep counting), Push-up, and Plank basics. Displays live angles, feedback, and rep count.

## Setup

```bash
python -m venv .venv
.\.venv\Scripts\activate  # on Windows PowerShell
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

- Press `1` Squat, `2` Push-up, `3` Plank
- Press `q` to quit

## Project Structure

- `main.py`: App entry point; webcam loop, overlays
- `pose_detector.py`: MediaPipe wrapper for detection and drawing
- `angle_utils.py`: NumPy angle math utilities
- `feedback.py`: Computes joint angles and feedback against references
- `rep_counter.py`: Phase machine and repetition counting
- `reference_loader.py`: Load JSON/default reference ranges
- `references.json`: Sample reference ranges

## How it works

1. Detects pose landmarks via MediaPipe
2. Computes joint angles (Knee, Hip, Elbow, Shoulder, Back)
3. Chooses phase by best-matching reference ranges; validates feedback
4. Counts reps (Squat/Push-up) based on phase transitions
5. Renders landmarks, angles, phase, feedback, and rep count

## Extend

- Supabase reference data
  - Use `supabase-py` to fetch references instead of JSON.
  - Store as table `exercise_references(exercise, phase, joint, low, high)` and cache locally.
- User-specific tracking
  - Create tables `sessions(user_id, started_at)`, `session_events(session_id, t, exercise, phase, rep, ok)`
  - Log each frame/phase change; compute per-session accuracy and total reps.
- Voice feedback
  - Use `pyttsx3` (offline) or `edge-tts`/`gTTS` for TTS to speak `msg` when it changes.

## Notes

- Angle thresholds are approximate; tune per camera setup.
- Ensure good lighting and keep the full body visible for best accuracy.
