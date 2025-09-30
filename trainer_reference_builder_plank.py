"""
Plank Trainer Reference Builder

This script analyzes trainer images/videos to extract reference angle ranges for plank exercises.
It processes trainer media, detects pose landmarks, calculates hip angles (shoulder-hip-ankle),
and builds reference JSON data for proper plank position detection.

Usage:
    python trainer_reference_builder_plank.py

Requirements:
    - Trainer_Videos/Plank.jpg (or .mp4) should exist in the project directory
    - Existing pose_detector.py, angle_utils.py modules
"""

import cv2
import json
import numpy as np
from typing import List, Tuple, Dict, Optional
import matplotlib.pyplot as plt
import os

from pose_detector import PoseDetector
from angle_utils import calculate_angle


class PlankTrainerReferenceBuilder:
    def __init__(self, media_path: str):
        """Initialize the plank trainer reference builder.
        
        Args:
            media_path: Path to the trainer image or video file
        """
        self.media_path = media_path
        self.detector = PoseDetector(
            model_complexity=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.left_hip_angles = []
        self.right_hip_angles = []
        self.frame_numbers = []
        self.is_video = media_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))
        
    def extract_angles_from_media(self) -> bool:
        """Extract hip angles from the trainer image or video.
        
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(self.media_path):
            print(f"Error: Media file not found at {self.media_path}")
            return False
            
        if self.is_video:
            return self._extract_from_video()
        else:
            return self._extract_from_image()
    
    def _extract_from_image(self) -> bool:
        """Extract angles from a single plank image."""
        print(f"Processing plank image: {self.media_path}")
        
        # Load and process the image
        frame = cv2.imread(self.media_path)
        if frame is None:
            print(f"Error: Could not load image {self.media_path}")
            return False
            
        # Process frame with pose detector
        results = self.detector.process(frame)
        landmarks = self.detector.get_landmarks(frame, results)
        
        if landmarks and self._has_required_landmarks(landmarks):
            left_angle, right_angle = self._calculate_hip_angles(landmarks)
            
            if not np.isnan(left_angle):
                self.left_hip_angles.append(left_angle)
                print(f"Left hip angle: {left_angle:.1f}°")
            
            if not np.isnan(right_angle):
                self.right_hip_angles.append(right_angle)
                print(f"Right hip angle: {right_angle:.1f}°")
            
            self.frame_numbers.append(1)
            
            # Save annotated image for verification
            self._save_annotated_image(frame, results, landmarks)
            
            return len(self.left_hip_angles) > 0 or len(self.right_hip_angles) > 0
        else:
            print("Error: Could not detect proper plank pose in the image")
            return False
    
    def _extract_from_video(self) -> bool:
        """Extract angles from a plank video."""
        cap = cv2.VideoCapture(self.media_path)
        if not cap.isOpened():
            print(f"Error: Could not open video file {self.media_path}")
            return False
            
        print(f"Processing plank video: {self.media_path}")
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
                left_angle, right_angle = self._calculate_hip_angles(landmarks)
                
                if not np.isnan(left_angle):
                    self.left_hip_angles.append(left_angle)
                    
                if not np.isnan(right_angle):
                    self.right_hip_angles.append(right_angle)
                    
                self.frame_numbers.append(frame_count)
                    
        cap.release()
        print(f"Extracted {len(self.left_hip_angles)} left and {len(self.right_hip_angles)} right hip angle measurements")
        return len(self.left_hip_angles) > 0 or len(self.right_hip_angles) > 0
        
    def _has_required_landmarks(self, landmarks: Dict) -> bool:
        """Check if all required landmarks for hip angle calculation are present.
        
        Args:
            landmarks: Dictionary of detected landmarks
            
        Returns:
            True if all required landmarks are present for at least one side
        """
        # Check for left side landmarks
        left_required = ["LEFT_SHOULDER", "LEFT_HIP", "LEFT_ANKLE"]
        right_required = ["RIGHT_SHOULDER", "RIGHT_HIP", "RIGHT_ANKLE"]
        
        left_ok = all(lm in landmarks for lm in left_required)
        right_ok = all(lm in landmarks for lm in right_required)
        
        return left_ok or right_ok
        
    def _calculate_hip_angles(self, landmarks: Dict) -> Tuple[float, float]:
        """Calculate hip angles from landmarks for both sides.
        
        Args:
            landmarks: Dictionary of detected landmarks
            
        Returns:
            Tuple of (left_hip_angle, right_hip_angle) in degrees, or NaN if calculation fails
        """
        left_angle = float('nan')
        right_angle = float('nan')
        
        # Calculate left hip angle (shoulder-hip-ankle)
        try:
            if all(key in landmarks for key in ["LEFT_SHOULDER", "LEFT_HIP", "LEFT_ANKLE"]):
                shoulder = landmarks["LEFT_SHOULDER"]
                hip = landmarks["LEFT_HIP"]
                ankle = landmarks["LEFT_ANKLE"]
                
                # Check visibility if available
                if (hasattr(shoulder, 'visibility') and shoulder.visibility > 0.3 and
                    hasattr(hip, 'visibility') and hip.visibility > 0.3 and
                    hasattr(ankle, 'visibility') and ankle.visibility > 0.3):
                    
                    left_angle = calculate_angle(
                        (shoulder.x, shoulder.y),
                        (hip.x, hip.y),
                        (ankle.x, ankle.y)
                    )
        except Exception as e:
            print(f"Warning: Could not calculate left hip angle: {e}")
            
        # Calculate right hip angle (shoulder-hip-ankle)
        try:
            if all(key in landmarks for key in ["RIGHT_SHOULDER", "RIGHT_HIP", "RIGHT_ANKLE"]):
                shoulder = landmarks["RIGHT_SHOULDER"]
                hip = landmarks["RIGHT_HIP"]
                ankle = landmarks["RIGHT_ANKLE"]
                
                # Check visibility if available
                if (hasattr(shoulder, 'visibility') and shoulder.visibility > 0.3 and
                    hasattr(hip, 'visibility') and hip.visibility > 0.3 and
                    hasattr(ankle, 'visibility') and ankle.visibility > 0.3):
                    
                    right_angle = calculate_angle(
                        (shoulder.x, shoulder.y),
                        (hip.x, hip.y),
                        (ankle.x, ankle.y)
                    )
        except Exception as e:
            print(f"Warning: Could not calculate right hip angle: {e}")
            
        return left_angle, right_angle
    
    def _save_annotated_image(self, frame, results, landmarks):
        """Save an annotated image showing the detected pose and angles."""
        try:
            # Draw pose landmarks
            self.detector.draw(frame, results)
            
            # Add angle annotations
            if landmarks:
                height, width = frame.shape[:2]
                
                # Left side annotation
                if "LEFT_HIP" in landmarks and len(self.left_hip_angles) > 0:
                    hip = landmarks["LEFT_HIP"]
                    cv2.putText(frame, f"L: {self.left_hip_angles[-1]:.0f}°", 
                               (int(hip.x * width) - 30, int(hip.y * height) - 20),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Right side annotation
                if "RIGHT_HIP" in landmarks and len(self.right_hip_angles) > 0:
                    hip = landmarks["RIGHT_HIP"]
                    cv2.putText(frame, f"R: {self.right_hip_angles[-1]:.0f}°", 
                               (int(hip.x * width) + 20, int(hip.y * height) - 20),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # Save the annotated image
            output_path = "plank_analysis_annotated.jpg"
            cv2.imwrite(output_path, frame)
            print(f"Annotated image saved as {output_path}")
            
        except Exception as e:
            print(f"Warning: Could not save annotated image: {e}")
    
    def calculate_reference_ranges(self) -> Dict:
        """Calculate reference angle ranges for plank position.
        
        Returns:
            Dictionary with reference ranges
        """
        if not self.left_hip_angles and not self.right_hip_angles:
            print("Error: No angle data to analyze")
            return {}
            
        print("\nAnalyzing plank hip angles:")
        
        # Combine left and right angles for overall analysis
        all_angles = []
        if self.left_hip_angles:
            all_angles.extend(self.left_hip_angles)
            print(f"Left hip angles: {self.left_hip_angles}")
            print(f"Left range: {np.min(self.left_hip_angles):.1f}° to {np.max(self.left_hip_angles):.1f}°")
            
        if self.right_hip_angles:
            all_angles.extend(self.right_hip_angles)
            print(f"Right hip angles: {self.right_hip_angles}")
            print(f"Right range: {np.min(self.right_hip_angles):.1f}° to {np.max(self.right_hip_angles):.1f}°")
        
        if not all_angles:
            return {}
            
        # Calculate statistics
        mean_angle = np.mean(all_angles)
        std_angle = np.std(all_angles)
        min_angle = np.min(all_angles)
        max_angle = np.max(all_angles)
        
        print(f"\nOverall statistics:")
        print(f"Mean angle: {mean_angle:.1f}°")
        print(f"Standard deviation: {std_angle:.1f}°")
        print(f"Range: {min_angle:.1f}° to {max_angle:.1f}°")
        
        # Define acceptable range for plank position
        # Good plank should have hip angle close to straight line (165-185 degrees)
        # Use mean ± 1.5 standard deviations, but constrain to reasonable plank range
        tolerance = max(5.0, 1.5 * std_angle)  # At least 5 degrees tolerance
        
        range_min = max(160.0, mean_angle - tolerance)  # Don't go below 160°
        range_max = min(185.0, mean_angle + tolerance)  # Don't go above 185°
        
        # Ensure minimum range
        if range_max - range_min < 10.0:
            center = (range_min + range_max) / 2
            range_min = center - 5.0
            range_max = center + 5.0
        
        print(f"\nFinal plank reference ranges:")
        print(f"Hip angle range: {range_min:.1f}° to {range_max:.1f}°")
        print(f"Tolerance: ±{tolerance:.1f}°")
        
        return {
            "Plank": {
                "Hip": {
                    "Min": round(range_min, 1),
                    "Max": round(range_max, 1)
                },
                # Additional metadata for analysis
                "Analysis": {
                    "source_angles_count": len(all_angles),
                    "mean_angle": round(mean_angle, 1),
                    "std_deviation": round(std_angle, 1),
                    "source_file": os.path.basename(self.media_path)
                }
            }
        }
        
    def visualize_analysis(self, save_plot: bool = True):
        """Create visualization of the plank angle analysis.
        
        Args:
            save_plot: Whether to save the plot as an image
        """
        all_angles = []
        labels = []
        
        if self.left_hip_angles:
            all_angles.extend(self.left_hip_angles)
            labels.extend(['Left'] * len(self.left_hip_angles))
            
        if self.right_hip_angles:
            all_angles.extend(self.right_hip_angles)
            labels.extend(['Right'] * len(self.right_hip_angles))
            
        if not all_angles:
            print("No angle data to visualize")
            return
            
        plt.figure(figsize=(12, 8))
        
        # Plot 1: Angle sequence (if video)
        if self.is_video and len(self.frame_numbers) > 1:
            plt.subplot(2, 2, 1)
            if self.left_hip_angles:
                plt.plot(self.frame_numbers[:len(self.left_hip_angles)], self.left_hip_angles, 
                        'b-', alpha=0.7, label='Left Hip Angle', marker='o')
            if self.right_hip_angles:
                plt.plot(self.frame_numbers[:len(self.right_hip_angles)], self.right_hip_angles, 
                        'r-', alpha=0.7, label='Right Hip Angle', marker='s')
            plt.xlabel('Frame Number')
            plt.ylabel('Hip Angle (degrees)')
            plt.title('Hip Angle Sequence')
            plt.legend()
            plt.grid(True, alpha=0.3)
        
        # Plot 2: Angle distribution
        subplot_idx = 2 if self.is_video and len(self.frame_numbers) > 1 else 1
        plt.subplot(2, 2, subplot_idx)
        
        bins = np.linspace(min(all_angles) - 5, max(all_angles) + 5, 20)
        
        if self.left_hip_angles:
            plt.hist(self.left_hip_angles, bins=bins, alpha=0.6, color='blue', 
                    label=f'Left Hip (n={len(self.left_hip_angles)})', edgecolor='black')
        if self.right_hip_angles:
            plt.hist(self.right_hip_angles, bins=bins, alpha=0.6, color='red', 
                    label=f'Right Hip (n={len(self.right_hip_angles)})', edgecolor='black')
            
        plt.xlabel('Hip Angle (degrees)')
        plt.ylabel('Frequency')
        plt.title('Hip Angle Distribution')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Plot 3: Box plot comparison
        plt.subplot(2, 2, subplot_idx + 1)
        plot_data = []
        plot_labels = []
        
        if self.left_hip_angles:
            plot_data.append(self.left_hip_angles)
            plot_labels.append('Left Hip')
        if self.right_hip_angles:
            plot_data.append(self.right_hip_angles)
            plot_labels.append('Right Hip')
            
        plt.boxplot(plot_data, labels=plot_labels)
        plt.ylabel('Hip Angle (degrees)')
        plt.title('Angle Distribution Box Plot')
        plt.grid(True, alpha=0.3)
        
        # Plot 4: Statistics summary
        plt.subplot(2, 2, subplot_idx + 2)
        plt.axis('off')
        
        stats_text = f"""
