import os
import requests
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()
print("✅ Loaded .env file")

api_key = os.getenv('SPORTMONKS_API_KEY')

# Get multiple live matches
url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
params = {
    'api_token': api_key,
    'include': 'scores;participants;state;events;periods'
}

print("🔍 Getting live matches...")
response = requests.get(url, params=params)
data = response.json()
matches = data.get('data', [])

print(f"📊 Found {len(matches)} live matches")

# Test multiple matches to discover stat types
stat_type_frequency = defaultdict(int)
stat_type_values = defaultdict(list)

print("\n📈 Analyzing statistics across multiple matches...")

for i, match in enumerate(matches[:5]):  # Test first 5 matches
    match_id = match['id']
    print(f"\n  🔍 Match {i+1}: ID {match_id}")
    
    # Get detailed fixture stats
    fixture_url = f"https://api.sportmonks.com/v3/football/fixtures/{match_id}"
    fixture_params = {
        'api_token': api_key,
        'include': 'statistics'
    }
    
    fixture_response = requests.get(fixture_url, params=fixture_params)
    if fixture_response.status_code == 200:
        fixture_data = fixture_response.json()
        
        if 'data' in fixture_data:
            fixture = fixture_data['data']
            statistics = fixture.get('statistics', [])
            
            print(f"    📊 Found {len(statistics)} stats")
            
            for stat in statistics:
                type_id = stat.get('type_id')
                value = stat.get('data', {}).get('value', 0)
                location = stat.get('location', 'unknown')
                
                if type_id:
                    stat_type_frequency[type_id] += 1
                    stat_type_values[type_id].append((value, location, match_id))

print(f"\n🎯 DISCOVERED STAT TYPES (across {len(matches[:5])} matches):")
print("=" * 80)

# Sort by frequency to see most common stats
sorted_stats = sorted(stat_type_frequency.items(), key=lambda x: x[1], reverse=True)

for type_id, frequency in sorted_stats:
    values = stat_type_values[type_id]
    max_val = max(v[0] for v in values)
    min_val = min(v[0] for v in values)
    
    print(f"Type ID {type_id:2d}: Found in {frequency} entries | Values: {min_val}-{max_val}")
    
    # Show sample values to help identify the stat
    sample_values = values[:6]  # First 6 examples
    print(f"           Samples: {[(v[0], v[1]) for v in sample_values]}")

print(f"\n🔍 POTENTIAL CORNER/SHOT CANDIDATES:")
print("=" * 80)

# Look for patterns that might indicate corners/shots
corner_candidates = []
shot_candidates = []

for type_id, frequency in sorted_stats:
    values = [v[0] for v in stat_type_values[type_id]]
    max_val = max(values)
    avg_val = sum(values) / len(values)
    
    # Corners typically: low values (0-15), integer
    if max_val <= 20 and avg_val <= 10:
        corner_candidates.append((type_id, max_val, avg_val, frequency))
    
    # Shots typically: medium values (0-30), integer  
    if max_val <= 50 and avg_val <= 15:
        shot_candidates.append((type_id, max_val, avg_val, frequency))

print("\n🎯 CORNER CANDIDATES (max ≤ 20, avg ≤ 10):")
for type_id, max_val, avg_val, freq in corner_candidates:
    print(f"   Type ID {type_id:2d}: max={max_val:2.0f}, avg={avg_val:4.1f}, freq={freq}")

print("\n🏃 SHOT CANDIDATES (max ≤ 50, avg ≤ 15):")  
for type_id, max_val, avg_val, freq in shot_candidates:
    print(f"   Type ID {type_id:2d}: max={max_val:2.0f}, avg={avg_val:4.1f}, freq={freq}")

# Show raw data for top candidates
print(f"\n📋 RAW DATA FOR TOP CANDIDATES:")
print("=" * 80)

top_candidates = [t[0] for t in sorted_stats[:10]]
for type_id in top_candidates:
    print(f"\nType ID {type_id}:")
    values = stat_type_values[type_id][:10]  # First 10 examples
    for value, location, match_id in values:
        print(f"   {value:3d} ({location:4s}) - Match {match_id}") 