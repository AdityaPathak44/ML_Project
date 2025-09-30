"""
Bicep Curl Exercise Implementation

This module provides comprehensive bicep curl functionality including:
- Angle calculation (elbow angle: shoulder-elbow-wrist)
- Rep counting with phase tracking (up/down)
- Reference range validation
- Integration with existing PoseFIt system

Usage:
    from bicep_curl_exercise import BicepCurlExercise
    
    # Initialize
    bicep = BicepCurlExercise()
    
    # Process frame
    results = bicep.process_frame(landmarks)
    
    # Get current state
    angle = bicep.current_angle
    reps = bicep.rep_count
    phase = bicep.current_phase
"""

import math
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

from pose_detector import LandmarkPoint
from angle_utils import calculate_angle


@dataclass
class BicepCurlState:
    """Current state of bicep curl exercise"""
    angle: float
    phase: str  # 'up' or 'down'
    rep_count: int
    is_valid_form: bool
    feedback_message: str


class BicepCurlExercise:
    """
    Bicep Curl Exercise Processor
    
    Handles angle calculation, rep counting, and form validation for bicep curls.
    Uses elbow angle (shoulder-elbow-wrist) as primary measurement.
    """
    
    def __init__(self, angle_thresholds: Optional[Dict[str, float]] = None):
        """
        Initialize bicep curl processor.
        
        Args:
            angle_thresholds: Custom angle thresholds for rep counting
                            Default: {'extended': 160, 'flexed': 30}
        """
        # Default thresholds based on typical bicep curl movement
        self.thresholds = angle_thresholds or {
            'extended': 160.0,  # Arm fully extended (down position)
            'flexed': 30.0,     # Arm fully flexed (up position)
            'transition': 90.0   # Mid-point for smooth transitions
        }
        
        # State tracking
        self.rep_count = 0
        self.current_phase: Optional[str] = None  # 'up', 'down', or None
        self.current_angle = float('nan')
        self.previous_angle = float('nan')
        
        # Reference ranges (loaded from references.json)
        self.reference_min = 7.4   # From trainer video analysis
        self.reference_max = 180.0
        
        # Form validation
        self.form_tolerance = 15.0  # Degrees tolerance for "good form"
        
    def set_reference_ranges(self, min_angle: float, max_angle: float) -> None:
        """Set reference ranges from loaded data"""
        self.reference_min = min_angle
        self.reference_max = max_angle
        
    def calculate_elbow_angle(self, landmarks: Dict[str, LandmarkPoint]) -> float:
        """
        Calculate elbow angle from pose landmarks.
        Tries left side first, then right side.
        
        Args:
            landmarks: Dictionary of detected landmarks
            
        Returns:
            Elbow angle in degrees, or NaN if calculation fails
        """
        for prefix in ["LEFT_", "RIGHT_"]:
            shoulder_key = f"{prefix}SHOULDER"
            elbow_key = f"{prefix}ELBOW"
            wrist_key = f"{prefix}WRIST"
            
            if all(key in landmarks for key in [shoulder_key, elbow_key, wrist_key]):
                shoulder = landmarks[shoulder_key]
                elbow = landmarks[elbow_key]
                wrist = landmarks[wrist_key]
                
                # Check visibility (if available)
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
        
        return float('nan')
    
    def update_rep_count(self, angle: float) -> bool:
        """
        Update rep count based on angle measurement.
        Uses state machine approach for reliable counting.
        
        Args:
            angle: Current elbow angle
            
        Returns:
            True if a new rep was completed, False otherwise
        """
        if math.isnan(angle):
            return False
            
        new_rep = False
        
        # State machine for rep counting
        if angle >= self.thresholds['extended']:
            # Arm is extended (down position)
            if self.current_phase != 'down':
                self.current_phase = 'down'
                
        elif angle <= self.thresholds['flexed']:
            # Arm is flexed (up position)
            if self.current_phase == 'down':
                # Complete rep: down -> up
                self.current_phase = 'up'
                self.rep_count += 1
                new_rep = True
            elif self.current_phase != 'up':
                self.current_phase = 'up'
                
        # Store angle for next iteration
        self.previous_angle = self.current_angle
        self.current_angle = angle
        
        return new_rep
    
    def validate_form(self, angle: float) -> Tuple[bool, str]:
        """
        Validate bicep curl form based on reference ranges.
        
        Args:
            angle: Current elbow angle
            
        Returns:
            Tuple of (is_valid, feedback_message)
        """
        if math.isnan(angle):
            return False, "Arm not visible - ensure full body is in frame"
        
        # Check if angle is within expected range
        if angle < (self.reference_min - self.form_tolerance):
            return False, "Don't curl too high - control the movement"
        elif angle > (self.reference_max + self.form_tolerance):
            return False, "Extend arm fully but don't lock elbow"
        
        # Check for smooth movement (avoid jerky motions)
        if not math.isnan(self.previous_angle):
            angle_change = abs(angle - self.previous_angle)
            if angle_change > 20.0:  # Large sudden changes indicate jerky movement
                return False, "Move smoothly - avoid jerky motions"
        
        # Form is good
        phase_msg = f"Phase: {self.current_phase.title()}" if self.current_phase else "Start curling"
        return True, f"Good form! {phase_msg}"
    
    def process_frame(self, landmarks: Dict[str, LandmarkPoint]) -> BicepCurlState:
        """
        Process a single frame for bicep curl analysis.
        
        Args:
            landmarks: Dictionary of detected pose landmarks
            
        Returns:
            BicepCurlState with current exercise state
        """
        # Calculate elbow angle
        angle = self.calculate_elbow_angle(landmarks)
        
        # Update rep count
        new_rep = self.update_rep_count(angle)
        
        # Validate form
        is_valid, feedback = self.validate_form(angle)
        
        # Return current state
        return BicepCurlState(
            angle=angle,
            phase=self.current_phase or 'unknown',
            rep_count=self.rep_count,
            is_valid_form=is_valid,
            feedback_message=feedback
        )
    
    def reset(self) -> None:
        """Reset exercise state"""
        self.rep_count = 0
        self.current_phase = None
        self.current_angle = float('nan')
        self.previous_angle = float('nan')
    
    def get_angle_display_info(self, landmarks: Dict[str, LandmarkPoint]) -> Optional[Dict]:
        """
        Get information for displaying angle on screen.
        
        Args:
            landmarks: Dictionary of detected landmarks
            
        Returns:
            Dictionary with display information or None if not available
        """
        # Find the active side (left or right)
        for prefix in ["LEFT_", "RIGHT_"]:
            shoulder_key = f"{prefix}SHOULDER"
            elbow_key = f"{prefix}ELBOW"
            wrist_key = f"{prefix}WRIST"
            
            if all(key in landmarks for key in [shoulder_key, elbow_key, wrist_key]):
                elbow = landmarks[elbow_key]
                return {
                    'position': (int(elbow.x), int(elbow.y)),
                    'angle': self.current_angle,
                    'landmarks': {
                        'shoulder': landmarks[shoulder_key],
                        'elbow': landmarks[elbow_key],
                        'wrist': landmarks[wrist_key]
                    }
                }
        
        return None


