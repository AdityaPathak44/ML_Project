"""
Trainer Reference Builder

This script analyzes trainer videos to extract reference angle ranges for exercises.
It processes a trainer video, detects pose landmarks, calculates elbow angles,
segments the video into repetitions, and builds reference JSON data.

Usage:
    python trainer_reference_builder.py

Requirements:
    - trainer_videos/bicep_curl.mp4 should exist in the project directory
    - Existing pose_detector.py, angle_utils.py modules
"""

import cv2
import json
import numpy as np
from typing import List, Tuple, Dict, Optional
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import os

from pose_detector import PoseDetector
from angle_utils import calculate_angle


class TrainerReferenceBuilder:
    def __init__(self, video_path: str):
        """Initialize the trainer reference builder.
        
        Args:
            video_path: Path to the trainer video file
        """
        self.video_path = video_path
        self.detector = PoseDetector(
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.angles = []
        self.frame_numbers = []
        
    def extract_angles_from_video(self) -> bool:
        """Extract elbow angles from the trainer video.
        
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(self.video_path):
            print(f"Error: Video file not found at {self.video_path}")
            return False
            
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video file {self.video_path}")
            return False
            
        print(f"Processing video: {self.video_path}")
        frame_count = 0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            if frame_count % 10 == 0:  # Progress indicator
                print(f"Processing frame {frame_count}/{total_frames} ({frame_count/total_frames*100:.1f}%)")
                
            # Process frame with pose detector
            results = self.detector.process(frame)
            landmarks = self.detector.get_landmarks(frame, results)
            
            if landmarks and self._has_required_landmarks(landmarks):
                # Calculate elbow angle
                angle = self._calculate_elbow_angle(landmarks)
                if not np.isnan(angle):
                    self.angles.append(angle)
                    self.frame_numbers.append(frame_count)
                    
        cap.release()
        print(f"Extracted {len(self.angles)} valid angle measurements from {total_frames} frames")
        return len(self.angles) > 0
        
    def _has_required_landmarks(self, landmarks: Dict) -> bool:
        """Check if all required landmarks for elbow angle calculation are present.
        
        Args:
            landmarks: Dictionary of detected landmarks
            
        Returns:
            True if all required landmarks are present
        """
        # Try left side first, then right side
        left_required = ["LEFT_SHOULDER", "LEFT_ELBOW", "LEFT_WRIST"]
        right_required = ["RIGHT_SHOULDER", "RIGHT_ELBOW", "RIGHT_WRIST"]
        
        return (all(lm in landmarks for lm in left_required) or 
                all(lm in landmarks for lm in right_required))
        
    def _calculate_elbow_angle(self, landmarks: Dict) -> float:
        """Calculate elbow angle from landmarks.
        
        Args:
            landmarks: Dictionary of detected landmarks
            
        Returns:
            Elbow angle in degrees, or NaN if calculation fails
        """
        # Try left side first, then right side
        for prefix in ["LEFT_", "RIGHT_"]:
            try:
                shoulder_key = f"{prefix}SHOULDER"
                elbow_key = f"{prefix}ELBOW"
                wrist_key = f"{prefix}WRIST"
                
                if all(key in landmarks for key in [shoulder_key, elbow_key, wrist_key]):
                    shoulder = landmarks[shoulder_key]
                    elbow = landmarks[elbow_key]
                    wrist = landmarks[wrist_key]
                    
                    # Try with visibility check first
                    try:
                        if (hasattr(shoulder, 'visibility') and shoulder.visibility > 0.3 and
                            hasattr(elbow, 'visibility') and elbow.visibility > 0.3 and
                            hasattr(wrist, 'visibility') and wrist.visibility > 0.3):
                            
                            return calculate_angle(
                                (shoulder.x, shoulder.y),
                                (elbow.x, elbow.y),
                                (wrist.x, wrist.y)
                            )
                    except:
                        # Fallback: calculate without visibility check
                        return calculate_angle(
                            (shoulder.x, shoulder.y),
                            (elbow.x, elbow.y),
                            (wrist.x, wrist.y)
                        )
            except Exception as e:
                continue
                
        return float('nan')
            
    def segment_repetitions(self) -> List[Tuple[int, int]]:
        """Segment the angle sequence into individual repetitions.
        
        Uses peak detection to find repetition boundaries:
        - Peaks (high angles) = arm extended position
        - Valleys (low angles) = arm flexed position
        
        Returns:
            List of (start_idx, end_idx) tuples for each repetition
        """
        if len(self.angles) < 10:
            print("Warning: Not enough angle data for segmentation")
            return []
            
        angles_array = np.array(self.angles)
        
        # Smooth the signal to reduce noise
        from scipy.ndimage import gaussian_filter1d
        smoothed_angles = gaussian_filter1d(angles_array, sigma=2.0)
        
        # Find peaks (extended arm positions) - high angles
        # Use prominence to avoid detecting small fluctuations
        min_prominence = (np.max(smoothed_angles) - np.min(smoothed_angles)) * 0.3
        peaks, peak_properties = find_peaks(
            smoothed_angles,
            prominence=min_prominence,
            distance=20  # Minimum distance between peaks (frames)
        )
        
        # Find valleys (flexed arm positions) - low angles
        inverted_angles = -smoothed_angles
        valleys, valley_properties = find_peaks(
            inverted_angles,
            prominence=min_prominence,
            distance=20
        )
        
        print(f"Detected {len(peaks)} peaks and {len(valleys)} valleys")
        print(f"Angle range: {np.min(angles_array):.1f}° to {np.max(angles_array):.1f}°")
        
        if len(peaks) < 2 or len(valleys) < 2:
            print("Warning: Not enough peaks/valleys detected for full repetition segmentation")
            print("Using simple approach with available data...")
            
            # If we have at least one peak and one valley, create a single repetition
            if len(peaks) >= 1 and len(valleys) >= 1:
                # Find the range that covers the main movement
                all_extremes = sorted(list(peaks) + list(valleys))
                if len(all_extremes) >= 2:
                    return [(all_extremes[0], all_extremes[-1])]
            
            # Last resort: use the full sequence as one repetition
            print("Using entire sequence as single repetition")
            return [(0, len(angles_array) - 1)]
            
        # Create repetitions by pairing consecutive peaks with valleys
        repetitions = []
        
        for i in range(len(peaks) - 1):
            start_peak = peaks[i]
            end_peak = peaks[i + 1]
            
            # Find valley between these two peaks
            valleys_between = valleys[(valleys > start_peak) & (valleys < end_peak)]
            
            if len(valleys_between) > 0:
                # Use the deepest valley between the peaks
                valley_idx = valleys_between[np.argmin(smoothed_angles[valleys_between])]
                
                # Repetition goes from first peak to second peak
                repetitions.append((start_peak, end_peak))
                
        print(f"Segmented into {len(repetitions)} repetitions")
        return repetitions
        
    def calculate_reference_ranges(self, repetitions: List[Tuple[int, int]]) -> Dict:
        """Calculate reference angle ranges from segmented repetitions.
        
        Args:
            repetitions: List of (start_idx, end_idx) tuples for each repetition
            
        Returns:
            Dictionary with reference ranges
        """
        if not repetitions:
            print("Error: No repetitions to analyze")
            return {}
            
        all_mins = []
        all_maxs = []
        
        print("\nAnalyzing repetitions:")
        for i, (start_idx, end_idx) in enumerate(repetitions):
            rep_angles = self.angles[start_idx:end_idx + 1]
            rep_min = np.min(rep_angles)
            rep_max = np.max(rep_angles)
            
            all_mins.append(rep_min)
            all_maxs.append(rep_max)
            
            print(f"Rep {i+1}: Min={rep_min:.1f}°, Max={rep_max:.1f}°, Range={rep_max-rep_min:.1f}°")
            
        # Calculate overall ranges with some tolerance
        overall_min = np.min(all_mins)
        overall_max = np.max(all_maxs)
        
        # Add small tolerance margins (5 degrees) to account for natural variation
        tolerance = 5.0
        final_min = max(0, overall_min - tolerance)
        final_max = min(180, overall_max + tolerance)
        
        print(f"\nFinal reference ranges:")
        print(f"Minimum angle: {final_min:.1f}° (flexed arm)")
        print(f"Maximum angle: {final_max:.1f}° (extended arm)")
        print(f"Total range: {final_max - final_min:.1f}°")
        
        return {
            "BicepCurl": {
                "Elbow": {
                    "Min": round(final_min, 1),
                    "Max": round(final_max, 1)
                }
            }
        }
        
    def visualize_analysis(self, repetitions: List[Tuple[int, int]], save_plot: bool = True):
        """Create visualization of the angle analysis.
        
        Args:
            repetitions: List of repetition segments
            save_plot: Whether to save the plot as an image
        """
        if not self.angles:
            print("No angle data to visualize")
            return
            
        plt.figure(figsize=(12, 6))
        
        # Plot angle sequence
        plt.subplot(2, 1, 1)
        plt.plot(self.frame_numbers, self.angles, 'b-', alpha=0.7, label='Elbow Angles')
        
        # Mark repetition boundaries
        for i, (start_idx, end_idx) in enumerate(repetitions):
            start_frame = self.frame_numbers[start_idx]
            end_frame = self.frame_numbers[end_idx]
            plt.axvspan(start_frame, end_frame, alpha=0.2, color=f'C{i%10}', 
                       label=f'Rep {i+1}' if i < 5 else None)
                       
        plt.xlabel('Frame Number')
        plt.ylabel('Elbow Angle (degrees)')
        plt.title('Elbow Angle Sequence with Repetition Segmentation')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Plot angle distribution
        plt.subplot(2, 1, 2)
        plt.hist(self.angles, bins=30, alpha=0.7, color='green', edgecolor='black')
        plt.xlabel('Elbow Angle (degrees)')
        plt.ylabel('Frequency')
        plt.title('Distribution of Elbow Angles')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_plot:
            plot_path = "trainer_analysis_visualization.png"
            plt.savefig(plot_path, dpi=150, bbox_inches='tight')
            print(f"Visualization saved as {plot_path}")
            
        plt.show()
        
    def save_references(self, references: Dict, output_path: str = "references.json"):
        """Save reference data to JSON file.
        
        Args:
            references: Reference data dictionary
            output_path: Path to save the JSON file
        """
        try:
            # Load existing references if they exist
            existing_references = {}
            if os.path.exists(output_path):
                with open(output_path, 'r') as f:
                    existing_references = json.load(f)
                    
            # Merge with new references
            existing_references.update(references)
            
            # Save updated references
            with open(output_path, 'w') as f:
                json.dump(existing_references, f, indent=2)
                
            print(f"References saved to {output_path}")
            print(f"Updated JSON content:")
            print(json.dumps(existing_references, indent=2))
            
        except Exception as e:
            print(f"Error saving references: {e}")
            
    def build_references(self, visualize: bool = True) -> bool:
        """Complete pipeline to build reference data from trainer video.
        
        Args:
            visualize: Whether to create visualization plots
            
        Returns:
            True if successful, False otherwise
        """
        print("=== Trainer Reference Builder ===")
        
        # Step 1: Extract angles from video
        if not self.extract_angles_from_video():
            return False
            
        # Step 2: Segment into repetitions
        repetitions = self.segment_repetitions()
        if not repetitions:
            return False
            
        # Step 3: Calculate reference ranges
        references = self.calculate_reference_ranges(repetitions)
        if not references:
            return False
            
        # Step 4: Visualize (optional)
        if visualize:
            try:
                self.visualize_analysis(repetitions)
            except Exception as e:
                print(f"Warning: Could not create visualization: {e}")
                
        # Step 5: Save references
        self.save_references(references)
        
        return True


def main():
    """Main function to run the trainer reference builder."""
    # Configuration
    video_path = "Trainer_videos/Biceps_curl.mp4"
    
    # Check if video exists
    if not os.path.exists("Trainer_videos"):
        os.makedirs("Trainer_videos")
        print(f"Created Trainer_videos directory. Please place Biceps_curl.mp4 in this folder.")
        return
        
    if not os.path.exists(video_path):
        print(f"Error: Trainer video not found at {video_path}")
        print("Please ensure the trainer video file exists.")
        return
        
    # Build references
    builder = TrainerReferenceBuilder(video_path)
    success = builder.build_references(visualize=True)
    
    if success:
        print("\n✅ Reference building completed successfully!")
        print("The references.json file has been updated with bicep curl reference ranges.")
    else:
        print("\n❌ Reference building failed. Please check the video file and try again.")


if __name__ == "__main__":
    main()
