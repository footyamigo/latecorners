#!/usr/bin/env python3
"""
Test the extended 85-87 minute alert window to ensure alerts are sent
throughout the entire range, not just at 85th minute.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from scoring_engine import ScoringEngine

def test_extended_minute_range():
    print("🧪 TESTING EXTENDED 85-87 MINUTE ALERT WINDOW")
    print("="*60)
    
    config = Config()
    scoring_engine = ScoringEngine()
    
    print(f"📋 CONFIG:")
    print(f"   Alert window: {config.TARGET_ALERT_MINUTE_MIN}-{config.TARGET_ALERT_MINUTE_MAX} minutes")
    print()
    
    # Test different minutes around the alert window
    test_minutes = [82, 83, 84, 85, 86, 87, 88, 89]
    
    print("🎯 TESTING ALERT WINDOW LOGIC:")
    for minute in test_minutes:
        is_in_window = scoring_engine._is_in_alert_window(minute)
        
        if minute in [85, 86, 87]:
            expected = True
            status = "✅ SHOULD ALLOW" if is_in_window else "❌ BLOCKED (BUG!)"
        else:
            expected = False
            status = "✅ CORRECTLY BLOCKED" if not is_in_window else "❌ INCORRECTLY ALLOWED"
        
        print(f"   Minute {minute:2d}: {status:20s} (Expected: {expected}, Actual: {is_in_window})")
    
    # Check results
    minute_85 = scoring_engine._is_in_alert_window(85)
    minute_86 = scoring_engine._is_in_alert_window(86)
    minute_87 = scoring_engine._is_in_alert_window(87)
    minute_84 = scoring_engine._is_in_alert_window(84)
    minute_88 = scoring_engine._is_in_alert_window(88)
    
    print("\n" + "="*60)
    print("📊 SUMMARY:")
    print(f"   85th minute: {'✅ PASS' if minute_85 else '❌ FAIL'}")
    print(f"   86th minute: {'✅ PASS' if minute_86 else '❌ FAIL'}")
    print(f"   87th minute: {'✅ PASS' if minute_87 else '❌ FAIL'}")
    print(f"   84th minute (blocked): {'✅ PASS' if not minute_84 else '❌ FAIL'}")
    print(f"   88th minute (blocked): {'✅ PASS' if not minute_88 else '❌ FAIL'}")
    
    all_passed = (minute_85 and minute_86 and minute_87 and not minute_84 and not minute_88)
    print(f"\n🎯 OVERALL: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("🎉 Extended 85-87 minute window is working correctly!")
        print("   • Alerts will now be sent at 85th, 86th, AND 87th minutes")
        print("   • This captures more games with odds available after 85th minute")
    else:
        print("🚨 The extended minute range is not working correctly!")
        
    return all_passed

if __name__ == "__main__":
    success = test_extended_minute_range()
    sys.exit(0 if success else 1) 