#!/usr/bin/env python3
"""Debug why some matches have completely empty odds data"""

import os
from web_dashboard import check_corner_odds_available

# Test match IDs from the logs that have empty odds
test_matches = [19516813, 19347833]

for match_id in test_matches:
    print(f"🔍 Testing match {match_id}")
    print("=" * 50)
    
    result = check_corner_odds_available(match_id)
    
    print(f"   Available: {result.get('available', 'N/A')}")
    print(f"   Count: {result.get('count', 'N/A')}")
    print(f"   Active Count: {result.get('active_count', 'N/A')}")
    print(f"   Total Markets: {result.get('total_corner_markets', 'N/A')}")
    
    if 'error' in result:
        print(f"   ❌ Error: {result['error']}")
    
    odds_details = result.get('odds_details', [])
    active_odds = result.get('active_odds', [])
    
    print(f"   Odds details: {len(odds_details)} items")
    print(f"   Active odds: {len(active_odds)} items")
    
    if odds_details:
        print("   📋 Sample odds details:")
        for i, odds in enumerate(odds_details[:3]):
            print(f"      {i+1}. {odds}")
    
    print()

print("💡 EXPLANATION:")
print("If these matches show 0 odds available, it means:")
print("1. The match may have ended (no live odds)")
print("2. No corner markets were offered by bet365")
print("3. API rate limiting/caching issues")
print("4. Match might not be from a major league")
print("\nThis is different from suspended odds - it's NO odds at all.")