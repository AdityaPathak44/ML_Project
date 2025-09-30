"""
Standalone Squat Counter - Similar to your provided script

This script replicates the exact functionality of your squat counter example
using the same MediaPipe approach and angle calculation method.
"""

import cv2
import mediapipe as mp
import numpy as np

# Initialize MediaPipe drawing utilities and pose model
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose


def calculate_angle(a, b, c):
    """Calculate angle between three points - matches your script exactly"""
    a = np.array(a)  # First point (e.g., hip)
    b = np.array(b)  # Mid point (e.g., knee)
    c = np.array(c)  # End point (e.g., ankle)

    # Calculate vectors
    ba = a - b
    bc = c - b

    # Calculate cosine of angle using dot product
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.degrees(np.arccos(cosine_angle))

    return angle


def main():
    """Main squat counter - matches your script functionality"""
    # --- Main Squat Counter Logic ---
    cap = cv2.VideoCapture(0)  # 0 for default webcam

    # Squat counter variables
    squat_counter = 0
    squat_stage = None  # "up" or "down"

    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break

            # Recolor image to RGB for MediaPipe
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False

            # Make detection
            results = pose.process(image)

            # Recolor back to BGR for OpenCV
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            try:
                landmarks = results.pose_landmarks.landmark

                # Get coordinates for the right knee angle (or left, choose one consistently)
                # Hip: mp_pose.PoseLandmark.RIGHT_HIP
                # Knee: mp_pose.PoseLandmark.RIGHT_KNEE
                # Ankle: mp_pose.PoseLandmark.RIGHT_ANKLE

                # We need the x and y coordinates for 2D angle calculation
                hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,
                       landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
                knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x,
                        landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
                ankle = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x,
                         landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y]

                # Calculate the angle at the knee joint
                knee_angle = calculate_angle(hip, knee, ankle)

                # --- Squat counter logic ---
                # You might need to adjust these angle thresholds based on your typical squat form
                # For "up" position, knee angle should be relatively large (leg straight)
                # For "down" position, knee angle should be relatively small (squatted)
                if knee_angle > 165:  # Standing up straight (or near straight)
                    squat_stage = "up"
                if knee_angle < 90 and squat_stage == 'up':  # Deep squat position, coming from 'up'
                    squat_stage = "down"
                    squat_counter += 1

                # --- Visualizations ---
                # Display the calculated angle
                # Convert normalized coordinates to pixel coordinates for text placement
                knee_pixel_coords = tuple(np.multiply(knee, [frame.shape[1], frame.shape[0]]).astype(int))
                cv2.putText(image, f"Knee Angle: {int(knee_angle)}",
                            (knee_pixel_coords[0] - 50, knee_pixel_coords[1] - 30),  # Adjust text position
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

            except Exception as e:
                # print(f"Error extracting landmarks or calculating angle: {e}")
                pass  # Continue if landmarks are not fully detected

            # --- Render Counter and Stage ---
            # Setup status box
            cv2.rectangle(image, (0, 0), (280, 73), (245, 117, 16), -1)

            # Reps counter
            cv2.putText(image, 'SQUATS', (15, 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(image, str(squat_counter), (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2, cv2.LINE_AA)

            # Stage display
            cv2.putText(image, 'STAGE', (160, 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(image, squat_stage if squat_stage else "N/A", (150, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2, cv2.LINE_AA)

            # Draw landmarks and connections
            # Define drawing specs for custom colors
            landmark_drawing_spec = mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2)
            connection_drawing_spec = mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2)

            mp_drawing.draw_landmarks(
                image,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec,
                connection_drawing_spec
            )

            cv2.imshow('Squat Tracker', image)

            key = cv2.waitKey(10) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):  # Reset counter
                squat_counter = 0
                squat_stage = None
                print("Counter reset!")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    print("🏋️ Standalone Squat Counter")
    print("📱 Based on your provided script")
    print("🎯 Press 'q' to quit, 'r' to reset counter")
    print("🦵 Perform squats in front of the camera!")
    print()
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Squat counter stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
