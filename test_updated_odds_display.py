#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv

# Add current directory to path
sys.path.append('.')

load_dotenv()

def test_updated_odds_display():
    """Test the updated odds display system"""
    
    fixture_id = 19468975  # The live match with odds
    
    print(f"🎯 TESTING UPDATED ODDS DISPLAY SYSTEM")
    print(f"=" * 60)
    
    try:
        # Import our updated function
        from web_dashboard import check_corner_odds_available
        
        print(f"🔍 Testing check_corner_odds_available({fixture_id})...")
        
        result = check_corner_odds_available(fixture_id)
        
        print(f"\n📊 UPDATED RESULT STRUCTURE:")
        print(f"=" * 40)
        
        for key, value in result.items():
            if key == 'odds_details' and isinstance(value, list):
                print(f"{key}: {len(value)} odds")
                for i, odds in enumerate(value, 1):
                    print(f"   {i}. {odds}")
            elif key == 'active_odds' and isinstance(value, list):
                print(f"{key}: {len(value)} active odds")
                for i, odds in enumerate(value, 1):
                    print(f"   {i}. {odds}")
            else:
                print(f"{key}: {value}")
        
        print(f"\n🎯 WHAT THIS MEANS:")
        print(f"=" * 40)
        
        if result.get('available'):
            total_count = result.get('count', 0)
            active_count = result.get('active_count', 0)
            suspended_count = total_count - active_count
            
            print(f"✅ Corner odds found!")
            print(f"📊 Total: {total_count} odds available")
            print(f"🟢 Active: {active_count} odds (can bet on these)")
            print(f"🔶 Suspended: {suspended_count} odds (not bettable)")
            
            if result.get('active_odds'):
                print(f"\n💎 BETTABLE RIGHT NOW:")
                for odds in result['active_odds']:
                    print(f"   • {odds}")
            
            print(f"\n🚀 This detailed info will now appear in:")
            print(f"   ✅ Dashboard logs (every minute)")
            print(f"   ✅ Elite alert logs (at 85')")
            print(f"   ✅ Alert messages to Telegram")
        else:
            print(f"❌ No corner odds available")
            
    except Exception as e:
        print(f"💥 Exception: {e}")

if __name__ == "__main__":
    test_updated_odds_display() 