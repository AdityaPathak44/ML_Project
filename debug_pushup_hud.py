"""
Debug script to test Push-up HUD angle display
"""
import cv2
from typing import Dict
from pose_detector import PoseDetector
from angle_utils import calculate_angle
from feedback import FeedbackEngine

def main():
    print("🔍 Push-up HUD Debug Test")
    print("=" * 40)
    
    detector = PoseDetector(model_complexity=1, min_detection_confidence=0.5, min_tracking_confidence=0.5)
    engine = FeedbackEngine()
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Could not open webcam.")
        return
    
    frame_count = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            
            results = detector.process(frame)
            lms = detector.get_landmarks(frame, results)
            angles: Dict[str, float] = {}
            
            frame_count += 1
            if frame_count % 30 == 0 and lms is not None:  # Debug every 30 frames
                print(f"\n📊 Frame {frame_count}: Testing Push-up angle computation")
                
                # Test the exact same logic as main.py for Push-up
                for side_prefix in ["LEFT_", "RIGHT_"]:
                    shoulder_key = side_prefix + "SHOULDER"
                    elbow_key = side_prefix + "ELBOW"
                    wrist_key = side_prefix + "WRIST"
                    if lms and shoulder_key in lms and elbow_key in lms and wrist_key in lms:
                        shoulder = lms[shoulder_key]
                        elbow = lms[elbow_key]
                        wrist = lms[wrist_key]
                        elbow_angle = calculate_angle((shoulder.x, shoulder.y), (elbow.x, elbow.y), (wrist.x, wrist.y))
                        angles["Elbow"] = elbow_angle
                        print(f"✅ {side_prefix} Elbow angle: {elbow_angle:.1f}° → angles['Elbow'] = {angles.get('Elbow', 'NOT SET')}")
                        
                        # Try to add shoulder and back angles if hip/knee available
                        hip_key = side_prefix + "HIP"
                        knee_key = side_prefix + "KNEE"
                        if lms and hip_key in lms:
                            hip = lms[hip_key]
                            shoulder_angle = calculate_angle((hip.x, hip.y), (shoulder.x, shoulder.y), (elbow.x, elbow.y))
                            angles["Shoulder"] = shoulder_angle
                            print(f"✅ {side_prefix} Shoulder angle: {shoulder_angle:.1f}° → angles['Shoulder'] = {angles.get('Shoulder', 'NOT SET')}")
                            
                            if lms and knee_key in lms:
                                knee = lms[knee_key]
                                back_angle = calculate_angle((shoulder.x, shoulder.y), (hip.x, hip.y), (knee.x, knee.y))
                                angles["Back"] = back_angle
                                print(f"✅ {side_prefix} Back angle: {back_angle:.1f}° → angles['Back'] = {angles.get('Back', 'NOT SET')}")
                        break
                
                # Also compute other standard angles for consistency
                try:
                    standard_angles = engine.compute_all_angles(lms)
                    print(f"📐 Standard angles computed: {list(standard_angles.keys())}")
                    angles.update({k: v for k, v in standard_angles.items() if k not in angles})
                    print(f"📋 Final angles dict keys: {list(angles.keys())}")
                except Exception as e:
                    print(f"❌ Standard angle computation failed: {e}")
                
                # Test HUD angle display logic
                exercise = "Push-up"
                angle_keys = ["Elbow", "Shoulder", "Back"]
                print(f"\n🖥️ HUD Display Test for {exercise}:")
                print(f"Looking for angle keys: {angle_keys}")
                
                for k in angle_keys:
                    ang = angles.get(k, float('nan'))
                    if ang == ang:  # Not NaN
                        print(f"  {k}: {ang:.1f}° ✅")
                    else:
                        print(f"  {k}: Not detected ❌")
            
            # Display frame
            detector.draw(frame, results)
            cv2.putText(frame, "Push-up HUD Debug - Press 'q' to quit", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow("Push-up HUD Debug", frame)
            
            key = cv2.waitKey(30) & 0xFF
            if key == ord('q'):
                break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
