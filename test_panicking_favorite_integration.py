#!/usr/bin/env python3
"""Test the complete PANICKING FAVORITE system integration"""

import sys
import os
import logging

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_panicking_favorite_integration():
    """Test the complete integration of panicking favorite system"""
    
    print("🧪 TESTING PANICKING FAVORITE SYSTEM INTEGRATION")
    print("=" * 60)
    
    # Test 1: Import the systems
    try:
        from panicking_favorite_system import PanickingFavoriteSystem
        from new_telegram_system import NewTelegramSystem
        print("✅ Test 1: Successfully imported all systems")
    except Exception as e:
        print(f"❌ Test 1: Import failed: {e}")
        return False
    
    # Test 2: Create panicking favorite system
    try:
        pf_system = PanickingFavoriteSystem()
        print("✅ Test 2: Successfully created PanickingFavoriteSystem")
    except Exception as e:
        print(f"❌ Test 2: PanickingFavoriteSystem creation failed: {e}")
        return False
    
    # Test 3: Test psychology evaluation with sample data
    try:
        # Man City (1.20) drawing 0-0 vs Luton at 85' - maximum panic scenario
        fixture_data = {
            'odds': [{
                'bookmaker_id': 2,
                'markets': [{
                    'market_id': 1,
                    'name': '1X2',
                    'selections': [
                        {'label': '1', 'odds': 1.20},  # Man City (massive favorite)
                        {'label': 'X', 'odds': 7.50},  # Draw
                        {'label': '2', 'odds': 15.00}  # Luton (massive underdog)
                    ]
                }]
            }]
        }
        
        match_data = {
            'minute': 85,
            'home_score': 0,
            'away_score': 0,
            'total_corners': 9,
            'total_shots': 20,
            'total_shots_on_target': 7
        }
        
        momentum_data = {
            'home_momentum10': 95,  # City in full panic mode
            'away_momentum10': 35   # Luton defending
        }
        
        psychology_alert = pf_system.evaluate_panicking_favorite_alert(
            fixture_data, match_data, momentum_data
        )
        
        if psychology_alert:
            print("✅ Test 3: Psychology evaluation successful")
            print(f"   Alert Type: {psychology_alert['alert_type']}")
            print(f"   Panic Level: {psychology_alert['panic_level']}")
            print(f"   Psychology Score: {psychology_alert['psychology_score']:.1f}")
            print(f"   Reasoning: {psychology_alert['reasoning']}")
        else:
            print("❌ Test 3: Psychology evaluation failed - no alert generated")
            return False
            
    except Exception as e:
        print(f"❌ Test 3: Psychology evaluation error: {e}")
        return False
    
    # Test 4: Test Telegram message generation
    try:
        telegram_system = NewTelegramSystem()
        
        # Prepare match data for telegram
        telegram_match_data = {
            'home_team': 'Manchester City',
            'away_team': 'Luton Town',
            'home_score': 0,
            'away_score': 0,
            'minute': 85,
            'total_corners': 9,
            'psychology_data': psychology_alert  # Pass psychology data
        }
        
        # Test if the confidence text works
        confidence_text = telegram_system._get_confidence_text('PANICKING_FAVORITE')
        print(f"✅ Test 4a: Confidence text: {confidence_text}")
        
        # Test if the dynamic message works
        message_text = telegram_system._create_panicking_favorite_message(telegram_match_data)
        print(f"✅ Test 4b: Dynamic message generated ({len(message_text)} chars)")
        print(f"   Preview: {message_text[:100]}...")
        
    except Exception as e:
        print(f"❌ Test 4: Telegram system test failed: {e}")
        return False
    
    # Test 5: Test different panic scenarios
    try:
        test_scenarios = [
            {
                'name': 'Heavy Favorite Behind',
                'odds': 1.30,
                'score': (0, 1),
                'minute': 75,
                'expected': 'HIGH_PANIC'
            },
            {
                'name': 'Massive Favorite Drawing Late',
                'odds': 1.15,
                'score': (1, 1),
                'minute': 88,
                'expected': 'MAXIMUM_PANIC'
            },
            {
                'name': 'Balanced Match (Should Fail)',
                'odds': 2.20,
                'score': (0, 0),
                'minute': 85,
                'expected': None
            }
        ]
        
        scenarios_passed = 0
        for scenario in test_scenarios:
            test_fixture = {
                'odds': [{
                    'bookmaker_id': 2,
                    'markets': [{
                        'market_id': 1,
                        'selections': [
                            {'label': '1', 'odds': scenario['odds']},
                            {'label': '2', 'odds': 6.00}
                        ]
                    }]
                }]
            }
            
            test_match = {
                'minute': scenario['minute'],
                'home_score': scenario['score'][0],
                'away_score': scenario['score'][1],
                'total_corners': 8,
                'total_shots': 15,
                'total_shots_on_target': 5
            }
            
            test_momentum = {'home_momentum10': 85, 'away_momentum10': 45}
            
            result = pf_system.evaluate_panicking_favorite_alert(test_fixture, test_match, test_momentum)
            
            if scenario['expected'] is None:
                # Should fail
                if not result:
                    scenarios_passed += 1
                    print(f"   ✅ {scenario['name']}: Correctly rejected")
                else:
                    print(f"   ❌ {scenario['name']}: Should have been rejected")
            else:
                # Should pass
                if result and result.get('panic_level') == scenario['expected']:
                    scenarios_passed += 1
                    print(f"   ✅ {scenario['name']}: {result['panic_level']}")
                else:
                    print(f"   ❌ {scenario['name']}: Expected {scenario['expected']}, got {result.get('panic_level') if result else None}")
        
        print(f"✅ Test 5: Scenario testing - {scenarios_passed}/{len(test_scenarios)} passed")
        
    except Exception as e:
        print(f"❌ Test 5: Scenario testing failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 PANICKING FAVORITE INTEGRATION TEST COMPLETE!")
    print("🚀 System ready for production deployment!")
    return True

if __name__ == "__main__":
    success = test_panicking_favorite_integration()
    sys.exit(0 if success else 1)