Plank Analysis Summary:
Source: {os.path.basename(self.media_path)}
Type: {'Video' if self.is_video else 'Image'}

Left Hip Angles: {len(self.left_hip_angles)} measurements
Right Hip Angles: {len(self.right_hip_angles)} measurements

Combined Statistics:
Mean: {np.mean(all_angles):.1f}°
Std Dev: {np.std(all_angles):.1f}°
Range: {np.min(all_angles):.1f}° - {np.max(all_angles):.1f}°

Ideal Plank Range: 165° - 185°
"""
        plt.text(0.1, 0.9, stats_text, transform=plt.gca().transAxes, 
                fontsize=10, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.5))
        
        plt.tight_layout()
        
        if save_plot:
            plot_path = "plank_trainer_analysis.png"
            plt.savefig(plot_path, dpi=150, bbox_inches='tight')
            print(f"Analysis visualization saved as {plot_path}")
            
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
                    
            # Update plank references (merge with existing)
            if "Plank" in existing_references and "Plank" in references:
                existing_references["Plank"].update(references["Plank"])
            else:
                existing_references.update(references)
            
            # Save updated references
            with open(output_path, 'w') as f:
                json.dump(existing_references, f, indent=2)
                
            print(f"Plank references saved to {output_path}")
            print(f"Updated Plank section:")
            print(json.dumps(existing_references.get("Plank", {}), indent=2))
            
        except Exception as e:
            print(f"Error saving references: {e}")
            
    def build_references(self, visualize: bool = True) -> bool:
        """Complete pipeline to build plank reference data from trainer media.
        
        Args:
            visualize: Whether to create visualization plots
            
        Returns:
            True if successful, False otherwise
        """
        print("=== Plank Trainer Reference Builder ===")
        
        # Step 1: Extract angles from media
        if not self.extract_angles_from_media():
            return False
            
        # Step 2: Calculate reference ranges
        references = self.calculate_reference_ranges()
        if not references:
            return False
            
        # Step 3: Visualize (optional)
        if visualize:
            try:
                self.visualize_analysis()
            except Exception as e:
                print(f"Warning: Could not create visualization: {e}")
                
        # Step 4: Save references
        self.save_references(references)
        
        return True


def main():
    """Main function to run the plank trainer reference builder."""
    # Try different possible plank media files
    possible_files = [
        "Trainer_Videos/Plank.jpg",
        "Trainer_Videos/plank.jpg", 
        "Trainer_Videos/Plank.mp4",
        "Trainer_Videos/plank.mp4"
    ]
    
    media_path = None
    for file_path in possible_files:
        if os.path.exists(file_path):
            media_path = file_path
            break
    
    if not media_path:
        print("Error: No plank trainer media found. Looking for:")
        for file_path in possible_files:
            print(f"  - {file_path}")
        print("\nPlease ensure at least one plank trainer image (.jpg) or video (.mp4) exists.")
        return
        
    # Build references
    print(f"Found plank trainer media: {media_path}")
    builder = PlankTrainerReferenceBuilder(media_path)
    success = builder.build_references(visualize=True)
    
    if success:
        print("\n✅ Plank reference building completed successfully!")
        print("The references.json file has been updated with plank reference ranges.")
        print("You can now use these improved ranges for better plank detection.")
    else:
        print("\n❌ Plank reference building failed. Please check the media file and try again.")


if __name__ == "__main__":
    main()
