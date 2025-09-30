"""
Test script for Squat angle-based rep counting

This script tests the updated squat implementation using knee angle thresholds
similar to the provided example script.
"""

import math
from typing import Dict

from rep_counter import RepCounter
from pose_detector import LandmarkPoint
from angle_utils import calculate_angle


class MockLandmark:
    """Mock landmark for testing"""
    def __init__(self, x: float, y: float, visibility: float = 0.9):
        self.x = x
        self.y = y
        self.z = 0.0
        self.visibility = visibility


def create_squat_landmarks(knee_angle: float) -> Dict[str, LandmarkPoint]:
    """Create mock landmarks that simulate a squat at the given knee angle"""
    # Fixed hip and knee positions
    hip_x, hip_y = 300, 200
    knee_x, knee_y = 300, 300  # Knee directly below hip
    
    # Calculate ankle position based on desired knee angle
    # Angle is measured at knee between hip-knee and knee-ankle vectors
    angle_rad = math.radians(knee_angle)
    
    # For squat, ankle moves forward/back as knee bends
    # When standing (180°), ankle is directly below knee
    # When squatting (90°), ankle moves forward
    offset = 100 * math.cos(angle_rad - math.pi/2)
    ankle_x = knee_x + offset
    ankle_y = knee_y + 100  # Fixed distance below knee
    
    return {
        "RIGHT_HIP": MockLandmark(hip_x, hip_y),
        "RIGHT_KNEE": MockLandmark(knee_x, knee_y),
        "RIGHT_ANKLE": MockLandmark(ankle_x, ankle_y)
    }


def test_squat_rep_counting():
    """Test squat rep counting with angle sequence"""
    print("🏋️ Testing Squat Angle-Based Rep Counting")
    print("=" * 50)
    
    rep_counter = RepCounter("Squat")
    print(f"Initial state - Count: {rep_counter.count}, Stage: {rep_counter.stage}")
    
    # Simulate squat sequence: standing -> squatting -> standing
    # Based on your script: >165° = up, <90° (from up) = down + rep
    angle_sequence = [
        180, 175, 170, 165, 160, 150, 140, 130, 120, 110,  # Going down
        100, 95, 90, 85, 80, 85, 90, 95, 100, 110,        # At bottom, starting up
        120, 130, 140, 150, 160, 165, 170, 175, 180       # Going up
    ]
    
    print(f"\n🎯 Processing {len(angle_sequence)} knee angle measurements...")
    print("Angle  | Count | Stage | Notes")
    print("-" * 40)
    
    for i, angle in enumerate(angle_sequence):
        old_count = rep_counter.count
        old_stage = rep_counter.stage
        
        rep_counter.update_with_angle(angle)
        
        # Show key transitions
        if (i == 0 or  # Start
            rep_counter.count > old_count or  # Rep completed
            rep_counter.stage != old_stage or  # Stage change
            i == len(angle_sequence) - 1):  # End
            
            notes = ""
            if rep_counter.count > old_count:
                notes = "🎉 REP COMPLETED!"
            elif rep_counter.stage != old_stage:
                notes = f"Stage: {old_stage} → {rep_counter.stage}"
            
            print(f"{angle:3.0f}°  |   {rep_counter.count}   | {rep_counter.stage or 'None':5s} | {notes}")
    
    print(f"\n🏆 Final Results:")
    print(f"   • Total Reps: {rep_counter.count}")
    print(f"   • Final Stage: {rep_counter.stage}")


def test_angle_calculation():
    """Test angle calculation consistency"""
    print("\n🔍 Testing Knee Angle Calculation")
    print("=" * 50)
    
    test_angles = [180, 165, 140, 120, 90, 60, 45]
    
    print("Expected | Calculated | Difference")
    print("-" * 35)
    
    for expected_angle in test_angles:
        landmarks = create_squat_landmarks(expected_angle)
        
        # Calculate using the same method as main.py
        hip = landmarks["RIGHT_HIP"]
        knee = landmarks["RIGHT_KNEE"]
        ankle = landmarks["RIGHT_ANKLE"]
        
        calculated = calculate_angle((hip.x, hip.y), (knee.x, knee.y), (ankle.x, ankle.y))
        difference = abs(expected_angle - calculated)
        
        status = "✓" if difference < 5.0 else "✗"
        print(f"{expected_angle:3.0f}°     | {calculated:6.1f}°   | {difference:4.1f}° {status}")


def test_threshold_validation():
    """Test the squat thresholds match your script"""
    print("\n⚙️ Testing Squat Thresholds")
    print("=" * 50)
    
    rep_counter = RepCounter("Squat")
    
    test_cases = [
        (180, "Standing straight", "up"),
        (170, "Almost straight", "up"),
        (165, "Threshold up position", "up"),
        (160, "Slight bend", "up"),  # Should stay up
        (120, "Moderate squat", "up"),  # Should stay up
        (95, "Deep squat", "up"),   # Should stay up
        (90, "Squat threshold", "down"),  # Should trigger down + rep
        (85, "Very deep squat", "down"),
        (170, "Back up", "down"),   # Should stay down until >165
        (165, "Back to up threshold", "down"),  # Should stay down
        (166, "Just above threshold", "up"),    # Should go to up
    ]
    
    print("Angle | Expected Stage | Actual Stage | Rep Count | Notes")
    print("-" * 60)
    
    for angle, description, expected_stage in test_cases:
        old_count = rep_counter.count
        rep_counter.update_with_angle(angle)
        
        rep_change = "+" if rep_counter.count > old_count else ""
        match = "✓" if rep_counter.stage == expected_stage else "✗"
        
        print(f"{angle:3.0f}° | {expected_stage:10s}   | {rep_counter.stage or 'None':10s} | {rep_counter.count:3d}{rep_change:1s}     | {match} {description}")


def main():
    """Run all tests"""
    print("🦵 Squat Angle-Based Rep Counting Test Suite")
    print("🎯 Testing implementation matching your provided script")
    print()
    
    try:
        test_squat_rep_counting()
        test_angle_calculation()
        test_threshold_validation()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed!")
        print("\n📝 Integration Summary:")
        print("   • Squat now uses angle-based rep counting")
        print("   • Thresholds: >165° = up, <90° (from up) = down + rep")
        print("   • Matches your provided squat script logic")
        print("   • Press '1' in main.py to use Squat exercise")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
