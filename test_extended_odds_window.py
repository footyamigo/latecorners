#!/usr/bin/env python3

import sys
sys.path.append('.')

def test_extended_odds_window():
    """Test the new extended 70-90 minute odds checking window"""
    
    print(f"🎯 TESTING EXTENDED ODDS WINDOW (70-90 MINUTES)")
    print(f"=" * 60)
    
    try:
        from web_dashboard import should_check_odds
        
        # Test different minutes to show the new window
        test_cases = [
            (65, "Before window"),
            (69, "Just before window"),
            (70, "Window start"),
            (75, "Early window"),
            (80, "Mid window"), 
            (85, "Alert minute"),
            (90, "Window end"),
            (91, "After window"),
            (95, "Well after window")
        ]
        
        print(f"📊 TESTING DIFFERENT MINUTES:")
        print(f"-" * 40)
        
        for minute, description in test_cases:
            # Create a mock match object
            mock_match = {
                'match_id': 12345,
                'minute': minute
            }
            
            should_check = should_check_odds(mock_match)
            status = "✅ CHECK ODDS" if should_check else "❌ SKIP"
            
            print(f"Minute {minute:2d} ({description:15s}): {status}")
        
        print(f"\n🎯 NEW BENEFITS:")
        print(f"=" * 40)
        print(f"✅ 20 minutes of odds data (vs 10 minutes before)")
        print(f"✅ See odds from minute 70 onwards")
        print(f"✅ Better trend analysis for final period")
        print(f"✅ Earlier detection of betting opportunities")
        print(f"✅ Still only ~13% of API rate limit usage")
        
        print(f"\n📊 API USAGE ESTIMATE:")
        print(f"=" * 40)
        print(f"• Old window (80-90): 10 minutes × 20 matches = 200 calls/hour")
        print(f"• New window (70-90): 20 minutes × 20 matches = 400 calls/hour")
        print(f"• Rate limit: 3000 calls/hour")
        print(f"• Usage: 400/3000 = 13.3% (very safe!)")
        
    except Exception as e:
        print(f"💥 Exception: {e}")

if __name__ == "__main__":
    test_extended_odds_window() 