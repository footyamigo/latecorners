import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()
print("✅ Loaded .env file")

api_key = os.getenv('SPORTMONKS_API_KEY')

# First, try to get stat type definitions directly
print("🔍 TRYING TO GET STAT TYPE DEFINITIONS:")
print("=" * 80)

# Test different endpoints for stat types
stat_type_endpoints = [
    'https://api.sportmonks.com/v3/football/types',
    'https://api.sportmonks.com/v3/football/types/statistics',
    'https://api.sportmonks.com/v3/core/types',
    'https://api.sportmonks.com/v3/core/types/statistics'
]

for endpoint in stat_type_endpoints:
    print(f"\n🔍 Testing endpoint: {endpoint}")
    
    try:
        response = requests.get(endpoint, params={'api_token': api_key})
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                types = data['data']
                print(f"   ✅ Found {len(types)} type definitions")
                
                # Look for statistics-related types
                stat_types = []
                for type_def in types[:10]:  # Check first 10
                    if isinstance(type_def, dict):
                        name = type_def.get('name', '')
                        code = type_def.get('code', '')
                        if 'stat' in name.lower() or 'shot' in name.lower() or 'corner' in name.lower():
                            stat_types.append(type_def)
                
                if stat_types:
                    print(f"   🎯 Found stat-related types:")
                    for stat_type in stat_types:
                        print(f"      {stat_type}")
                else:
                    print(f"   📋 Sample types:")
                    for type_def in types[:3]:
                        print(f"      {type_def}")
            else:
                print(f"   ❌ No data in response")
        else:
            print(f"   ❌ Failed with status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

# Now test with higher-tier leagues  
print(f"\n🏆 TESTING WITH HIGHER-TIER LEAGUES:")
print("=" * 80)

# Get matches from all leagues
url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
params = {
    'api_token': api_key,
    'include': 'scores;participants;state;events;periods;league'
}

response = requests.get(url, params=params)
data = response.json()
matches = data.get('data', [])

# Filter for major leagues (approximate IDs - need to verify)
major_league_names = [
    'Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1',
    'Champions League', 'Europa League', 'Championship', 'MLS',
    'Primeira Liga', 'Eredivisie'
]

major_league_matches = []
for match in matches:
    league_info = match.get('league', {})
    league_name = league_info.get('name', '')
    
    for major_name in major_league_names:
        if major_name.lower() in league_name.lower():
            major_league_matches.append(match)
            break

print(f"📊 Found {len(major_league_matches)} matches from major leagues")

if major_league_matches:
    print(f"\n🔍 ANALYZING MAJOR LEAGUE MATCHES:")
    
    for i, match in enumerate(major_league_matches[:3]):  # Test top 3
        match_id = match['id']
        league_info = match.get('league', {})
        league_name = league_info.get('name', 'Unknown')
        
        # Get team names
        participants = match.get('participants', [])
        teams = []
        for participant in participants:
            teams.append(participant.get('name', 'Unknown'))
        
        print(f"\n🏆 Match {i+1}: {' vs '.join(teams)}")
        print(f"   League: {league_name}")
        print(f"   Match ID: {match_id}")
        
        # Get comprehensive stats
        fixture_url = f"https://api.sportmonks.com/v3/football/fixtures/{match_id}"
        fixture_params = {
            'api_token': api_key,
            'include': 'statistics;events.type'
        }
        
        fixture_response = requests.get(fixture_url, params=fixture_params)
        if fixture_response.status_code == 200:
            fixture_data = fixture_response.json()
            
            if 'data' in fixture_data:
                fixture = fixture_data['data']
                statistics = fixture.get('statistics', [])
                events = fixture.get('events', [])
                
                print(f"   📊 Statistics: {len(statistics)}")
                print(f"   📊 Events: {len(events)}")
                
                # Analyze stat types
                stat_types = set()
                for stat in statistics:
                    stat_types.add(stat.get('type_id'))
                
                print(f"   📊 Unique stat types: {sorted(stat_types)}")
                
                # Check for our key missing stats
                key_stats_check = {
                    49: "Shots Inside Box",
                    50: "Shots Outside Box",
                    58: "Crosses", 
                    47: "Penalties"
                }
                
                found_key = []
                for type_id, name in key_stats_check.items():
                    if type_id in stat_types:
                        found_key.append(f"{name} ({type_id})")
                
                if found_key:
                    print(f"   ✅ FOUND KEY STATS: {', '.join(found_key)}")
                else:
                    print(f"   ❌ Still missing key stats")
                
                # Analyze events for shot location data
                shot_events = []
                corner_events = []
                
                for event in events:
                    event_type = event.get('type', {})
                    if isinstance(event_type, dict):
                        type_name = event_type.get('name', '').lower()
                        if 'shot' in type_name or 'attempt' in type_name:
                            shot_events.append(event)
                        elif 'corner' in type_name:
                            corner_events.append(event)
                
                print(f"   🎯 Shot events: {len(shot_events)}")
                print(f"   🏁 Corner events: {len(corner_events)}")
                
                if shot_events:
                    print(f"   📋 Sample shot event structure:")
                    sample_shot = shot_events[0]
                    print(f"      Type: {sample_shot.get('type', {})}")
                    print(f"      Details: {sample_shot.get('details', {})}")
        else:
            print(f"   ❌ Failed to get fixture data: {fixture_response.status_code}")

else:
    print(f"❌ No major league matches currently live")
    
    # Test with any available match but use different includes
    print(f"\n🔍 TESTING ALTERNATIVE INCLUDES WITH AVAILABLE MATCHES:")
    
    if matches:
        test_match = matches[0]
        match_id = test_match['id']
        
        alternative_includes = [
            'statistics.type;events.type.detail',
            'detailed_events;statistics.extended',
            'lineups;statistics;events.extra',
            'benchmarks;statistics.advanced'
        ]
        
        for include_param in alternative_includes:
            print(f"\n🔍 Testing include: '{include_param}'")
            
            fixture_url = f"https://api.sportmonks.com/v3/football/fixtures/{match_id}"
            fixture_params = {
                'api_token': api_key,
                'include': include_param
            }
            
            try:
                fixture_response = requests.get(fixture_url, params=fixture_params)
                print(f"   Status: {fixture_response.status_code}")
                
                if fixture_response.status_code == 200:
                    fixture_data = fixture_response.json()
                    if 'data' in fixture_data:
                        fixture = fixture_data['data']
                        statistics = fixture.get('statistics', [])
                        
                        if statistics:
                            sample_stat = statistics[0]
                            if 'type' in sample_stat:
                                print(f"   ✅ SUCCESS! Got stat type object:")
                                type_obj = sample_stat['type']
                                print(f"      {type_obj}")
                                break
                            else:
                                print(f"   ❌ Still no type object")
                        else:
                            print(f"   ❌ No statistics in response")
                else:
                    print(f"   ❌ Request failed")
            except Exception as e:
                print(f"   ❌ Error: {e}")

print(f"\n💡 FINAL RECOMMENDATIONS:")
print("=" * 80)
print(f"1. 🎯 Focus on Type 54 (values 3-5) as likely Shots Inside Box")
print(f"2. 🎯 Focus on Type 52 (values 0-1) as likely Penalties/Cards") 
print(f"3. 📊 Use events data to calculate shot locations manually")
print(f"4. 🏆 Target matches from major leagues for better stat coverage")
print(f"5. 🔍 Investigate if different API tiers provide more detailed stats") 