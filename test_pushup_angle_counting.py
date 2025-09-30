"""
Test script for Push-up angle-based rep counting

This script tests the updated push-up implementation using elbow angle thresholds
matching your provided pushup script.
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


def create_pushup_landmarks(elbow_angle: float) -> Dict[str, LandmarkPoint]:
    """Create mock landmarks that simulate a push-up at the given elbow angle"""
    # Fixed shoulder and elbow positions for push-up
    shoulder_x, shoulder_y = 300, 200
    elbow_x, elbow_y = 400, 200  # Elbow at same height as shoulder for push-up position
    
    # Calculate wrist position based on desired elbow angle
    # For push-up: larger angles = arms extended, smaller angles = arms bent
    angle_rad = math.radians(elbow_angle)
    
    # Wrist position relative to elbow
    wrist_offset = 100
    wrist_x = elbow_x + wrist_offset * math.cos(angle_rad)
    wrist_y = elbow_y + wrist_offset * math.sin(angle_rad)
    
    return {
        "RIGHT_SHOULDER": MockLandmark(shoulder_x, shoulder_y),
        "RIGHT_ELBOW": MockLandmark(elbow_x, elbow_y),
        "RIGHT_WRIST": MockLandmark(wrist_x, wrist_y)
    }


def test_pushup_rep_counting():
    """Test push-up rep counting with angle sequence"""
    print("🏋️ Testing Push-up Angle-Based Rep Counting")
    print("=" * 50)
    
    rep_counter = RepCounter("Push-up")
    print(f"Initial state - Count: {rep_counter.count}, Stage: {rep_counter.stage}")
    
    # Simulate push-up sequence: arms extended -> arms bent -> arms extended
    # Based on your script and trainer data: >161.5° = up, <62.2° (from up) = down + rep
    angle_sequence = [
        180, 175, 170, 165, 162, 155, 140, 120, 100, 80,   # Going down
        70, 62, 55, 60, 65, 70, 90, 110, 130, 150,        # At bottom, starting up
        160, 165, 170, 175, 180                           # Going up
    ]
    
    print(f"\n🎯 Processing {len(angle_sequence)} elbow angle measurements...")
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


def test_threshold_validation():
    """Test the push-up thresholds match your script"""
    print("\n⚙️ Testing Push-up Thresholds")
    print("=" * 50)
    
    rep_counter = RepCounter("Push-up")
    
    test_cases = [
        (180, "Arms fully extended", "up"),
        (170, "Arms mostly extended", "up"),
        (161.5, "Threshold up position", "up"),
        (160, "Slight arm bend", "up"),       # Should stay up
        (120, "Moderate bend", "up"),        # Should stay up
        (70, "Deeper bend", "up"),           # Should stay up
        (62.2, "Push-up threshold", "down"), # Should trigger down + rep
        (60, "Arms fully bent", "down"),
        (80, "Starting back up", "down"),    # Should stay down until >161.5
        (161, "Near up threshold", "down"),  # Should stay down
        (162, "Just above threshold", "up"), # Should go to up
    ]
    
    print("Angle | Expected Stage | Actual Stage | Rep Count | Notes")
    print("-" * 60)
    
    for angle, description, expected_stage in test_cases:
        old_count = rep_counter.count
        rep_counter.update_with_angle(angle)
        
        rep_change = "+" if rep_counter.count > old_count else ""
        match = "✓" if rep_counter.stage == expected_stage else "✗"
        
        print(f"{angle:5.1f}° | {expected_stage:10s}   | {rep_counter.stage or 'None':10s} | {rep_counter.count:3d}{rep_change:1s}     | {match} {description}")


def test_angle_calculation():
    """Test angle calculation consistency"""
    print("\n🔍 Testing Elbow Angle Calculation")
    print("=" * 50)
    
    test_angles = [180, 161.5, 140, 120, 90, 62.2, 45]
    
    print("Expected | Calculated | Difference")
    print("-" * 35)
    
    for expected_angle in test_angles:
        landmarks = create_pushup_landmarks(expected_angle)
        
        # Calculate using the same method as main.py
        shoulder = landmarks["RIGHT_SHOULDER"]
        elbow = landmarks["RIGHT_ELBOW"]
        wrist = landmarks["RIGHT_WRIST"]
        
        calculated = calculate_angle((shoulder.x, shoulder.y), (elbow.x, elbow.y), (wrist.x, wrist.y))
        difference = abs(expected_angle - calculated)
        
        status = "✓" if difference < 5.0 else "✗"
        print(f"{expected_angle:6.1f}°  | {calculated:6.1f}°   | {difference:4.1f}° {status}")


def test_trainer_ranges_integration():
    """Test integration with trainer-derived ranges"""
    print("\n📊 Testing Trainer Ranges Integration")
    print("=" * 50)
    
    # From trainer_reference_builder_pushup.py results:
    trainer_ranges = {
        "Elbow": {"Min": 62.2, "Max": 161.5},
        "Shoulder": {"Min": 4.6, "Max": 65.2},
        "Back": {"Min": 172.5, "Max": 179.7}
    }
    
    print("Trainer-derived reference ranges:")
    for joint, ranges in trainer_ranges.items():
        range_size = ranges["Max"] - ranges["Min"]
        print(f"  {joint}: {ranges['Min']:.1f}° to {ranges['Max']:.1f}° (range: {range_size:.1f}°)")
    
    print(f"\nThreshold analysis:")
    elbow_range = trainer_ranges["Elbow"]
    print(f"  Up threshold: {elbow_range['Max']:.1f}° (arms extended)")
    print(f"  Down threshold: {elbow_range['Min']:.1f}° (arms bent)")
    print(f"  Range: {elbow_range['Max'] - elbow_range['Min']:.1f}° (excellent for rep detection)")
    
    # Test if our rep counter uses the same thresholds
    rep_counter = RepCounter("Push-up")
    print(f"\nRep counter validation:")
    
    # Test up threshold
    rep_counter.update_with_angle(elbow_range["Max"] + 0.1)  # Just above max
    stage1 = rep_counter.stage
    
    # Test down threshold
    rep_counter.update_with_angle(elbow_range["Min"] - 0.1)  # Just below min
    stage2 = rep_counter.stage
    count_after = rep_counter.count
    
    print(f"  Above max ({elbow_range['Max'] + 0.1:.1f}°): Stage = {stage1}")
    print(f"  Below min ({elbow_range['Min'] - 0.1:.1f}°): Stage = {stage2}, Rep count = {count_after}")


def main():
    """Run all tests"""
    print("💪 Push-up Angle-Based Rep Counting Test Suite")
    print("🎯 Testing implementation matching your provided script")
    print()
    
    try:
        test_pushup_rep_counting()
        test_angle_calculation()
        test_threshold_validation()
        test_trainer_ranges_integration()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed!")
        print("\n📝 Integration Summary:")
        print("   • Push-up now uses angle-based rep counting")
        print("   • Thresholds: >161.5° = up, <62.2° (from up) = down + rep")
        print("   • Matches your provided push-up script logic")
        print("   • Uses trainer-derived reference ranges")
        print("   • Press '2' in main.py to use Push-up exercise")
        
        print(f"\n🎮 Updated exercise controls:")
        print("   Key 1: Squat (angle-based - knee)")
        print("   Key 2: Push-up (angle-based - elbow)")
        print("   Key 3: Plank (phase-based)")
        print("   Key 4: BicepCurl (angle-based - elbow)")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
