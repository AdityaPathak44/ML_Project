"""
Test script for BicepCurl integration with PoseFIt system

This script tests:
1. BicepCurl exercise class functionality
2. Integration with RepCounter
3. Reference data loading
4. Angle calculation consistency
5. Form validation logic
"""

import json
import math
from typing import Dict

from bicep_curl_exercise import BicepCurlExercise, BicepCurlIntegration, create_bicep_curl_processor
from rep_counter import RepCounter
from reference_loader import ReferenceProvider
from pose_detector import LandmarkPoint


class MockLandmark:
    """Mock landmark for testing"""
    def __init__(self, x: float, y: float, visibility: float = 0.9):
        self.x = x
        self.y = y
        self.z = 0.0
        self.visibility = visibility


def create_test_landmarks(elbow_angle: float) -> Dict[str, LandmarkPoint]:
    """Create test landmarks that form the specified elbow angle"""
    # Place shoulder at (100, 100)
    # Place elbow at (200, 100) - 100 pixels to the right
    # Calculate wrist position to create desired angle
    
    shoulder_x, shoulder_y = 100, 100
    elbow_x, elbow_y = 200, 100
    
    # For simplicity, place wrist below elbow at calculated position
    # This creates angles from ~0° (straight down) to ~180° (straight up)
    angle_rad = math.radians(elbow_angle)
    wrist_x = elbow_x + 100 * math.cos(angle_rad - math.pi/2)
    wrist_y = elbow_y + 100 * math.sin(angle_rad - math.pi/2)
    
    return {
        "LEFT_SHOULDER": MockLandmark(shoulder_x, shoulder_y),
        "LEFT_ELBOW": MockLandmark(elbow_x, elbow_y),
        "LEFT_WRIST": MockLandmark(wrist_x, wrist_y)
    }


def test_bicep_curl_exercise():
    """Test basic BicepCurl exercise functionality"""
    print("=== Testing BicepCurl Exercise ===")
    
    processor = BicepCurlExercise()
    
    # Test angle calculation
    test_landmarks = create_test_landmarks(90.0)
    calculated_angle = processor.calculate_elbow_angle(test_landmarks)
    print(f"Test angle calculation: Expected ~90°, Got {calculated_angle:.1f}°")
    
    # Test rep counting sequence
    angles_sequence = [170, 160, 120, 80, 40, 25, 30, 60, 120, 160, 170]
    rep_count = 0
    
    for angle in angles_sequence:
        test_lms = create_test_landmarks(angle)
        state = processor.process_frame(test_lms)
        if state.rep_count > rep_count:
            rep_count = state.rep_count
            print(f"Rep completed at angle {angle}°! Total reps: {rep_count}")
    
    print(f"Final rep count: {processor.rep_count}")
    print(f"Current phase: {processor.current_phase}")


def test_rep_counter_integration():
    """Test RepCounter integration with BicepCurl"""
    print("\n=== Testing RepCounter Integration ===")
    
    rep_counter = RepCounter("BicepCurl")
    print(f"Initial state - Count: {rep_counter.count}, Stage: {rep_counter.stage}")
    
    # Test angle sequence for rep counting
    test_angles = [170, 160, 150, 100, 50, 25, 30, 80, 140, 165, 170]
    
    for angle in test_angles:
        old_count = rep_counter.count
        rep_counter.update_with_angle(angle)
        if rep_counter.count > old_count:
            print(f"Rep completed! Angle: {angle}°, Stage: {rep_counter.stage}, Count: {rep_counter.count}")
    
    print(f"Final RepCounter state - Count: {rep_counter.count}, Stage: {rep_counter.stage}")


def test_reference_integration():
    """Test reference data integration"""
    print("\n=== Testing Reference Integration ===")
    
    # Load reference data
    try:
        ref_provider = ReferenceProvider("references.json")
        references = ref_provider.data
        
        # Check if BicepCurl data exists
        if "BicepCurl" in references:
            print("BicepCurl found in references:")
            bicep_refs = references["BicepCurl"]
            print(f"  Reference data: {bicep_refs}")
            
            # Test reference range extraction
            min_angle, max_angle = BicepCurlIntegration.get_reference_ranges(references)
            print(f"  Extracted ranges: Min={min_angle}°, Max={max_angle}°")
            
            # Create processor with reference data
            processor = create_bicep_curl_processor(references)
            print(f"  Processor configured with ranges: {processor.reference_min}° to {processor.reference_max}°")
        else:
            print("BicepCurl not found in references.json")
            
    except Exception as e:
        print(f"Error loading references: {e}")


def test_form_validation():
    """Test form validation logic"""
    print("\n=== Testing Form Validation ===")
    
    processor = BicepCurlExercise()
    
    test_cases = [
        (180, "Extended arm"),
        (160, "Slightly bent arm"),
        (90, "Mid-curl position"),
        (30, "Fully curled"),
        (10, "Over-curled"),
        (190, "Beyond normal range")
    ]
    
    for angle, description in test_cases:
        test_lms = create_test_landmarks(angle)
        state = processor.process_frame(test_lms)
        
        status = "✓" if state.is_valid_form else "✗"
        print(f"{status} {description} ({angle}°): {state.feedback_message}")


def test_angle_consistency():
    """Test angle calculation consistency between modules"""
    print("\n=== Testing Angle Calculation Consistency ===")
    
    from angle_utils import calculate_angle
    
    # Create test landmark
    test_lms = create_test_landmarks(45.0)
    
    # Method 1: Direct calculation
    shoulder = test_lms["LEFT_SHOULDER"]
    elbow = test_lms["LEFT_ELBOW"]
    wrist = test_lms["LEFT_WRIST"]
    
    direct_angle = calculate_angle(
        (shoulder.x, shoulder.y),
        (elbow.x, elbow.y), 
        (wrist.x, wrist.y)
    )
    
    # Method 2: Through BicepCurl class
    processor = BicepCurlExercise()
    class_angle = processor.calculate_elbow_angle(test_lms)
    
    # Method 3: Through integration helper
    angles_dict = BicepCurlIntegration.compute_angles_for_feedback(test_lms)
    integration_angle = angles_dict.get("Elbow", float('nan'))
    
    print(f"Direct calculation: {direct_angle:.1f}°")
    print(f"BicepCurl class: {class_angle:.1f}°")
    print(f"Integration helper: {integration_angle:.1f}°")
    
    # Check consistency
    if (abs(direct_angle - class_angle) < 0.1 and 
        abs(direct_angle - integration_angle) < 0.1):
        print("✓ All methods consistent!")
    else:
        print("✗ Inconsistency detected!")


def main():
    """Run all tests"""
    print("BicepCurl Integration Test Suite")
    print("=" * 50)
    
    try:
        test_bicep_curl_exercise()
        test_rep_counter_integration()
        test_reference_integration()
        test_form_validation()
        test_angle_consistency()
        
        print("\n" + "=" * 50)
        print("All tests completed!")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
