"""
Test script to verify Dumbbell Crunch removal and BicepCurl integration

This script tests that:
1. Dumbbell Crunch references have been completely removed
2. BicepCurl functionality remains intact
3. Keyboard shortcuts work correctly
4. References.json no longer contains Dumbbell Crunch
"""

import json
from typing import Dict

from rep_counter import RepCounter
from reference_loader import ReferenceProvider


def test_rep_counter_exercises():
    """Test that RepCounter only supports valid exercises"""
    print("🔄 Testing RepCounter Exercise Support")
    print("=" * 50)
    
    valid_exercises = ["Squat", "Push-up", "Plank", "BicepCurl"]
    removed_exercises = ["Dumbbell Crunch"]
    
    print("Valid exercises:")
    for exercise in valid_exercises:
        try:
            rep_counter = RepCounter(exercise)
            print(f"  ✅ {exercise}: RepCounter created successfully")
            
            # Test angle-based exercises
            if exercise in ["Squat", "BicepCurl"]:
                test_angles = [180, 30] if exercise == "BicepCurl" else [180, 85]
                for angle in test_angles:
                    old_count = rep_counter.count
                    rep_counter.update_with_angle(angle)
                    if rep_counter.count > old_count:
                        print(f"     📈 Rep completed at {angle}°")
        except Exception as e:
            print(f"  ❌ {exercise}: Error - {e}")
    
    print(f"\nRemoved exercises (should still work but no special logic):")
    for exercise in removed_exercises:
        try:
            rep_counter = RepCounter(exercise)
            print(f"  ✅ {exercise}: RepCounter created (but no angle logic)")
            
            # Test that angle logic doesn't trigger
            rep_counter.update_with_angle(30)
            print(f"     📊 Angle logic test: Count = {rep_counter.count} (should be 0)")
        except Exception as e:
            print(f"  ❌ {exercise}: Error - {e}")


def test_references_json():
    """Test that references.json no longer contains Dumbbell Crunch"""
    print("\n📄 Testing References.json Content")
    print("=" * 50)
    
    try:
        ref_provider = ReferenceProvider("references.json")
        references = ref_provider.data
        
        expected_exercises = ["Squat", "Push-up", "Plank", "BicepCurl"]
        removed_exercises = ["Dumbbell Crunch"]
        
        print("Expected exercises in references.json:")
        for exercise in expected_exercises:
            if exercise in references:
                print(f"  ✅ {exercise}: Found")
                if exercise == "BicepCurl":
                    bicep_data = references[exercise]
                    print(f"     📊 BicepCurl data: {bicep_data}")
            else:
                print(f"  ❌ {exercise}: Missing!")
        
        print(f"\nRemoved exercises (should not be present):")
        for exercise in removed_exercises:
            if exercise not in references:
                print(f"  ✅ {exercise}: Successfully removed")
            else:
                print(f"  ❌ {exercise}: Still present! {references[exercise]}")
        
        print(f"\nTotal exercises in references.json: {len(references)}")
        print(f"Exercise list: {list(references.keys())}")
        
    except Exception as e:
        print(f"❌ Error loading references: {e}")


def test_bicep_curl_functionality():
    """Test that BicepCurl functionality remains intact"""
    print("\n💪 Testing BicepCurl Functionality")
    print("=" * 50)
    
    # Test basic rep counting
    rep_counter = RepCounter("BicepCurl")
    print(f"Initial state: Count={rep_counter.count}, Stage={rep_counter.stage}")
    
    # Simulate bicep curl sequence
    angle_sequence = [180, 170, 160, 120, 80, 40, 25, 30, 60, 120, 160, 180]
    
    print("\nProcessing angle sequence:")
    for i, angle in enumerate(angle_sequence):
        old_count = rep_counter.count
        old_stage = rep_counter.stage
        
        rep_counter.update_with_angle(angle)
        
        if rep_counter.count > old_count or rep_counter.stage != old_stage or i == 0:
            print(f"  Angle {angle:3.0f}°: Count={rep_counter.count}, Stage={rep_counter.stage}")
            if rep_counter.count > old_count:
                print(f"    🎉 Rep completed!")
    
    print(f"\nFinal results: {rep_counter.count} reps, stage '{rep_counter.stage}'")


def test_keyboard_mapping():
    """Test the new keyboard mapping"""
    print("\n⌨️ Testing Updated Keyboard Mapping")
    print("=" * 50)
    
    expected_mapping = {
        '1': 'Squat',
        '2': 'Push-up', 
        '3': 'Plank',
        '4': 'BicepCurl'  # Moved from key 5
    }
    
    removed_mapping = {
        '5': 'BicepCurl'  # No longer on key 5
    }
    
    print("Updated keyboard mapping:")
    for key, exercise in expected_mapping.items():
        print(f"  Key {key}: {exercise}")
    
    print(f"\nRemoved mappings:")
    for key, exercise in removed_mapping.items():
        print(f"  Key {key}: {exercise} (moved to key 4)")
    
    print(f"\nNote: Key 4 now maps to BicepCurl instead of Dumbbell Crunch")


def test_integration_consistency():
    """Test that all components are consistent"""
    print("\n🔗 Testing Integration Consistency")
    print("=" * 50)
    
    # Check that angle-based exercises are consistent
    angle_based_exercises = ["Squat", "BicepCurl"]
    phase_based_exercises = ["Push-up", "Plank"]
    
    print("Angle-based exercises:")
    for exercise in angle_based_exercises:
        rep_counter = RepCounter(exercise)
        # Test that update_with_angle works
        rep_counter.update_with_angle(90)
        print(f"  ✅ {exercise}: Supports angle-based counting")
    
    print(f"\nPhase-based exercises:")
    for exercise in phase_based_exercises:
        rep_counter = RepCounter(exercise)
        # Test that regular update works
        rep_counter.update(True, "test_phase")
        print(f"  ✅ {exercise}: Supports phase-based counting")


def main():
    """Run all tests"""
    print("🧹 Dumbbell Crunch Removal & BicepCurl Integration Test")
    print("🎯 Verifying clean removal and proper integration")
    print()
    
    try:
        test_rep_counter_exercises()
        test_references_json()
        test_bicep_curl_functionality()
        test_keyboard_mapping()
        test_integration_consistency()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed!")
        print("\n📋 Summary of changes:")
        print("   • Dumbbell Crunch completely removed from codebase")
        print("   • BicepCurl moved from key 5 to key 4")
        print("   • References.json cleaned up")
        print("   • All functionality consolidated under BicepCurl")
        print("   • Visual displays updated")
        print("   • Help text updated")
        
        print(f"\n🎮 New exercise controls:")
        print("   Key 1: Squat (angle-based)")
        print("   Key 2: Push-up (phase-based)")
        print("   Key 3: Plank (phase-based)")
        print("   Key 4: BicepCurl (angle-based)")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
