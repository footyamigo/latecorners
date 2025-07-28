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
            print("=" * 60)
            
            # Group by participant (home/away)
            home_stats = {}
            away_stats = {}
            
            for stat in statistics:
                participant = stat.get('participant', 'unknown')
                stat_type = stat.get('type', {})
                stat_name = stat_type.get('name', 'Unknown')
                stat_id = stat_type.get('id', 'Unknown')
                stat_code = stat_type.get('code', 'Unknown')
                value = stat.get('value', 0)
                
                stat_info = {
                    'name': stat_name,
                    'id': stat_id,
                    'code': stat_code,
                    'value': value
                }
                
                if participant == 'home':
                    home_stats[stat_name] = stat_info
                elif participant == 'away':
                    away_stats[stat_name] = stat_info
            
            print("\n🏠 HOME TEAM STATISTICS:")
            for stat_name, info in home_stats.items():
                print(f"   {info['name']:<25} | ID: {info['id']:<3} | Code: {info['code']:<20} | Value: {info['value']}")
            
            print("\n🏃 AWAY TEAM STATISTICS:")  
            for stat_name, info in away_stats.items():
                print(f"   {info['name']:<25} | ID: {info['id']:<3} | Code: {info['code']:<20} | Value: {info['value']}")
            
            # Show key stats for our corner system
            print("\n🎯 KEY STATS FOR LATE CORNER SYSTEM:")
            print("=" * 60)
            
            key_stats = [
                'Corners', 'Corner Kicks', 'Shots Total', 'Shots on Goal', 
                'Dangerous Attacks', 'Attacks', 'Yellow Cards', 'Red Cards',
                'Shots Blocked', 'Big Chances Created', 'Big Chances Missed'
            ]
            
            for key_stat in key_stats:
                home_val = home_stats.get(key_stat, {}).get('value', 'N/A')
                away_val = away_stats.get(key_stat, {}).get('value', 'N/A')
                stat_id = home_stats.get(key_stat, {}).get('id', 'N/A')
                print(f"   {key_stat:<20} | ID: {stat_id:<3} | Home: {home_val:<3} | Away: {away_val}")
        
        else:
            print("❌ No statistics found in API response")
            
        # Also show a sample of the raw structure
        print(f"\n📋 RAW STATISTICS STRUCTURE (first 3):")
        for i, stat in enumerate(statistics[:3]):
            print(f"   Stat {i+1}: {json.dumps(stat, indent=4)}")
    
    else:
        print("❌ No fixture data returned")
        print(f"Response: {json.dumps(fixture_data, indent=2)}")

else:
    print("❌ No live matches found") 