import cv2
import mediapipe as mp
import numpy as np

# Initialize MediaPipe drawing utilities and pose model
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# Function to calculate angle between three points
def calculate_angle(a, b, c):
    """
    Calculates the angle (in degrees) between three points a, b, and c,
    where b is the vertex of the angle.
    """
    a = np.array(a)  # First point (e.g., shoulder)
    b = np.array(b)  # Mid point/Vertex (e.g., elbow)
    c = np.array(c)  # End point (e.g., wrist)

    # Calculate vectors
    ba = a - b
    bc = c - b

    # Calculate cosine of angle using dot product
    # Handles potential divide by zero or floating point issues
    norm_product = np.linalg.norm(ba) * np.linalg.norm(bc)
    if norm_product == 0:
        return 0
        
    cosine_angle = np.dot(ba, bc) / norm_product
    
    # Clip value to ensure it's within the valid range [-1, 1] for arccos
    cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
    
    angle = np.degrees(np.arccos(cosine_angle))

    # Optional: ensure angle is between 0 and 180 degrees
    # if angle > 180.0:
    #     angle = 360 - angle

    return angle

# --- Main Pushup Tracker Logic ---
# Note: For pushups, positioning the camera to the side or slightly above and to the side works best.
cap = cv2.VideoCapture(0)

# Pushup counter variables
pushup_counter = 0
pushup_stage = None # "up" (arms straight) or "down" (chest near floor)

with mp_pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6) as pose:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        # Recolor image to RGB for MediaPipe
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writable = False

        # Make detection
        results = pose.process(image)

        # Recolor back to BGR for OpenCV
        image.flags.writable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Get frame dimensions for calculating pixel coordinates
        frame_height, frame_width, _ = frame.shape
        elbow_angle = 0 # Initialize angle

        try:
            landmarks = results.pose_landmarks.landmark

            # 1. Get coordinates for the right elbow angle (Shoulder-Elbow-Wrist)
            # Choose the Right side (or Left, but be consistent)
            shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                        landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
            elbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,
                     landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
            wrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,
                     landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]

            # Calculate the angle at the elbow joint
            elbow_angle = calculate_angle(shoulder, elbow, wrist)

            # --- Pushup counter logic ---
            # Angle thresholds for pushups:
            # - UP position (arms straight): Angle should be close to 180 degrees.
            # - DOWN position (chest near floor): Angle should be small, typically < 90 degrees.

            if elbow_angle > 170: # Arms straight/locked out
                pushup_stage = "up"
            if elbow_angle < 100 and pushup_stage == 'up': # Elbow bent, coming from 'up' stage
                pushup_stage = "down"
                pushup_counter += 1

            # --- Visualizations ---
            # Display the calculated angle near the elbow
            elbow_pixel_coords = tuple(np.multiply(elbow, [frame_width, frame_height]).astype(int))
            cv2.putText(image, f"Elbow Angle: {int(elbow_angle)}",
                        (elbow_pixel_coords[0] + 10, elbow_pixel_coords[1] + 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)

        except:
            # Handle cases where landmarks are not fully detected (e.g., person is off-screen)
            pass

        # --- Render Counter and Stage ---
        # Setup status box
        cv2.rectangle(image, (0, 0), (280, 73), (138, 50, 222), -1) # Using a purple color

        # Reps counter
        cv2.putText(image, 'PUSHUPS', (15, 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(image, str(pushup_counter), (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2, cv2.LINE_AA)

        # Stage display
        cv2.putText(image, 'STAGE', (160, 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(image, pushup_stage if pushup_stage else "N/A", (150, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2, cv2.LINE_AA)


        # Draw landmarks and connections
        landmark_drawing_spec = mp_drawing.DrawingSpec(color=(255, 0, 255), thickness=2, circle_radius=2)
        connection_drawing_spec = mp_drawing.DrawingSpec(color=(128, 0, 128), thickness=2, circle_radius=2)

        mp_drawing.draw_landmarks(
            image,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec,
            connection_drawing_spec
        )

        cv2.imshow('Pushup Tracker', image)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
