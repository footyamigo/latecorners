import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()
print("✅ Loaded .env file")

api_key = os.getenv('SPORTMONKS_API_KEY')

# First get a live match ID
url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
params = {
    'api_token': api_key,
    'include': 'scores;participants;state;events;periods'
}

print("🔍 Getting live matches...")
response = requests.get(url, params=params)
data = response.json()
matches = data.get('data', [])

if matches:
    test_match_id = matches[0]['id']
    print(f"📊 Testing statistics for match ID: {test_match_id}")
    
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
        
        # Show statistics structure
        statistics = fixture.get('statistics', [])
        print(f"\n📊 Found {len(statistics)} statistics entries")
        
        if statistics:
            print("\n🔍 Available Statistics:")
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
            
            print("\n🏠 HOME TEAM STATISTICS:")
            for type_id, info in home_stats.items():
                print(f"   Type ID: {info['type_id']:<3} | Value: {info['value']:<3} | Participant: {info['participant_id']}")
            
            print("\n🏃 AWAY TEAM STATISTICS:")  
            for type_id, info in away_stats.items():
                print(f"   Type ID: {info['type_id']:<3} | Value: {info['value']:<3} | Participant: {info['participant_id']}")
            
            # Common stat type IDs (based on typical SportMonks mapping)
            print("\n🎯 LIKELY STAT TYPE MAPPINGS:")
            print("=" * 80)
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
                84: "Big Chances Missed"
            }
            
            print("\n📋 INTERPRETED STATS:")
            print("=" * 80)
            for type_id, stat_name in stat_type_mapping.items():
                home_val = home_stats.get(type_id, {}).get('value', 'N/A')
                away_val = away_stats.get(type_id, {}).get('value', 'N/A')
                if home_val != 'N/A' or away_val != 'N/A':
                    print(f"   {stat_name:<20} | Type ID: {type_id:<3} | Home: {home_val:<3} | Away: {away_val}")
        
        else:
            print("❌ No statistics found in API response")
            
        # Show team names for context
        participants = fixture.get('participants', [])
        if participants:
            print(f"\n👥 TEAMS:")
            for participant in participants:
                name = participant.get('name', 'Unknown')
                participant_id = participant.get('id', 'Unknown')
                meta = participant.get('meta', {})
                location = meta.get('location', 'unknown')
                print(f"   {location.upper()}: {name} (ID: {participant_id})")
            
        # Also show a sample of the raw structure
        print(f"\n📋 RAW STATISTICS STRUCTURE (first 3):")
        for i, stat in enumerate(statistics[:3]):
            print(f"   Stat {i+1}: {json.dumps(stat, indent=4)}")
    
    else:
        print("❌ No fixture data returned")
        print(f"Response: {json.dumps(fixture_data, indent=2)}")

else:
    print("❌ No live matches found") 