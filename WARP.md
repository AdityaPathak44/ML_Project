# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Development Commands

### Environment Setup
```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```powershell
# Run the main exercise form corrector
python main.py

# Interactive controls once running:
# Press '1' for Squat mode
# Press '2' for Push-up mode  
# Press '3' for Plank mode
# Press '4' for Dumbbell Crunch mode
# Press 'q' to quit
```

### Development and Testing
```powershell
# Run specific exercise mode for testing
python -c "
exercise = 'Squat'  # Change to 'Push-up', 'Plank', or 'Dumbbell Crunch'
exec(open('main.py').read())
"

# Test individual components
python -c "from pose_detector import PoseDetector; print('PoseDetector imported successfully')"
python -c "from feedback import FeedbackEngine; print('FeedbackEngine imported successfully')"
python -c "from angle_utils import calculate_angle; print('angle_utils imported successfully')"
```

## Architecture Overview

### Core Components

**main.py** - Application entry point and orchestration
- Manages webcam capture loop and OpenCV display
- Coordinates all components (pose detection, feedback, rep counting)
- Handles exercise mode switching and UI overlays
- Contains the phase detection logic that determines exercise states

**pose_detector.py** - MediaPipe pose estimation wrapper  
- Wraps MediaPipe Pose for landmark detection
- Converts MediaPipe landmarks to normalized pixel coordinates
- Provides drawing utilities for pose visualization
- Returns structured LandmarkPoint objects with visibility scores

**feedback.py** - Exercise form analysis engine
- Defines joint angle calculations using JOINT_DEFINITIONS mapping
- Maps human-readable joint names to MediaPipe landmark triplets
- Computes angles for Knee, Hip, Elbow, Shoulder, Back, and Arm joints
- Validates form against reference ranges and generates feedback messages

**angle_utils.py** - Mathematical utilities for angle computation
- Pure NumPy-based angle calculation between three points
- Handles edge cases (zero-length vectors, NaN values)
- Range validation utilities for form checking

**rep_counter.py** - Exercise repetition counting state machine
- Maintains exercise-specific state machines for rep counting
- Handles phase transitions: Squat/Push-up (Down↔Up), Plank (Hold), Dumbbell Crunch (Up↔Down)
- Tracks current phase and total completed repetitions

**reference_loader.py** - Exercise reference data management
- Loads exercise reference ranges from JSON configuration
- Provides fallback defaults if JSON is unavailable
- Manages exercise-specific angle thresholds per phase

### Data Flow Architecture

1. **Pose Detection Pipeline**: main.py → PoseDetector → MediaPipe → LandmarkPoint objects
2. **Angle Computation**: LandmarkPoint objects → FeedbackEngine → angle_utils → joint angles
3. **Phase Detection**: Joint angles + reference_loader data → choose_phase() → current exercise phase
4. **Form Validation**: Current phase + angles → FeedbackEngine.check_feedback() → form feedback
5. **Rep Counting**: Phase transitions → RepCounter → updated rep count
6. **Display**: All computed data → draw_overlay() → OpenCV visualization

### Key Design Patterns

**Component Separation**: Each major function (pose detection, feedback, counting) is isolated in separate modules with clear interfaces.

**State Machine Pattern**: RepCounter uses exercise-specific state machines to track phase transitions and count repetitions.

**Strategy Pattern**: Different exercises use the same core components but with different reference data and phase logic.

**Data Pipeline**: Unidirectional flow from raw camera input through pose detection, angle computation, phase detection, to final display.

## Configuration Files

**references.json** - Exercise reference angle ranges
- Defines acceptable angle ranges for each exercise phase
- Structure: `{exercise: {phase: {joint: [min_angle, max_angle]}}}`
- Easily extensible for new exercises or refined thresholds

**requirements.txt** - Python dependencies
- Core: opencv-python, mediapipe, tensorflow, numpy
- Fixed versions for MediaPipe (0.10.13) and TensorFlow (2.15.0) for stability

## Frontend Integration

The `frontend/` directory contains HTML files for a web interface:
- Static HTML pages for login, landing, workout, dashboard, and features
- Currently separate from the Python computer vision backend
- Potential integration point for web-based exercise tracking

## Extension Points

**New Exercise Types**: Add to JOINT_DEFINITIONS in feedback.py, update references.json, and add phase logic to rep_counter.py.

**Database Integration**: Replace reference_loader.py JSON with database queries (suggested: Supabase integration).

**Real-time Analytics**: Extend RepCounter to log detailed session data including frame-by-frame form accuracy.

**Voice Feedback**: Integrate TTS engines (pyttsx3, edge-tts) to speak feedback messages from FeedbackEngine.

## Technical Notes

- MediaPipe Pose uses normalized coordinates (0-1 range) which are converted to pixel coordinates
- Angle calculations handle both left and right body sides, falling back if landmarks are not visible
- The system is designed for single-person pose detection in good lighting conditions
- Camera calibration may be needed for different setups - adjust reference ranges in references.json accordingly
