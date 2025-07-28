import os
import requests
from dotenv import load_dotenv
from collections import defaultdict
import json

load_dotenv()
print("✅ Loaded .env file")

api_key = os.getenv('SPORTMONKS_API_KEY')

# Get multiple live matches from different leagues
url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
params = {
    'api_token': api_key,
    'include': 'scores;participants;state;events;periods;league'
}

print("🔍 Getting live matches for investigation...")
response = requests.get(url, params=params)
data = response.json()
matches = data.get('data', [])

print(f"📊 Found {len(matches)} live matches to investigate")

# Track stats across matches
stat_availability = defaultdict(int)
match_analysis = []
total_matches_tested = 0

print(f"\n🔎 INVESTIGATING STAT AVAILABILITY ACROSS MATCHES:")
print("=" * 80)

# Test up to 10 different matches
for i, match in enumerate(matches[:10]):
    match_id = match['id']
    total_matches_tested += 1
    
    # Get league info
    league_info = match.get('league', {})
    league_name = league_info.get('name', 'Unknown League')
    league_id = league_info.get('id', 'Unknown')
    
    # Get team info
    participants = match.get('participants', [])
    home_team = "Unknown"
    away_team = "Unknown"
    for participant in participants:
        meta = participant.get('meta', {})
        location = meta.get('location', 'unknown')
        if location == 'home':
            home_team = participant.get('name', 'Unknown')
        elif location == 'away':
            away_team = participant.get('name', 'Unknown')
    
    print(f"\n🔍 Match {i+1}: {home_team} vs {away_team}")
    print(f"   League: {league_name} (ID: {league_id})")
    print(f"   Match ID: {match_id}")
    
    # Get detailed fixture stats
    fixture_url = f"https://api.sportmonks.com/v3/football/fixtures/{match_id}"
    fixture_params = {
        'api_token': api_key,
        'include': 'statistics;events;scores;participants;state;periods;league'
    }
    
    fixture_response = requests.get(fixture_url, params=fixture_params)
    if fixture_response.status_code == 200:
        fixture_data = fixture_response.json()
        
        if 'data' in fixture_data:
            fixture = fixture_data['data']
            statistics = fixture.get('statistics', [])
            
            print(f"   📊 Found {len(statistics)} statistics")
            
            # Track which stats are available
            available_stat_types = set()
            for stat in statistics:
                type_id = stat.get('type_id')
                if type_id:
                    available_stat_types.add(type_id)
                    stat_availability[type_id] += 1
            
            # Check for our key missing stats
            key_missing_stats = {
                49: "Shots Inside Box",
                50: "Shots Outside Box", 
                58: "Crosses",
                45: "Ball Possession %",
                47: "Penalties"
            }
            
            found_key_stats = []
            missing_key_stats = []
            
            for type_id, name in key_missing_stats.items():
                if type_id in available_stat_types:
                    found_key_stats.append(f"{name} (ID: {type_id})")
                else:
                    missing_key_stats.append(f"{name} (ID: {type_id})")
            
            if found_key_stats:
                print(f"   ✅ Found: {', '.join(found_key_stats)}")
            if missing_key_stats:
                print(f"   ❌ Missing: {', '.join(missing_key_stats)}")
            
            # Store match analysis
            match_analysis.append({
                'match_id': match_id,
                'league': league_name,
                'league_id': league_id,
                'teams': f"{home_team} vs {away_team}",
                'total_stats': len(statistics),
                'available_types': available_stat_types,
                'has_key_stats': len(found_key_stats)
            })
            
            # Show all available stat types for first few matches
            if i < 3:
                print(f"   📋 All available types: {sorted(available_stat_types)}")
        
        else:
            print(f"   ❌ No data in fixture response")
    else:
        print(f"   ❌ API error: {fixture_response.status_code}")

# Analysis summary
print(f"\n📈 INVESTIGATION SUMMARY:")
print("=" * 80)

print(f"🔍 Tested {total_matches_tested} matches")

# Show stat availability frequency
print(f"\n📊 STAT TYPE AVAILABILITY ACROSS ALL MATCHES:")
sorted_stats = sorted(stat_availability.items(), key=lambda x: x[1], reverse=True)

