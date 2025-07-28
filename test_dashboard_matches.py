#!/usr/bin/env python3
"""
Test script to debug dashboard live matches issue
"""

import os
import sys
sys.path.append('.')

from web_dashboard import get_live_matches

def test_dashboard_matches():
    """Test if dashboard can find live matches"""
    
    print("🔍 Testing Dashboard Live Matches Function")
    print("=" * 50)
    
    # Test the fixed dashboard function
    print("📡 Calling get_live_matches()...")
    
    try:
        matches = get_live_matches()
        
        print(f"📊 Dashboard found: {len(matches)} matches")
        
        if matches:
            print("\n✅ Found matches:")
            for i, match in enumerate(matches[:5]):  # Show first 5 matches
                print(f"  {i+1}. {match['home_team']} vs {match['away_team']} - {match['minute']}'")
                print(f"     Score: {match['home_score']}-{match['away_score']} | Status: {match['status']}")
        else:
            print("\n❌ No matches found by dashboard")
            print("   This means the dashboard API will return empty results")
            
    except Exception as e:
        print(f"❌ Error testing dashboard: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dashboard_matches() 