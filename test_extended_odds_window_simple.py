#!/usr/bin/env python3

def test_extended_odds_window_simple():
    """Simple test for the new extended 70-90 minute window logic"""
    
    print(f"🎯 TESTING EXTENDED ODDS WINDOW (70-90 MINUTES)")
    print(f"=" * 60)
    
    def should_check_odds_simple(minute):
        """Simplified version of should_check_odds logic"""
        return 70 <= minute <= 90
    
    # Test different minutes to show the new window
    test_cases = [
        (65, "Before window"),
        (69, "Just before window"), 
        (70, "Window start ✨"),
        (75, "Early window"),
        (80, "Mid window"),
        (85, "Alert minute 🎯"),
        (88, "Late window"),
        (90, "Window end"),
        (91, "After window"),
        (95, "Well after window")
    ]
    
    print(f"📊 MINUTE-BY-MINUTE TESTING:")
    print(f"-" * 50)
    
    for minute, description in test_cases:
        should_check = should_check_odds_simple(minute)
        status = "✅ CHECK ODDS" if should_check else "❌ SKIP"
        print(f"Minute {minute:2d} ({description:20s}): {status}")
    
    print(f"\n🎯 COMPARISON WITH OLD SYSTEM:")
    print(f"=" * 50)
    print(f"OLD (80-90 minutes):")
    for minute in range(75, 96):
        old_check = 80 <= minute <= 90
        print(f"  {minute}': {'✅' if old_check else '❌'}", end="")
        if minute % 5 == 4:  # New line every 5
            print()
    
    print(f"\nNEW (70-90 minutes):")
    for minute in range(75, 96):
        new_check = 70 <= minute <= 90
        print(f"  {minute}': {'✅' if new_check else '❌'}", end="")
        if minute % 5 == 4:  # New line every 5
            print()
    
    print(f"\n\n🚀 BENEFITS OF EXTENSION:")
    print(f"=" * 50)
    print(f"✅ 10 EXTRA MINUTES of odds data (70-79')")
    print(f"✅ 20 total minutes (vs 10 before)")
    print(f"✅ See odds evolution during crucial final period")
    print(f"✅ Earlier opportunity detection")
    print(f"✅ Better betting context for 85' alerts")
    
    print(f"\n📊 API IMPACT ANALYSIS:")
    print(f"=" * 50)
    print(f"• Typical scenario: 20 live matches")
    print(f"• Old usage: 10 minutes × 20 matches = 200 calls/hour")
    print(f"• New usage: 20 minutes × 20 matches = 400 calls/hour")
    print(f"• Rate limit: 3000 calls/hour")
    print(f"• Utilization: 400/3000 = 13.3% (VERY SAFE! 🟢)")
    print(f"• Remaining capacity: 2600 calls for other features")

if __name__ == "__main__":
    test_extended_odds_window_simple() 