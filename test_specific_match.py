import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()
print("✅ Loaded .env file")

api_key = os.getenv('SPORTMONKS_API_KEY')

# Test specific match that's in late 2nd half
test_match_id = 19380117  # Malmö FF W vs Vittsjo W at 111 minutes
print(f"📊 Testing statistics for specific match ID: {test_match_id}")

# Get detailed fixture stats
fixture_url = f"https://api.sportmonks.com/v3/football/fixtures/{test_match_id}"
fixture_params = {
    'api_token': api_key,
    'include': 'statistics;events;scores;participants;state;periods'
}

print("📈 Fetching detailed fixture statistics...")
fixture_response = requests.get(fixture_url, params=fixture_params)
fixture_data = fixture_response.json()

if 'data' in fixture_data:
    fixture = fixture_data['data']
    
    # Show match info first
    participants = fixture.get('participants', [])
    if participants:
        print(f"\n⚽ MATCH INFO:")
        for participant in participants:
            name = participant.get('name', 'Unknown')
            participant_id = participant.get('id', 'Unknown')
            meta = participant.get('meta', {})
            location = meta.get('location', 'unknown')
            print(f"   {location.upper()}: {name} (ID: {participant_id})")
    
    # Show current state and minute
    state = fixture.get('state', {})
    periods = fixture.get('periods', [])
    minute = 0
    for period in periods:
        if period.get('ticking', False):
            minute = period.get('minutes', 0)
            if '2nd' in period.get('description', '').lower():
                minute += 45
            break
    
    print(f"   State: {state.get('developer_name', 'Unknown')} | Minute: {minute}'")
    
    # Show statistics structure
    statistics = fixture.get('statistics', [])
    print(f"\n📊 Found {len(statistics)} statistics entries")
    
    if statistics:
        print("\n🔍 All Available Statistics:")
        print("=" * 80)
        
        # Group by location (home/away)
        home_stats = {}
        away_stats = {}
        
        for stat in statistics:
            location = stat.get('location', 'unknown')
            type_id = stat.get('type_id', 'Unknown')
            value = stat.get('data', {}).get('value', 0)
            participant_id = stat.get('participant_id', 'Unknown')
            
            stat_info = {
                'type_id': type_id,
                'value': value,
                'participant_id': participant_id
            }
            
            if location == 'home':
                home_stats[type_id] = stat_info
            elif location == 'away':
                away_stats[type_id] = stat_info
        
        # Enhanced stat type mapping
        stat_type_mapping = {
            12: "Corners",
            13: "Shots Total", 
            14: "Shots on Goal",
            15: "Shots off Goal",
            16: "Shots Blocked",
            17: "Shots Inside Box",
            18: "Shots Outside Box",
            19: "Fouls",
            20: "Corner Kicks",
            44: "Attacks",
            45: "Dangerous Attacks",
            46: "Yellow Cards",
            47: "Red Cards",
            52: "Possession %",
            83: "Big Chances Created",
            84: "Big Chances Missed",
            1: "Ball Possession",
            2: "Goal Attempts",
            3: "Goals",
            4: "Saves",
            5: "Substitutions",
            6: "Free Kicks",
            7: "Goal Kicks",
            8: "Throw Ins",
            9: "Offsides",
            10: "Crosses",
            11: "Dribbles"
        }
        
        print("\n📋 ALL FOUND STATS:")
        print("=" * 80)
        all_type_ids = set(home_stats.keys()) | set(away_stats.keys())
        for type_id in sorted(all_type_ids):
            home_val = home_stats.get(type_id, {}).get('value', 'N/A')
            away_val = away_stats.get(type_id, {}).get('value', 'N/A')
            stat_name = stat_type_mapping.get(type_id, f"Unknown Type {type_id}")
            print(f"   {stat_name:<20} | Type ID: {type_id:<3} | Home: {home_val:<3} | Away: {away_val}")
        
        # Focus on key stats for corner system
        print("\n🎯 KEY STATS FOR CORNER SYSTEM:")
        print("=" * 80)
        key_type_ids = [12, 13, 14, 16, 20, 44, 45, 46, 47, 83, 84]  # Corners, shots, attacks, cards, chances
        
        for type_id in key_type_ids:
            if type_id in all_type_ids:
                home_val = home_stats.get(type_id, {}).get('value', 'N/A')
                away_val = away_stats.get(type_id, {}).get('value', 'N/A')
                stat_name = stat_type_mapping.get(type_id, f"Type {type_id}")
                print(f"   ✅ {stat_name:<20} | Type ID: {type_id:<3} | Home: {home_val:<3} | Away: {away_val}")
            else:
                stat_name = stat_type_mapping.get(type_id, f"Type {type_id}")
                print(f"   ❌ {stat_name:<20} | Type ID: {type_id:<3} | NOT AVAILABLE")
    
    else:
        print("❌ No statistics found in API response")
        
    # Also show a sample of the raw structure
    print(f"\n📋 RAW STATISTICS STRUCTURE (first 5):")
    for i, stat in enumerate(statistics[:5]):
        print(f"   Stat {i+1}: {json.dumps(stat, indent=4)}")

else:
    print("❌ No fixture data returned")
    print(f"Response: {json.dumps(fixture_data, indent=2)}") 