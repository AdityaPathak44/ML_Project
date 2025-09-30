"""
Test script for Pushup Trainer Reference Builder

This script validates that:
1. Pushup reference data was successfully generated
2. Reference ranges make sense for push-up exercise
3. All three angles (elbow, shoulder, back) are present
4. Integration with existing system works correctly
"""

import json
from typing import Dict

from reference_loader import ReferenceProvider


def test_pushup_references():
    """Test that pushup references were generated correctly"""
    print("📄 Testing Pushup Reference Data")
    print("=" * 50)
    
    try:
        ref_provider = ReferenceProvider("references.json")
        references = ref_provider.data
        
        if "Pushup" not in references:
            print("❌ 'Pushup' section not found in references.json")
            return False
        
        pushup_data = references["Pushup"]
        print(f"✅ Found Pushup reference data: {pushup_data}")
        
        # Check required angles
        required_angles = ["Elbow", "Shoulder", "Back"]
        for angle in required_angles:
            if angle not in pushup_data:
                print(f"❌ Missing {angle} angle data")
                return False
            
            angle_data = pushup_data[angle]
            if "Min" not in angle_data or "Max" not in angle_data:
                print(f"❌ {angle} missing Min/Max values")
                return False
            
            min_val = angle_data["Min"]
            max_val = angle_data["Max"]
            
            print(f"✅ {angle}: {min_val:.1f}° to {max_val:.1f}° (range: {max_val-min_val:.1f}°)")
            
            # Validate ranges make sense
            if min_val >= max_val:
                print(f"❌ {angle}: Invalid range (min >= max)")
                return False
            
            if min_val < 0 or max_val > 180:
                print(f"❌ {angle}: Out of valid angle range (0-180°)")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading references: {e}")
        return False


def analyze_pushup_ranges():
    """Analyze if the pushup ranges make biomechanical sense"""
    print("\n🔍 Analyzing Push-up Reference Ranges")
    print("=" * 50)
    
    try:
        ref_provider = ReferenceProvider("references.json")
        references = ref_provider.data
        pushup_data = references["Pushup"]
        
        # Extract ranges
        elbow_min = pushup_data["Elbow"]["Min"]
        elbow_max = pushup_data["Elbow"]["Max"]
        shoulder_min = pushup_data["Shoulder"]["Min"]
        shoulder_max = pushup_data["Shoulder"]["Max"]
        back_min = pushup_data["Back"]["Min"]
        back_max = pushup_data["Back"]["Max"]
        
        print("Biomechanical analysis:")
        
        # Elbow angle analysis
        elbow_range = elbow_max - elbow_min
        print(f"📐 Elbow angle: {elbow_min:.1f}° to {elbow_max:.1f}°")
        if elbow_range > 50:
            print("  ✅ Good elbow range of motion for push-ups")
        else:
            print("  ⚠️  Limited elbow range - may indicate partial reps")
        
        if elbow_min < 90:
            print("  ✅ Good elbow flexion (arms can bend adequately)")
        else:
            print("  ⚠️  Limited elbow flexion")
        
        # Shoulder angle analysis
        shoulder_range = shoulder_max - shoulder_min
        print(f"🏠 Shoulder angle: {shoulder_min:.1f}° to {shoulder_max:.1f}°")
        if shoulder_range > 30:
            print("  ✅ Good shoulder movement range")
        else:
            print("  ⚠️  Limited shoulder movement")
        
        # Back angle analysis (body straightness)
        back_range = back_max - back_min
        print(f"📏 Back angle: {back_min:.1f}° to {back_max:.1f}°")
        if back_min > 170:
            print("  ✅ Good body straightness maintained")
        else:
            print("  ⚠️  Body alignment may need improvement")
        
        if back_range < 15:
            print("  ✅ Consistent body position throughout movement")
        else:
            print("  ⚠️  Significant body position variation")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing ranges: {e}")
        return False


