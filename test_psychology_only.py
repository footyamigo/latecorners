#!/usr/bin/env python3
"""Test the PANICKING FAVORITE ONLY system"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_psychology_only():
    print("🧪 TESTING PANICKING FAVORITE ONLY SYSTEM")
    print("=" * 50)
    
    try:
        from panicking_favorite_system import PanickingFavoriteSystem
        
        # Test import
        pf_system = PanickingFavoriteSystem()
        print("✅ PanickingFavoriteSystem imported successfully")
        
        # Test scenario: Man City (1.25) drawing 0-0 at 87 minutes
        print("\n📊 Test Scenario: Man City (1.25) vs Luton at 87'")
        
        fixture_data = {
            'odds': [{
                'bookmaker_id': 2,
                'markets': [{
                    'market_id': 1,
                    'selections': [
                        {'label': '1', 'odds': 1.25},  # Man City (massive favorite)
                        {'label': '2', 'odds': 10.00}  # Luton (massive underdog)
                    ]
                }]
            }]
        }
        
        match_data = {
            'minute': 87,
            'home_score': 0,
            'away_score': 0,
            'total_corners': 9,
            'total_shots': 18,
            'total_shots_on_target': 6
        }
        
        momentum_data = {
            'home_momentum10': 88,  # City desperate
            'away_momentum10': 42   # Luton defending
        }
        
        # Simulate timing and odds checks (as would happen in main.py)
        timing_ok = 85 <= match_data['minute'] <= 89
        odds_ok = True  # Assume corner odds available
        
        print(f"   Minute: {match_data['minute']} - Timing OK: {timing_ok}")
        print(f"   Corner odds available: {odds_ok}")
        
        # Test psychology evaluation
        psychology_alert = pf_system.evaluate_panicking_favorite_alert(
            fixture_data, match_data, momentum_data
        )
        
        if psychology_alert:
            print(f"   🧠 PSYCHOLOGY ALERT DETECTED!")
            print(f"      Alert Type: {psychology_alert['alert_type']}")
            print(f"      Panic Level: {psychology_alert['panic_level']}")
            print(f"      Favorite Odds: {psychology_alert['favorite_odds']:.2f}")
            print(f"      Psychology Score: {psychology_alert['psychology_score']:.1f}")
            print(f"      Reasoning: {psychology_alert['reasoning']}")
            
            # Simulate main.py logic
            if psychology_alert and timing_ok and odds_ok:
                print("\n   🚨 ALERT WOULD BE SENT!")
                print("      ✅ Psychology alert detected")
                print("      ✅ Timing requirement met (85-89 min)")
                print("      ✅ Corner odds available")
                print("\n   📱 Alert Tier: PANICKING_FAVORITE")
            else:
                print("\n   ❌ Alert conditions not fully met")
        else:
            print(f"   😐 No psychology alert detected")
        
        print("\n" + "=" * 50)
        print("🎉 PANICKING FAVORITE ONLY TEST COMPLETE!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_psychology_only()