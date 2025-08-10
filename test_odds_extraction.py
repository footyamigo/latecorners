#!/usr/bin/env python3
"""Test odds extraction and favorite/underdog identification"""

import sys
import os
import json

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_odds_extraction():
    """Test how we extract 1X2 odds and identify favorites"""
    
    print("🧪 TESTING ODDS EXTRACTION & FAVORITE IDENTIFICATION")
    print("=" * 65)
    
    # Import the system
    try:
        from panicking_favorite_system import PanickingFavoriteSystem
        pf_system = PanickingFavoriteSystem()
        print("✅ Successfully imported PanickingFavoriteSystem")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test different fixture data formats
    test_fixtures = [
        {
            'name': 'Man City vs Luton (Massive Favorite)',
            'fixture_data': {
                'odds': [{
                    'bookmaker_id': 2,  # bet365
                    'markets': [{
                        'market_id': 1,  # 1X2 market
                        'name': '1X2',
                        'selections': [
                            {'label': '1', 'odds': 1.20},    # Man City (massive favorite)
                            {'label': 'X', 'odds': 7.50},    # Draw
                            {'label': '2', 'odds': 15.00}    # Luton (massive underdog)
                        ]
                    }]
                }]
            },
            'expected_favorite': 'home',
            'expected_favorite_odds': 1.20,
            'expected_underdog_odds': 15.00,
            'expected_type': 'HEAVY_FAVORITE_HOME'
        },
        {
            'name': 'Brighton vs Liverpool (Clear Away Favorite)',
            'fixture_data': {
                'odds': [{
                    'bookmaker_id': 2,
                    'markets': [{
                        'market_id': 1,
                        'name': 'Match Winner',
                        'selections': [
                            {'label': '1', 'odds': 4.20},    # Brighton (underdog)
                            {'label': 'X', 'odds': 3.80},    # Draw
                            {'label': '2', 'odds': 1.70}     # Liverpool (favorite)
                        ]
                    }]
                }]
            },
            'expected_favorite': 'away',
            'expected_favorite_odds': 1.70,
            'expected_underdog_odds': 4.20,
            'expected_type': 'CLEAR_FAVORITE_AWAY'
        },
        {
            'name': 'Arsenal vs Chelsea (Heavy Home Favorite)',
            'fixture_data': {
                'odds': [{
                    'bookmaker_id': 2,
                    'markets': [{
                        'name': 'Full Time Result',
                        'selections': [
                            {'label': 'home', 'odds': 1.35},  # Arsenal (heavy favorite)
                            {'label': 'draw', 'odds': 5.20},  # Draw
                            {'label': 'away', 'odds': 8.50}   # Chelsea (heavy underdog)
                        ]
                    }]
                }]
            },
            'expected_favorite': 'home',
            'expected_favorite_odds': 1.35,
            'expected_underdog_odds': 8.50,
            'expected_type': 'HEAVY_FAVORITE_HOME'
        },
        {
            'name': 'Balanced Match (No Psychological Edge)',
            'fixture_data': {
                'odds': [{
                    'bookmaker_id': 2,
                    'markets': [{
                        'name': 'Match Result',
                        'selections': [
                            {'label': '1', 'odds': 2.40},    # Home
                            {'label': 'X', 'odds': 3.20},    # Draw
                            {'label': '2', 'odds': 2.90}     # Away
                        ]
                    }]
                }]
            },
            'expected_favorite': 'home',  # Slight favorite
            'expected_favorite_odds': 2.40,
            'expected_underdog_odds': 2.90,
            'expected_type': 'BALANCED_MATCH'
        },
        {
            'name': 'No Odds Available',
            'fixture_data': {
                'odds': []  # No odds data
            },
            'expected_favorite': None,
            'expected_type': None
        }
    ]
    
    print("\n🔍 TESTING ODDS EXTRACTION:")
    print("-" * 50)
    
    for i, test in enumerate(test_fixtures, 1):
        print(f"\n📊 Test {i}: {test['name']}")
        
        try:
            # Test odds extraction
            odds_data = pf_system.get_1x2_odds_from_fixture(test['fixture_data'])
            
            if odds_data:
                print(f"   ✅ Odds extracted successfully:")
                print(f"      Home odds: {odds_data['home_odds']:.2f}")
                print(f"      Away odds: {odds_data['away_odds']:.2f}")
                if odds_data.get('draw_odds'):
                    print(f"      Draw odds: {odds_data['draw_odds']:.2f}")
                
                # Test psychology profile analysis
                psychology = pf_system.analyze_psychology_profile(
                    odds_data['home_odds'], 
                    odds_data['away_odds']
                )
                
                print(f"   🧠 Psychology Analysis:")
                print(f"      Match Type: {psychology.match_type}")
                print(f"      Favorite Team: {psychology.favorite_team}")
                print(f"      Favorite Odds: {psychology.favorite_odds:.2f}")
                print(f"      Underdog Odds: {psychology.underdog_odds:.2f}")
                print(f"      Pressure Multiplier: {psychology.pressure_multiplier:.1f}x")
                print(f"      Confidence Level: {psychology.confidence_level}")
                
                # Verify expectations
                if test.get('expected_favorite'):
                    if psychology.favorite_team == test['expected_favorite']:
                        print(f"      ✅ Favorite correctly identified: {psychology.favorite_team}")
                    else:
                        print(f"      ❌ Expected favorite: {test['expected_favorite']}, got: {psychology.favorite_team}")
                
                if test.get('expected_type'):
                    if psychology.match_type == test['expected_type']:
                        print(f"      ✅ Match type correct: {psychology.match_type}")
                    else:
                        print(f"      ❌ Expected type: {test['expected_type']}, got: {psychology.match_type}")
                
                # Test odds ratio calculation
                odds_ratio = psychology.underdog_odds / psychology.favorite_odds
                print(f"      📈 Odds Ratio: {odds_ratio:.1f}x")
                
                if odds_ratio >= 8.0:
                    print(f"      🚨 MASSIVE PSYCHOLOGICAL GAP!")
                elif odds_ratio >= 5.0:
                    print(f"      ⚠️ HIGH PSYCHOLOGICAL PRESSURE")
                elif odds_ratio >= 3.0:
                    print(f"      📊 MODERATE PSYCHOLOGICAL EDGE")
                else:
                    print(f"      😐 LIMITED PSYCHOLOGICAL IMPACT")
                    
            else:
                print(f"   ❌ No odds extracted")
                if test['expected_type'] is None:
                    print(f"      ✅ Expected no odds - correct")
                else:
                    print(f"      ❌ Expected odds but got none")
        
        except Exception as e:
            print(f"   ❌ Error in test {i}: {e}")
    
    print("\n" + "=" * 65)
    print("🎯 REAL-WORLD SCENARIOS TEST:")
    print("-" * 50)
    
    # Test complete scenarios with panic detection
    panic_scenarios = [
        {
            'name': 'MAXIMUM PANIC: Man City 1.20 drawing 0-0 at 87\'',
            'fixture_data': {
                'odds': [{
                    'bookmaker_id': 2,
                    'markets': [{
                        'market_id': 1,
                        'selections': [
                            {'label': '1', 'odds': 1.20},
                            {'label': '2', 'odds': 12.00}
                        ]
                    }]
                }]
            },
            'match_data': {
                'minute': 87,
                'home_score': 0,
                'away_score': 0,
                'total_corners': 9,
                'total_shots': 18,
                'total_shots_on_target': 6
            },
            'momentum_data': {
                'home_momentum10': 90,
                'away_momentum10': 40
            },
            'expected_panic': 'MAXIMUM_PANIC'
        },
        {
            'name': 'HIGH PANIC: Liverpool 1.30 losing 0-1 at 82\'',
            'fixture_data': {
                'odds': [{
                    'bookmaker_id': 2,
                    'markets': [{
                        'market_id': 1,
                        'selections': [
                            {'label': '1', 'odds': 3.80},
                            {'label': '2', 'odds': 1.30}
                        ]
                    }]
                }]
            },
            'match_data': {
                'minute': 82,
                'home_score': 1,
                'away_score': 0,
                'total_corners': 8,
                'total_shots': 16,
                'total_shots_on_target': 5
            },
            'momentum_data': {
                'home_momentum10': 45,
                'away_momentum10': 85
            },
            'expected_panic': 'HIGH_PANIC'
        },
        {
            'name': 'NO PANIC: Balanced match 2.20 vs 2.80',
            'fixture_data': {
                'odds': [{
                    'bookmaker_id': 2,
                    'markets': [{
                        'market_id': 1,
                        'selections': [
                            {'label': '1', 'odds': 2.20},
                            {'label': '2', 'odds': 2.80}
                        ]
                    }]
                }]
            },
            'match_data': {
                'minute': 85,
                'home_score': 0,
                'away_score': 0,
                'total_corners': 7,
                'total_shots': 12,
                'total_shots_on_target': 4
            },
            'momentum_data': {
                'home_momentum10': 70,
                'away_momentum10': 65
            },
            'expected_panic': None
        }
    ]
    
    for i, scenario in enumerate(panic_scenarios, 1):
        print(f"\n🎭 Scenario {i}: {scenario['name']}")
        
        try:
            psychology_alert = pf_system.evaluate_panicking_favorite_alert(
                scenario['fixture_data'],
                scenario['match_data'],
                scenario['momentum_data']
            )
            
            if psychology_alert:
                print(f"   🚨 ALERT TRIGGERED!")
                print(f"      Alert Type: {psychology_alert['alert_type']}")
                print(f"      Panic Level: {psychology_alert['panic_level']}")
                print(f"      Psychology Score: {psychology_alert['psychology_score']:.1f}")
                print(f"      Reasoning: {psychology_alert['reasoning']}")
                
                if scenario['expected_panic'] == psychology_alert['panic_level']:
                    print(f"      ✅ Expected panic level: {scenario['expected_panic']}")
                else:
                    print(f"      ❌ Expected: {scenario['expected_panic']}, got: {psychology_alert['panic_level']}")
            else:
                print(f"   😐 No alert triggered")
                if scenario['expected_panic'] is None:
                    print(f"      ✅ Correctly rejected (no psychological edge)")
                else:
                    print(f"      ❌ Expected {scenario['expected_panic']} but got no alert")
        
        except Exception as e:
            print(f"   ❌ Error in scenario {i}: {e}")
    
    print("\n" + "=" * 65)
    print("🎉 ODDS EXTRACTION & PSYCHOLOGY TEST COMPLETE!")
    return True

if __name__ == "__main__":
    test_odds_extraction()