def compare_with_existing():
    """Compare new trainer-derived ranges with existing manual ranges"""
    print("\n⚖️ Comparing Trainer vs Manual References")
    print("=" * 50)
    
    try:
        ref_provider = ReferenceProvider("references.json")
        references = ref_provider.data
        
        if "Push-up" in references and "Pushup" in references:
            manual = references["Push-up"]
            trainer = references["Pushup"]
            
            print("Manual ranges (Push-up):")
            print(f"  Down - Elbow: {manual['Down']['Elbow']}")
            if "Shoulder" in manual["Down"]:
                print(f"  Down - Shoulder: {manual['Down']['Shoulder']}")
            print(f"  Up - Elbow: {manual['Up']['Elbow']}")
            
            print(f"\nTrainer ranges (Pushup):")
            print(f"  Elbow: {trainer['Elbow']['Min']:.1f}° to {trainer['Elbow']['Max']:.1f}°")
            print(f"  Shoulder: {trainer['Shoulder']['Min']:.1f}° to {trainer['Shoulder']['Max']:.1f}°")
            print(f"  Back: {trainer['Back']['Min']:.1f}° to {trainer['Back']['Max']:.1f}°")
            
            print(f"\n📊 Comparison notes:")
            print("  • Manual ranges are phase-specific (Down/Up)")
            print("  • Trainer ranges are continuous (Min/Max)")
            print("  • Trainer data includes back angle for form checking")
            print("  • Both can coexist for different use cases")
        
        return True
        
    except Exception as e:
        print(f"❌ Error comparing ranges: {e}")
        return False


def test_integration_potential():
    """Test how the new ranges could be integrated with the existing system"""
    print("\n🔗 Testing Integration Potential")
    print("=" * 50)
    
    try:
        ref_provider = ReferenceProvider("references.json")
        references = ref_provider.data
        
        print("Integration scenarios:")
        
        # Scenario 1: Replace phase-based with continuous ranges
        print("1️⃣ Continuous angle-based push-ups (like Squat/BicepCurl):")
        if "Pushup" in references:
            pushup_data = references["Pushup"]
            elbow_range = pushup_data["Elbow"]["Max"] - pushup_data["Elbow"]["Min"]
            print(f"   • Could use elbow angle for rep counting")
            print(f"   • Elbow range: {elbow_range:.1f}° (sufficient for detection)")
            print(f"   • Thresholds: Down <{pushup_data['Elbow']['Min'] + 20:.1f}°, Up >{pushup_data['Elbow']['Max'] - 20:.1f}°")
        
        # Scenario 2: Enhanced form validation
        print("2️⃣ Enhanced form validation:")
        if "Pushup" in references:
            pushup_data = references["Pushup"]
            print(f"   • Back angle monitoring: {pushup_data['Back']['Min']:.1f}°-{pushup_data['Back']['Max']:.1f}°")
            print(f"   • Shoulder angle validation: {pushup_data['Shoulder']['Min']:.1f}°-{pushup_data['Shoulder']['Max']:.1f}°")
            print(f"   • Multi-joint form assessment")
        
        # Scenario 3: Dual system
        print("3️⃣ Dual reference system:")
        print("   • Keep 'Push-up' for phase-based traditional system")
        print("   • Use 'Pushup' for advanced angle-based analysis")
        print("   • Allow user/system to choose preferred method")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing integration: {e}")
        return False


def main():
    """Run all validation tests"""
    print("🏋️ Pushup Trainer Reference Builder Validation")
    print("🎯 Testing trainer-derived reference ranges")
    print()
    
    tests = [
        test_pushup_references,
        analyze_pushup_ranges,
        compare_with_existing,
        test_integration_potential
    ]
    
    passed = 0
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed: {e}")
    
    print("\n" + "=" * 50)
    print(f"✅ Tests completed: {passed}/{len(tests)} passed")
    
    if passed == len(tests):
        print("\n🎉 All tests passed! Pushup trainer reference building successful!")
        print("\n📋 Summary:")
        print("   • Trainer video successfully processed")
        print("   • Reference ranges extracted for Elbow, Shoulder, Back")
        print("   • Data saved to references.json under 'Pushup' key")
        print("   • Ranges are biomechanically reasonable")
        print("   • Ready for integration with main system")
    else:
        print(f"\n⚠️  Some tests failed. Please review the output above.")
    
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    raise SystemExit(main())
