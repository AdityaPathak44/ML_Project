"""
Debug script to test Push-up angle computation
"""
import cv2
from pose_detector import PoseDetector
from angle_utils import calculate_angle

def main():
    print("🔍 Push-up Angle Debug Test")
    print("=" * 40)
    
    detector = PoseDetector(model_complexity=1, min_detection_confidence=0.5, min_tracking_confidence=0.5)
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
            
            frame_count += 1
            if frame_count % 30 == 0:  # Print debug every 30 frames
                if lms is not None:
                    print(f"\n📊 Frame {frame_count}: Detected landmarks")
                    print(f"Available landmarks: {list(lms.keys())}")
                    
                    # Test push-up angle computation
                    for side_prefix in ["RIGHT_", "LEFT_"]:
                        shoulder_key = side_prefix + "SHOULDER"
                        elbow_key = side_prefix + "ELBOW"
                        wrist_key = side_prefix + "WRIST"
                        hip_key = side_prefix + "HIP"
                        knee_key = side_prefix + "KNEE"
                        
                        required_keys = [shoulder_key, elbow_key, wrist_key, hip_key]
                        available_keys = [key for key in required_keys if key in lms]
                        
                        print(f"\n{side_prefix} side:")
                        print(f"  Required: {required_keys}")
                        print(f"  Available: {available_keys}")
                        print(f"  Missing: {[key for key in required_keys if key not in lms]}")
                        
                        if all(key in lms for key in required_keys):
                            shoulder = lms[shoulder_key]
                            elbow = lms[elbow_key]
                            wrist = lms[wrist_key]
                            hip = lms[hip_key]
                            
                            elbow_angle = calculate_angle((shoulder.x, shoulder.y), (elbow.x, elbow.y), (wrist.x, wrist.y))
                            shoulder_angle = calculate_angle((hip.x, hip.y), (shoulder.x, shoulder.y), (elbow.x, elbow.y))
                            
                            print(f"  ✅ Elbow angle: {elbow_angle:.1f}°")
                            print(f"  ✅ Shoulder angle: {shoulder_angle:.1f}°")
                            
                            if knee_key in lms:
                                knee = lms[knee_key]
                                back_angle = calculate_angle((shoulder.x, shoulder.y), (hip.x, hip.y), (knee.x, knee.y))
                                print(f"  ✅ Back angle: {back_angle:.1f}°")
                            else:
                                print(f"  ❌ Knee not detected for back angle")
                            break
                        else:
                            print(f"  ❌ Missing landmarks for angle computation")
                else:
                    print(f"\n📊 Frame {frame_count}: No landmarks detected")
            
            # Display frame
            detector.draw(frame, results)
            cv2.putText(frame, "Push-up Angle Debug - Press 'q' to quit", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow("Push-up Debug", frame)
            
            key = cv2.waitKey(30) & 0xFF
            if key == ord('q'):
                break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
