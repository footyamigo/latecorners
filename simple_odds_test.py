#!/usr/bin/env python3
"""Simple test of odds extraction"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def simple_odds_test():
    print("🧪 SIMPLE ODDS EXTRACTION TEST")
    print("=" * 40)
    
    try:
        from panicking_favorite_system import PanickingFavoriteSystem
        pf_system = PanickingFavoriteSystem()
        print("✅ Import successful")
        
        # Test 1: Man City vs Luton
        print("\n📊 Test 1: Man City (1.20) vs Luton (15.00)")
        fixture_data = {
            'odds': [{
                'bookmaker_id': 2,
                'markets': [{
                    'market_id': 1,
                    'selections': [
                        {'label': '1', 'odds': 1.20},
                        {'label': '2', 'odds': 15.00}
                    ]
                }]
            }]
        }
        
        odds = pf_system.get_1x2_odds_from_fixture(fixture_data)
        if odds:
            print(f"   Home odds: {odds['home_odds']}")
            print(f"   Away odds: {odds['away_odds']}")
            
            psychology = pf_system.analyze_psychology_profile(odds['home_odds'], odds['away_odds'])
            print(f"   Favorite: {psychology.favorite_team}")
            print(f"   Match type: {psychology.match_type}")
            print(f"   Pressure: {psychology.pressure_multiplier}x")
        else:
            print("   ❌ No odds extracted")
        
        # Test 2: Different label format
        print("\n📊 Test 2: Different label format")
        fixture_data2 = {
            'odds': [{
                'bookmaker_id': 2,
                'markets': [{
                    'name': 'Match Winner',
                    'selections': [
                        {'label': 'home', 'odds': 1.35},
                        {'label': 'away', 'odds': 6.00}
                    ]
                }]
            }]
        }
        
        odds2 = pf_system.get_1x2_odds_from_fixture(fixture_data2)
        if odds2:
            print(f"   Home odds: {odds2['home_odds']}")
            print(f"   Away odds: {odds2['away_odds']}")
        else:
            print("   ❌ No odds extracted")
            
        print("\n🎉 Test complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_odds_test()