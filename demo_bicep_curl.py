"""
Demo script for BicepCurl functionality

This script demonstrates the complete BicepCurl implementation without requiring a webcam.
It simulates landmark data and shows how the system processes bicep curl movements.
"""

import time
import math
from typing import Dict

from bicep_curl_exercise import BicepCurlExercise, create_bicep_curl_processor
from rep_counter import RepCounter
from reference_loader import ReferenceProvider


class MockLandmark:
    """Mock landmark for demo"""
    def __init__(self, x: float, y: float, visibility: float = 0.9):
        self.x = x
        self.y = y
        self.z = 0.0
        self.visibility = visibility


def create_mock_landmarks(elbow_angle: float) -> Dict[str, MockLandmark]:
    """Create mock landmarks that simulate a bicep curl at the given angle"""
    # Fixed shoulder and elbow positions
    shoulder_x, shoulder_y = 300, 200
    elbow_x, elbow_y = 400, 300
    
    # Calculate wrist position based on desired elbow angle
    angle_rad = math.radians(elbow_angle)
    wrist_x = elbow_x + 100 * math.cos(angle_rad - math.pi)
    wrist_y = elbow_y + 100 * math.sin(angle_rad - math.pi)
    
    return {
        "LEFT_SHOULDER": MockLandmark(shoulder_x, shoulder_y),
        "LEFT_ELBOW": MockLandmark(elbow_x, elbow_y),
        "LEFT_WRIST": MockLandmark(wrist_x, wrist_y)
    }


def simulate_bicep_curl_sequence():
    """Simulate a complete bicep curl sequence"""
    print("🏋️ Simulating Bicep Curl Sequence")
    print("=" * 50)
    
    # Initialize components
    rep_counter = RepCounter("BicepCurl")
    
    try:
        ref_provider = ReferenceProvider("references.json")
        processor = create_bicep_curl_processor(ref_provider.data)
        print(f"📊 Loaded reference ranges: {processor.reference_min}° to {processor.reference_max}°")
    except:
        processor = BicepCurlExercise()
        print("⚠️ Using default reference ranges")
    
    # Simulate a complete bicep curl rep
    # Start extended (180°) → curl up to flexed (30°) → extend back (180°)
    angle_sequence = [
        180, 175, 170, 165, 160, 150, 140, 130, 120, 110, 
        100, 90, 80, 70, 60, 50, 40, 30, 25, 30,
        40, 50, 60, 70, 80, 90, 100, 110, 120, 130,
        140, 150, 160, 170, 175, 180
    ]
    
    print(f"\\n🎯 Processing {len(angle_sequence)} angle measurements...")
    print("Angle  | Rep | Phase | Feedback")
    print("-" * 45)
    
    for i, angle in enumerate(angle_sequence):
        # Create mock landmarks for this angle
        landmarks = create_mock_landmarks(angle)
        
        # Process with both systems
        rep_counter.update_with_angle(angle)
        state = processor.process_frame(landmarks)
        
        # Show key transitions
        if (i == 0 or  # Start
            state.rep_count != (0 if i < 20 else 1) or  # Rep completion
            i == len(angle_sequence) - 1):  # End
            
            feedback_short = state.feedback_message[:25] + "..." if len(state.feedback_message) > 28 else state.feedback_message
            status = "✓" if state.is_valid_form else "✗"
            
            print(f"{angle:3.0f}°  |  {state.rep_count}  | {state.phase:5s} | {status} {feedback_short}")
        
        # Small delay for demo effect
        time.sleep(0.05)
    
    print(f"\\n🏆 Final Results:")
    print(f"   • Total Reps: {rep_counter.count}")
    print(f"   • Final Phase: {rep_counter.stage}")
    print(f"   • Processor Reps: {processor.rep_count}")
    print(f"   • Final Angle: {angle_sequence[-1]}°")


def test_different_angles():
    """Test various angles and form validation"""
    print("\\n🔍 Testing Form Validation")
    print("=" * 50)
    
    processor = BicepCurlExercise()
    
    test_angles = [
        (200, "Over-extended (beyond natural range)"),
        (180, "Fully extended (down position)"),
        (160, "Slightly bent (transition)"),
        (90, "Mid-curl (halfway)"),
        (30, "Fully curled (up position)"),
        (10, "Over-curled (too high)"),
        (0, "Extreme over-curl")
    ]
    
    print("Angle | Validation | Feedback")
    print("-" * 40)
    
    for angle, description in test_angles:
        landmarks = create_mock_landmarks(angle)
        state = processor.process_frame(landmarks)
        
        status = "✅ Valid" if state.is_valid_form else "❌ Invalid"
        print(f"{angle:3.0f}° | {status:9s} | {description}")
        print(f"      | Feedback:  | {state.feedback_message}")
        print()


def demo_integration():
    """Demonstrate integration with existing systems"""
    print("🔧 Testing System Integration")
    print("=" * 50)
    
    # Test reference loading
    try:
        ref_provider = ReferenceProvider("references.json")
        if "BicepCurl" in ref_provider.data:
            print("✅ BicepCurl found in references.json")
            bicep_data = ref_provider.data["BicepCurl"]
            print(f"   📏 Reference data: {bicep_data}")
        else:
            print("❌ BicepCurl not found in references.json")
    except Exception as e:
        print(f"⚠️ Error loading references: {e}")
    
    # Test RepCounter integration
    print("\\n🔄 RepCounter Integration:")
    rep_counter = RepCounter("BicepCurl")
    angles = [180, 160, 100, 50, 25, 60, 120, 170]
    
    for angle in angles:
        old_count = rep_counter.count
        rep_counter.update_with_angle(angle)
        if rep_counter.count > old_count:
            print(f"   📈 Rep completed at {angle}°! Total: {rep_counter.count}")
    
    print(f"   🏁 Final count: {rep_counter.count}")


def main():
    """Run the complete demo"""
    print("🏋️‍♀️ BicepCurl Implementation Demo")
    print("🎯 This demo shows the complete BicepCurl functionality")
    print()
    
    try:
        simulate_bicep_curl_sequence()
        test_different_angles()
        demo_integration()
        
        print("\\n🎉 Demo completed successfully!")
        print("\\n📝 To use in the main app:")
        print("   1. Run: python main.py")
        print("   2. Press '5' to switch to BicepCurl")
        print("   3. Perform bicep curls in front of the camera")
        
    except KeyboardInterrupt:
        print("\\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
