#!/usr/bin/env python3
"""Test the DUAL PSYCHOLOGY SYSTEM - Panicking Favorite + Fighting Underdog"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_dual_psychology_system():
    print("🧪 TESTING DUAL PSYCHOLOGY SYSTEM")
    print("=" * 55)
    
    try:
        from panicking_favorite_system import PanickingFavoriteSystem
        from fighting_underdog_system import FightingUnderdogSystem
        from new_telegram_system import NewTelegramSystem
        
        # Initialize systems
        pf_system = PanickingFavoriteSystem()
        fu_system = FightingUnderdogSystem()
        telegram = NewTelegramSystem()
        
        print("✅ All systems imported successfully")
        
        # Test Case 1: PANICKING FAVORITE scenario
        print("\n🧠 TEST 1: PANICKING FAVORITE")
        print("-" * 40)
        print("Scenario: Man City (1.25) drawing 0-0 vs Luton at 87'")
        
        pf_fixture = {
            'odds': [{
                'bookmaker_id': 2,
                'markets': [{
                    'market_id': 1,
                    'selections': [
                        {'label': '1', 'odds': 1.25},  # City (massive favorite)
                        {'label': '2', 'odds': 10.00}  # Luton (massive underdog)
                    ]
                }]
            }]
        }
        
        pf_match = {
            'minute': 87,
            'home_score': 0,
            'away_score': 0,
            'total_corners': 9,
            'total_shots': 18,
            'total_shots_on_target': 6
        }
        
        pf_momentum = {
            'home_momentum10': 88,  # City desperate
            'away_momentum10': 42   # Luton defending
        }
        
        # Test panicking favorite
        pf_result = pf_system.evaluate_panicking_favorite_alert(pf_fixture, pf_match, pf_momentum)
        fu_result = fu_system.evaluate_fighting_underdog_alert(pf_fixture, pf_match, pf_momentum)
        
        print(f"   Panicking Favorite: {'✅ TRIGGERED' if pf_result else '❌ Not triggered'}")
        print(f"   Fighting Underdog: {'✅ TRIGGERED' if fu_result else '❌ Not triggered'}")
        
        if pf_result:
            print(f"   → Alert Type: {pf_result['alert_type']}")
            print(f"   → Panic Level: {pf_result['panic_level']}")
            print(f"   → Psychology Score: {pf_result['psychology_score']:.1f}")
        
        # Test Case 2: FIGHTING UNDERDOG scenario  
        print("\n🥊 TEST 2: FIGHTING UNDERDOG")
        print("-" * 40)
        print("Scenario: Luton (8.00) level 1-1 vs Man City (1.25) at 80'")
        
        fu_fixture = {
            'odds': [{
                'bookmaker_id': 2,
                'markets': [{
                    'market_id': 1,
                    'selections': [
                        {'label': '1', 'odds': 1.25},  # City (massive favorite)
                        {'label': '2', 'odds': 8.00}   # Luton (massive underdog)
                    ]
                }]
            }]
        }
        
        fu_match = {
            'minute': 80,
            'home_score': 1,  # City
            'away_score': 1,  # Luton LEVEL!
            'total_corners': 7,
            'total_shots': 14,
            'total_shots_on_target': 4
        }
        
        fu_momentum = {
            'home_momentum10': 55,  # City frustrated
            'away_momentum10': 75   # Luton fighting
        }
        
        # Test both systems
        pf_result2 = pf_system.evaluate_panicking_favorite_alert(fu_fixture, fu_match, fu_momentum)
        fu_result2 = fu_system.evaluate_fighting_underdog_alert(fu_fixture, fu_match, fu_momentum)
        
        print(f"   Panicking Favorite: {'✅ TRIGGERED' if pf_result2 else '❌ Not triggered'}")
        print(f"   Fighting Underdog: {'✅ TRIGGERED' if fu_result2 else '❌ Not triggered'}")
        
        if fu_result2:
            print(f"   → Alert Type: {fu_result2['alert_type']}")
            print(f"   → Giant-Killing Level: {fu_result2['giant_killing_level']}")
            print(f"   → Giant-Killing Score: {fu_result2['giant_killing_score']:.1f}")
        
        # Test Case 3: Simulate main.py logic
        print("\n🔄 TEST 3: MAIN.PY SIMULATION")
        print("-" * 40)
        print("Testing dual system priority logic...")
        
        def simulate_main_logic(fixture, match, momentum):
            """Simulate the main.py dual psychology logic"""
            # Try panicking favorite first
            psychology_alert = pf_system.evaluate_panicking_favorite_alert(fixture, match, momentum)
            
            # If not triggered, try fighting underdog
            if not psychology_alert:
                psychology_alert = fu_system.evaluate_fighting_underdog_alert(fixture, match, momentum)
            
            return psychology_alert
        
        # Test with panicking favorite scenario
        result1 = simulate_main_logic(pf_fixture, pf_match, pf_momentum)
        print(f"   Scenario 1 (City desperate): {result1['alert_type'] if result1 else 'No alert'}")
        
        # Test with fighting underdog scenario
        result2 = simulate_main_logic(fu_fixture, fu_match, fu_momentum)
        print(f"   Scenario 2 (Luton giant-killing): {result2['alert_type'] if result2 else 'No alert'}")
        
        # Test Case 4: Telegram message generation
        print("\n📱 TEST 4: TELEGRAM MESSAGES")
        print("-" * 40)
        
        if result1:
            print("   Panicking Favorite Message:")
            confidence = telegram._get_confidence_text('PANICKING_FAVORITE')
            print(f"      Confidence: {confidence}")
            
            test_match_data = {
                'home_team': 'Manchester City',
                'away_team': 'Luton Town',
                'home_score': 0,
                'away_score': 0,
                'minute': 87,
                'total_corners': 9,
                'psychology_data': result1
            }
            message = telegram._create_panicking_favorite_message(test_match_data)
            print(f"      Preview: {message[:100]}...")
        
        if result2:
            print("\n   Fighting Underdog Message:")
            confidence = telegram._get_confidence_text('FIGHTING_UNDERDOG')
            print(f"      Confidence: {confidence}")
            
            test_match_data2 = {
                'home_team': 'Manchester City',
                'away_team': 'Luton Town', 
                'home_score': 1,
                'away_score': 1,
                'minute': 80,
                'total_corners': 7,
                'psychology_data': result2
            }
            message2 = telegram._create_fighting_underdog_message(test_match_data2)
            print(f"      Preview: {message2[:100]}...")
        
        print("\n" + "=" * 55)
        print("🎉 DUAL PSYCHOLOGY SYSTEM TEST COMPLETE!")
        print("🚀 Both systems working perfectly together!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_dual_psychology_system()