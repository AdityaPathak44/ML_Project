"""
Test Reference Builder

Simple test script to demonstrate how the trainer reference builder works.
This version can work with webcam input for testing purposes.

Usage:
    python test_reference_builder.py

Instructions:
    1. Run the script
    2. Perform 5-10 bicep curls in front of the webcam
    3. Press 'q' to stop recording and analyze the data
    4. The script will generate reference ranges and show visualization
"""

import cv2
import json
import numpy as np
from typing import List, Tuple, Dict
import matplotlib.pyplot as plt

from pose_detector import PoseDetector
from angle_utils import calculate_angle


class SimpleReferenceBuilder:
    def __init__(self):
        """Initialize the simple reference builder."""
        self.detector = PoseDetector(
            model_complexity=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.angles = []
        self.frame_count = 0
        
    def collect_angles_from_webcam(self) -> bool:
        """Collect elbow angles from webcam input.
        
        Returns:
            True if successful, False otherwise
        """
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open webcam")
            return False
            
        print("=== Webcam Reference Collection ===")
        print("Instructions:")
        print("1. Position yourself so your left arm is visible")
        print("2. Perform 5-10 slow, controlled bicep curls")
        print("3. Press 'q' when finished")
        print("4. Make sure to extend your arm fully (down) and flex completely (up)")
        print("\nPress any key to start...")
        
        cv2.namedWindow("Reference Collection", cv2.WINDOW_AUTOSIZE)
        
        # Wait for user to be ready
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            cv2.putText(frame, "Press any key to start collecting data", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, "Then perform bicep curls and press 'q' when done", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow("Reference Collection", frame)
            key = cv2.waitKey(1) & 0xFF
            if key != 255:  # Any key pressed
                break
                
        # Start collecting data
        print("\n🔴 Recording... Perform your bicep curls now!")
        collecting = True
        
        while collecting:
            ret, frame = cap.read()
            if not ret:
                break
                
            frame = cv2.flip(frame, 1)  # Mirror the image
            self.frame_count += 1
            
            # Process frame
            results = self.detector.process(frame)
            landmarks = self.detector.get_landmarks(frame, results)
            
            # Draw pose
            self.detector.draw(frame, results)
            
            angle = None
            if landmarks and self._has_required_landmarks(landmarks):
                # Calculate and display angle
                angle = self._calculate_elbow_angle(landmarks)
                if not np.isnan(angle):
                    self.angles.append(angle)
                    
                    # Draw angle on screen
                    elbow = landmarks["LEFT_ELBOW"]
                    cv2.putText(frame, f"Angle: {angle:.1f}°", 
                               (int(elbow.x) + 20, int(elbow.y) - 20),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                    
                    # Draw landmarks
                    for lm_name in ["LEFT_SHOULDER", "LEFT_ELBOW", "LEFT_WRIST"]:
                        if lm_name in landmarks:
                            lm = landmarks[lm_name]
                            cv2.circle(frame, (int(lm.x), int(lm.y)), 8, (0, 255, 0), -1)
                            
            # Status display
            status_color = (0, 255, 0) if angle and not np.isnan(angle) else (0, 0, 255)
            cv2.putText(frame, f"🔴 RECORDING - Samples: {len(self.angles)}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
            cv2.putText(frame, "Perform bicep curls slowly and controlled", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, "Press 'q' when done (min 50 samples recommended)", 
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                       
            cv2.imshow("Reference Collection", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                collecting = False
                
        cap.release()
        cv2.destroyAllWindows()
        
        print(f"\n✅ Collection complete! Gathered {len(self.angles)} angle samples")
        return len(self.angles) >= 20  # Minimum samples needed
        
    def _has_required_landmarks(self, landmarks: Dict) -> bool:
        """Check if required landmarks are present."""
        required = ["LEFT_SHOULDER", "LEFT_ELBOW", "LEFT_WRIST"]
        return all(lm in landmarks for lm in required)
        
    def _calculate_elbow_angle(self, landmarks: Dict) -> float:
        """Calculate elbow angle from landmarks."""
        try:
            shoulder = landmarks["LEFT_SHOULDER"]
            elbow = landmarks["LEFT_ELBOW"]
            wrist = landmarks["LEFT_WRIST"]
            
            return calculate_angle(
                (shoulder.x, shoulder.y),
                (elbow.x, elbow.y),
                (wrist.x, wrist.y)
            )
        except:
            return float('nan')
            
    def simple_segmentation(self) -> List[Tuple[int, int]]:
        """Simple peak-valley detection for repetitions."""
        if len(self.angles) < 20:
            return []
            
        angles_array = np.array(self.angles)
        
        # Simple smoothing
        window_size = 5
        smoothed = np.convolve(angles_array, np.ones(window_size)/window_size, mode='valid')
        
        # Find local maxima and minima
        peaks = []
        valleys = []
        
        for i in range(2, len(smoothed) - 2):
            # Local maximum
            if (smoothed[i] > smoothed[i-1] and smoothed[i] > smoothed[i+1] and
                smoothed[i] > smoothed[i-2] and smoothed[i] > smoothed[i+2]):
                peaks.append(i)
                
            # Local minimum  
            elif (smoothed[i] < smoothed[i-1] and smoothed[i] < smoothed[i+1] and
                  smoothed[i] < smoothed[i-2] and smoothed[i] < smoothed[i+2]):
                valleys.append(i)
                
        print(f"Detected {len(peaks)} peaks and {len(valleys)} valleys")
        
        # Create repetitions from alternating peaks and valleys
        repetitions = []
        all_extrema = sorted([(p, 'peak') for p in peaks] + [(v, 'valley') for v in valleys])
        
        for i in range(len(all_extrema) - 1):
            start_idx, start_type = all_extrema[i]
            end_idx, end_type = all_extrema[i + 1]
            
            # Only count as repetition if it covers significant range
            if abs(end_idx - start_idx) > 10:
                repetitions.append((start_idx, end_idx))
                
        return repetitions[:10]  # Limit to first 10 reps
        
    def analyze_and_save(self):
        """Analyze collected data and save references."""
        if len(self.angles) < 20:
            print("❌ Not enough data collected. Need at least 20 samples.")
            return False
            
        print(f"\n=== Analysis ===")
        
        # Basic statistics
        min_angle = np.min(self.angles)
        max_angle = np.max(self.angles)
        mean_angle = np.mean(self.angles)
        std_angle = np.std(self.angles)
        
        print(f"Angle Statistics:")
        print(f"  Min: {min_angle:.1f}° (most flexed)")
        print(f"  Max: {max_angle:.1f}° (most extended)")  
        print(f"  Mean: {mean_angle:.1f}°")
        print(f"  Std Dev: {std_angle:.1f}°")
        
        # Try simple segmentation
        repetitions = self.simple_segmentation()
        print(f"Detected {len(repetitions)} repetitions")
        
        # Calculate reference ranges with tolerance
        tolerance = 10.0  # More generous tolerance for webcam data
        final_min = max(0, min_angle - tolerance)
        final_max = min(180, max_angle + tolerance)
        
        print(f"\nFinal Reference Ranges:")
        print(f"  Flexed (Up): {final_min:.1f}° - {mean_angle - std_angle:.1f}°")
        print(f"  Extended (Down): {mean_angle + std_angle:.1f}° - {final_max:.1f}°")
        
        # Create reference structure
        references = {
            "BicepCurl": {
                "Elbow": {
                    "Min": round(final_min, 1),
                    "Max": round(final_max, 1)
                }
            }
        }
        
        # Save to file
        try:
            with open("webcam_references.json", 'w') as f:
                json.dump(references, f, indent=2)
            print(f"\n💾 References saved to webcam_references.json")
        except Exception as e:
            print(f"❌ Error saving references: {e}")
            
        # Create visualization
        self._create_visualization(repetitions)
        
        return True
        
    def _create_visualization(self, repetitions: List[Tuple[int, int]]):
        """Create simple visualization."""
        try:
            plt.figure(figsize=(12, 8))
            
            # Plot angle sequence
            plt.subplot(2, 1, 1)
            plt.plot(self.angles, 'b-', alpha=0.7, linewidth=2, label='Elbow Angles')
            
            # Mark repetitions
            for i, (start_idx, end_idx) in enumerate(repetitions[:5]):
                plt.axvspan(start_idx, end_idx, alpha=0.3, color=f'C{i}', 
                           label=f'Rep {i+1}')
                           
            plt.xlabel('Sample Number')
            plt.ylabel('Elbow Angle (degrees)')
            plt.title('Collected Elbow Angle Data')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Plot histogram
            plt.subplot(2, 1, 2)
            plt.hist(self.angles, bins=25, alpha=0.7, color='green', edgecolor='black')
            plt.axvline(np.min(self.angles), color='red', linestyle='--', label=f'Min: {np.min(self.angles):.1f}°')
            plt.axvline(np.max(self.angles), color='red', linestyle='--', label=f'Max: {np.max(self.angles):.1f}°')
            plt.axvline(np.mean(self.angles), color='orange', linestyle='-', label=f'Mean: {np.mean(self.angles):.1f}°')
            
            plt.xlabel('Elbow Angle (degrees)')
            plt.ylabel('Frequency')
            plt.title('Angle Distribution')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig("webcam_analysis.png", dpi=150, bbox_inches='tight')
            print(f"📊 Visualization saved as webcam_analysis.png")
            
            plt.show()
            
        except Exception as e:
            print(f"⚠️ Could not create visualization: {e}")


def main():
    """Main function for the test reference builder."""
    print("=== Webcam Reference Builder Test ===")
    
    builder = SimpleReferenceBuilder()
    
    # Collect data from webcam
    if builder.collect_angles_from_webcam():
        # Analyze and save
        builder.analyze_and_save()
        print("\n✅ Test completed successfully!")
        print("Check webcam_references.json for the generated reference data.")
    else:
        print("\n❌ Data collection failed or insufficient data.")
        print("Make sure your webcam is working and you performed enough repetitions.")


if __name__ == "__main__":
    main()
