#!/usr/bin/env python3
"""
Test script to debug why second half stats are not being extracted for match 19401715
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sportmonks_client import SportmonksClient

def test_second_half_stats_extraction():
    """Test the exact scenario from the logs where second half stats are empty."""
    
    print("🧪 TESTING SECOND HALF STATS EXTRACTION")
    print("=" * 50)
    
    # Simulate the exact data from your logs
    periods = []  # Empty as shown in logs
    live_statistics = [
        {'type_id': 42, 'data': {'value': 13}, 'location': 'home'},   # shots_total
        {'type_id': 44, 'data': {'value': 38}, 'location': 'home'},   # dangerous_attacks  
        {'type_id': 34, 'data': {'value': 4}, 'location': 'home'},    # corners
        {'type_id': 45, 'data': {'value': 58}, 'location': 'home'},   # attacks
        {'type_id': 51, 'data': {'value': 0}, 'location': 'home'},    # offsides
        {'type_id': 41, 'data': {'value': 5}, 'location': 'home'},    # shots_off_target
        {'type_id': 86, 'data': {'value': 4}, 'location': 'home'},    # shots_on_target
        {'type_id': 42, 'data': {'value': 2}, 'location': 'away'},    # shots_total
        {'type_id': 86, 'data': {'value': 1}, 'location': 'away'},    # shots_on_target
        {'type_id': 44, 'data': {'value': 19}, 'location': 'away'},   # dangerous_attacks
        {'type_id': 41, 'data': {'value': 1}, 'location': 'away'},    # shots_off_target
        {'type_id': 34, 'data': {'value': 4}, 'location': 'away'},    # corners
        {'type_id': 45, 'data': {'value': 42}, 'location': 'away'},   # attacks
        {'type_id': 51, 'data': {'value': 1}, 'location': 'away'},    # offsides
    ]
    
    match_state = 'INPLAY_2ND_HALF'
    home_team_id = 12345  # Dummy IDs
    away_team_id = 67890
    
    # Get the stat mapping (define it directly since it's not a class attribute)
    stat_id_mapping = {
        34: 'corners',
        42: 'shots_total', 
        44: 'dangerous_attacks',
        45: 'attacks',  # ball_possession in some contexts
        51: 'offsides',
        41: 'shots_off_target',
        86: 'shots_on_target',
    }
    
    # Create client instance
    client = SportmonksClient()
    
    print(f"📊 INPUT DATA:")
    print(f"   Periods: {len(periods)} (empty)")
    print(f"   Live statistics: {len(live_statistics)} items")
    print(f"   Match state: {match_state}")
    print(f"   Is second half: {'2nd' in match_state.lower() or 'inplay_2nd_half' in match_state.lower()}")
    
    print(f"\n🗂️ STAT ID MAPPING:")
    for stat in live_statistics:
        stat_id = stat.get('type_id')
        stat_name = stat_id_mapping.get(stat_id, 'UNKNOWN')
        location = stat.get('location')
        value = stat.get('data', {}).get('value', 0)
        print(f"   Type {stat_id} -> {stat_name} ({location}: {value})")
    
    print(f"\n🔍 CALLING _extract_second_half_stats:")
    
    # Call the method directly
    result = client._extract_second_half_stats(
        periods=periods,
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        stat_id_mapping=stat_id_mapping,
        live_statistics=live_statistics,
        match_state=match_state
    )
    
    print(f"\n📈 RESULT:")
    print(f"   Home stats: {result['home']}")
    print(f"   Away stats: {result['away']}")
    
    # Check what we expected vs what we got
    expected_home_stats = ['shots_total', 'dangerous_attacks', 'attacks', 'shots_off_target', 'shots_on_target']
    expected_away_stats = ['shots_total', 'shots_on_target', 'dangerous_attacks', 'shots_off_target', 'attacks']
    
    print(f"\n✅ VALIDATION:")
    home_missing = [stat for stat in expected_home_stats if stat not in result['home']]
    away_missing = [stat for stat in expected_away_stats if stat not in result['away']]
    
    if home_missing:
        print(f"   ❌ Missing home stats: {home_missing}")
    else:
        print(f"   ✅ All expected home stats present")
        
    if away_missing:
        print(f"   ❌ Missing away stats: {away_missing}")
    else:
        print(f"   ✅ All expected away stats present")
    
    # Check if we got the key stats for scoring
    home_dangerous_attacks = result['home'].get('dangerous_attacks', 0)
    home_shots_on_target = result['home'].get('shots_on_target', 0)
    
    print(f"\n🎯 KEY SCORING STATS:")
    print(f"   Home dangerous attacks: {home_dangerous_attacks} (need 30+ for +4 points)")
    print(f"   Home shots on target: {home_shots_on_target} (need 5+ for +5 points)")
    
    if home_dangerous_attacks >= 30:
        print(f"   ✅ Would trigger: dangerous_attacks_2nd_half_30plus (+4 points)")
    else:
        print(f"   ❌ Would NOT trigger dangerous attacks bonus")
        
    if home_shots_on_target >= 5:
        print(f"   ✅ Would trigger: shots_on_target_last_15min_5plus (+5 points)")
    else:
        print(f"   ❌ Would NOT trigger shots on target bonus")
    
    return result

if __name__ == "__main__":
    test_second_half_stats_extraction() 