print(f"   {'Type ID':<8} | {'Found in X matches':<20} | {'% Availability':<15} | {'Likely Stat'}")
print("   " + "-" * 70)

# Official mapping for reference
stat_mapping = {
    34: "Corners",
    41: "Shots Off Target", 
    42: "Shots Total",
    43: "Attacks",
    44: "Dangerous Attacks",
    45: "Ball Possession %",
    47: "Penalties",
    49: "Shots Inside Box",
    50: "Shots Outside Box", 
    51: "Offsides",
    55: "Throw Ins",
    56: "Free Kicks",
    58: "Crosses",
    84: "Big Chances Missed",
    86: "Saves (Likely)"
}

for type_id, count in sorted_stats:
    percentage = (count / total_matches_tested) * 100
    stat_name = stat_mapping.get(type_id, "Unknown")
    print(f"   {type_id:<8} | {count:<20} | {percentage:<14.1f}% | {stat_name}")

# Identify missing critical stats
print(f"\n❌ CRITICAL MISSING STATS ANALYSIS:")
critical_stats = [49, 50, 58, 45, 47]
for type_id in critical_stats:
    count = stat_availability.get(type_id, 0)
    percentage = (count / total_matches_tested) * 100 if total_matches_tested > 0 else 0
    stat_name = stat_mapping.get(type_id, f"Type {type_id}")
    
    if percentage == 0:
        print(f"   🔴 {stat_name:<20} | NEVER FOUND (0%)")
    elif percentage < 50:
        print(f"   🟠 {stat_name:<20} | RARE ({percentage:.1f}%)")
    else:
        print(f"   🟢 {stat_name:<20} | COMMON ({percentage:.1f}%)")

# League analysis
print(f"\n🏆 LEAGUE-BASED ANALYSIS:")
league_stats = defaultdict(lambda: {'matches': 0, 'total_stats': 0, 'key_stats': 0})

for analysis in match_analysis:
    league = analysis['league']
    league_stats[league]['matches'] += 1
    league_stats[league]['total_stats'] += analysis['total_stats']
    league_stats[league]['key_stats'] += analysis['has_key_stats']

print(f"   {'League':<25} | {'Matches':<8} | {'Avg Stats':<10} | {'Key Stats Found'}")
print("   " + "-" * 65)

for league, stats in league_stats.items():
    avg_stats = stats['total_stats'] / stats['matches'] if stats['matches'] > 0 else 0
    avg_key = stats['key_stats'] / stats['matches'] if stats['matches'] > 0 else 0
    print(f"   {league[:24]:<25} | {stats['matches']:<8} | {avg_stats:<10.1f} | {avg_key:.1f}")

# Recommendations
print(f"\n💡 INVESTIGATION FINDINGS & RECOMMENDATIONS:")
print("=" * 80)

# Find patterns in available vs missing stats
common_stats = [type_id for type_id, count in sorted_stats if count >= total_matches_tested * 0.5]
rare_stats = [type_id for type_id, count in sorted_stats if count < total_matches_tested * 0.3]

print(f"🟢 CONSISTENTLY AVAILABLE STATS: {common_stats}")
print(f"🔴 RARELY AVAILABLE STATS: {rare_stats}")

# Check if missing stats might have different IDs
print(f"\n🔍 POSSIBLE ALTERNATIVE TYPE IDs TO INVESTIGATE:")
all_found_types = set()
for analysis in match_analysis:
    all_found_types.update(analysis['available_types'])

unknown_types = sorted([t for t in all_found_types if t not in stat_mapping])
if unknown_types:
    print(f"   Unknown types found: {unknown_types}")
    print(f"   ^^^ These might be our missing stats with different IDs!")
else:
    print(f"   No unknown types found - missing stats may require different API endpoints")

print(f"\n🚀 NEXT STEPS:")
print(f"   1. Test different API includes (e.g., 'statistics.type', 'detailed_events')")
print(f"   2. Check if missing stats are league/competition specific")
print(f"   3. Investigate alternative endpoints for detailed match stats")
print(f"   4. Test with finished matches vs live matches")
print(f"   5. Check if stat availability depends on match importance/level") 