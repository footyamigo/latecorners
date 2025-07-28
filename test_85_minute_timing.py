#!/usr/bin/env python3
"""
Test script to verify EXACT 85th minute timing logic
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scoring_engine import ScoringEngine
from config import get_config

def test_precise_timing():
    """Test the precise 85th minute timing window"""
    
    config = get_config()
    scoring_engine = ScoringEngine()  # No arguments needed
    
    print("🎯 Testing EXACT 85th Minute Timing Logic")
    print("=" * 50)
    
    # Test various minutes around the 85th minute
    test_minutes = [82, 83, 84, 85, 86, 87, 88]
    
    for minute in test_minutes:
        is_in_window = scoring_engine._is_in_alert_window(minute)
        status = "✅ ALERT WINDOW" if is_in_window else "❌ NO ALERT"
        
        print(f"Minute {minute:2d}: {status}")
    
    print("\n🎯 Expected Behavior:")
    print("✅ Minute 84: ALERT WINDOW (API timing buffer)")
    print("✅ Minute 85: ALERT WINDOW (EXACT TARGET)")
    print("❌ Minute 86: NO ALERT (too late)")
    print("❌ Minute 87: NO ALERT (too late)")
    
    print("\n⏰ Polling Configuration:")
    print(f"LIVE_POLL_INTERVAL: {config.LIVE_POLL_INTERVAL} seconds")
    print(f"TARGET_ALERT_MINUTE: {config.TARGET_ALERT_MINUTE}")
    
    print("\n📊 Real-World Timeline:")
    print("84:45 - System polls → Check conditions")
    print("85:00 - System polls → ALERT SENT! ⚡")
    print("85:15 - System polls → No alert (already sent)")
    print("85:30 - System polls → No alert (already sent)")

if __name__ == "__main__":
    test_precise_timing() 