class BicepCurlIntegration:
    """
    Integration helper for bicep curl with existing PoseFIt system
    """
    
    @staticmethod
    def update_rep_counter(rep_counter, angle: float) -> None:
        """Update existing RepCounter with bicep curl logic"""
        if rep_counter.exercise == "BicepCurl":
            # Bicep curl angle-based logic
            if angle > 160:  # Down position (arm extended)
                rep_counter.stage = "down"
            if angle < 30 and rep_counter.stage == 'down':  # Up position and previous was down
                rep_counter.stage = "up"
                rep_counter.count += 1
    
    @staticmethod
    def get_reference_ranges(references_data: Dict) -> Tuple[float, float]:
        """Extract bicep curl reference ranges from loaded data"""
        bicep_data = references_data.get("BicepCurl", {})
        elbow_data = bicep_data.get("Elbow", {})
        
        min_angle = elbow_data.get("Min", 7.4)
        max_angle = elbow_data.get("Max", 180.0)
        
        return min_angle, max_angle
    
    @staticmethod
    def compute_angles_for_feedback(landmarks: Dict[str, LandmarkPoint]) -> Dict[str, float]:
        """Compute angles in format expected by feedback system"""
        bicep = BicepCurlExercise()
        elbow_angle = bicep.calculate_elbow_angle(landmarks)
        
        return {
            "Elbow": elbow_angle,
            "Arm": elbow_angle  # Same angle, different name for compatibility
        }


# Convenience function for quick integration
def create_bicep_curl_processor(references_data: Optional[Dict] = None) -> BicepCurlExercise:
    """
    Create a properly configured bicep curl processor.
    
    Args:
        references_data: Optional reference data loaded from JSON
        
    Returns:
        Configured BicepCurlExercise instance
    """
    processor = BicepCurlExercise()
    
    if references_data:
        min_angle, max_angle = BicepCurlIntegration.get_reference_ranges(references_data)
        processor.set_reference_ranges(min_angle, max_angle)
    
    return processor


# Example usage and testing
if __name__ == "__main__":
    # Simple test
    processor = BicepCurlExercise()
    print(f"Bicep curl processor created with thresholds: {processor.thresholds}")
    print(f"Reference ranges: {processor.reference_min}° to {processor.reference_max}°")
    
    # Test angle validation
    test_angles = [180, 160, 90, 30, 10]
    for angle in test_angles:
        processor.current_angle = angle
        valid, msg = processor.validate_form(angle)
        print(f"Angle {angle}°: {'Valid' if valid else 'Invalid'} - {msg}")
