import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()
print("✅ Loaded .env file")

api_key = os.getenv('SPORTMONKS_API_KEY')

# Test with different API approaches
print("🔍 DECODING UNKNOWN STAT TYPE IDs:")
print("=" * 80)

# First, let's get a match with comprehensive stats
url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
params = {
    'api_token': api_key,
    'include': 'scores;participants;state;events;periods;league'
}

response = requests.get(url, params=params)
data = response.json()
matches = data.get('data', [])

# Find a match with the most statistics
best_match = None
max_stats = 0

for match in matches[:10]:
    match_id = match['id']
    
    fixture_url = f"https://api.sportmonks.com/v3/football/fixtures/{match_id}"
    fixture_params = {
        'api_token': api_key,
        'include': 'statistics'
    }
    
    fixture_response = requests.get(fixture_url, params=fixture_params)
    if fixture_response.status_code == 200:
        fixture_data = fixture_response.json()
        if 'data' in fixture_data:
            statistics = fixture_data['data'].get('statistics', [])
            if len(statistics) > max_stats:
                max_stats = len(statistics)
                best_match = match

if best_match:
    print(f"📊 Using match with most stats: {best_match['id']} ({max_stats} statistics)")
    
    # Test different include parameters
    include_variations = [
        'statistics',
        'statistics.type',
        'statistics;events',
        'statistics;detailed_statistics',
        'detailed_events',
        'statistics;lineups',
        'events;statistics'
    ]
    
    for include_param in include_variations:
        print(f"\n🔍 Testing include parameter: '{include_param}'")
        
        fixture_url = f"https://api.sportmonks.com/v3/football/fixtures/{best_match['id']}"
        fixture_params = {
            'api_token': api_key,
            'include': include_param
        }
        
        try:
            fixture_response = requests.get(fixture_url, params=fixture_params)
            if fixture_response.status_code == 200:
                fixture_data = fixture_response.json()
                if 'data' in fixture_data:
                    fixture = fixture_data['data']
                    statistics = fixture.get('statistics', [])
                    
                    print(f"   📈 Found {len(statistics)} statistics")
                    
                    # Check if we got type names
                    sample_stat = statistics[0] if statistics else None
                    if sample_stat:
                        if 'type' in sample_stat:
                            print(f"   ✅ Has 'type' object: {sample_stat['type']}")
                        else:
                            print(f"   ❌ No 'type' object, only type_id: {sample_stat.get('type_id')}")
                        
                        # Show structure
                        print(f"   📋 Sample stat structure: {json.dumps(sample_stat, indent=6)}")
                        break
            else:
                print(f"   ❌ API error: {fixture_response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Now analyze the unknown type IDs from our best match
    print(f"\n🔍 ANALYZING UNKNOWN TYPE IDs IN BEST MATCH:")
    print("=" * 80)
    
    fixture_url = f"https://api.sportmonks.com/v3/football/fixtures/{best_match['id']}"
    fixture_params = {
        'api_token': api_key,
        'include': 'statistics'
    }
    
    fixture_response = requests.get(fixture_url, params=fixture_params)
    if fixture_response.status_code == 200:
        fixture_data = fixture_response.json()
        fixture = fixture_data['data']
        statistics = fixture.get('statistics', [])
        
        # Group by type_id and analyze values
        type_analysis = {}
        for stat in statistics:
            type_id = stat.get('type_id')
            value = stat.get('data', {}).get('value', 0)
            location = stat.get('location', 'unknown')
            
            if type_id not in type_analysis:
                type_analysis[type_id] = {'values': [], 'locations': []}
            
            type_analysis[type_id]['values'].append(value)
            type_analysis[type_id]['locations'].append(location)
        
        # Known stats for reference
        known_stats = {
            34: "Corners",
            41: "Shots Off Target",
            42: "Shots Total", 
            43: "Attacks",
            44: "Dangerous Attacks",
            45: "Ball Possession %",
            51: "Offsides",
            55: "Throw Ins",
            56: "Free Kicks",
            84: "Big Chances Missed",
            86: "Saves (Likely)"
        }
        
        # Analyze unknown types
        unknown_types = [46, 52, 54, 59, 64, 82, 98, 117]
        
        for type_id in sorted(type_analysis.keys()):
            values = type_analysis[type_id]['values']
            locations = type_analysis[type_id]['locations']
            
            min_val = min(values)
            max_val = max(values)
            avg_val = sum(values) / len(values)
            
            stat_name = known_stats.get(type_id, "UNKNOWN")
            
            print(f"Type {type_id:3d}: {stat_name:<20} | Values: {min_val:2d}-{max_val:2d} (avg: {avg_val:4.1f}) | Locations: {set(locations)}")
            
            # Try to guess what unknown stats might be based on value patterns
            if type_id in unknown_types:
                print(f"       🔍 ANALYSIS: ", end="")
                
                if max_val <= 15 and avg_val <= 8:
                    print("Could be SHOTS INSIDE/OUTSIDE BOX (typical range)")
                elif max_val <= 5 and avg_val <= 2:
                    print("Could be PENALTIES or CARDS (low frequency)")
                elif max_val <= 30 and avg_val <= 15:
                    print("Could be CROSSES or FOULS (medium frequency)")
                elif max_val >= 50:
                    print("Could be POSSESSION related (high values)")
                else:
                    print("Unknown pattern")

# Test with alternative API endpoints
print(f"\n🔍 TESTING ALTERNATIVE API ENDPOINTS:")
print("=" * 80)

if best_match:
    # Test events endpoint for shot location data
    print(f"\n🎯 Testing EVENTS endpoint for shot details:")
    
    events_url = f"https://api.sportmonks.com/v3/football/fixtures/{best_match['id']}"
    events_params = {
        'api_token': api_key,
        'include': 'events.type;events.participant;events.player'
    }
    
    events_response = requests.get(events_url, params=events_params)
    if events_response.status_code == 200:
        events_data = events_response.json()
        if 'data' in events_data:
            fixture = events_data['data']
            events = fixture.get('events', [])
            
            print(f"   📊 Found {len(events)} events")
            
            # Look for shot-related events
            shot_events = []
            for event in events:
                event_type = event.get('type', {})
                type_name = event_type.get('name', '') if isinstance(event_type, dict) else str(event_type)
                
                if 'shot' in type_name.lower() or 'attempt' in type_name.lower():
                    shot_events.append(event)
            
            print(f"   🎯 Found {len(shot_events)} shot-related events")
            
            if shot_events:
                print(f"   📋 Sample shot event:")
                print(json.dumps(shot_events[0], indent=6))
    
    # Test with more detailed includes
    print(f"\n🔬 Testing MAXIMUM DETAIL includes:")
    
    max_detail_url = f"https://api.sportmonks.com/v3/football/fixtures/{best_match['id']}"
    max_detail_params = {
        'api_token': api_key,
        'include': 'statistics.type;events.type;participants;scores;state;periods;lineups;benchmarks'
    }
    
    max_response = requests.get(max_detail_url, params=max_detail_params)
    if max_response.status_code == 200:
        max_data = max_response.json()
        if 'data' in max_data:
            print(f"   ✅ Maximum detail request successful")
            fixture = max_data['data']
            
            # Check if we now have type names
            statistics = fixture.get('statistics', [])
            if statistics and 'type' in statistics[0]:
                print(f"   🎉 SUCCESS! Now have stat type names:")
                for stat in statistics[:5]:
                    type_info = stat.get('type', {})
                    type_name = type_info.get('name', 'Unknown')
                    type_id = stat.get('type_id', 'Unknown')
                    value = stat.get('data', {}).get('value', 0)
                    location = stat.get('location', 'Unknown')
                    print(f"      Type {type_id}: {type_name} = {value} ({location})")
            else:
                print(f"   ❌ Still no type names available")
    else:
        print(f"   ❌ Maximum detail request failed: {max_response.status_code}")

print(f"\n💡 RECOMMENDATIONS:")
print("=" * 80)
print(f"1. 🔍 Investigate Type IDs that might be our missing stats")
print(f"2. 🎯 Use events endpoint to get shot location data") 
print(f"3. 🏆 Test with higher-tier leagues (EPL, La Liga, etc.)")
print(f"4. 📊 Focus on leagues with comprehensive stat coverage")
print(f"5. 🔬 Try statistics.type include to get stat names") 