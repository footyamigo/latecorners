import os
import requests
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

api_key = os.getenv('SPORTMONKS_API_KEY')

print("🔍 ANALYZING ACTUAL MATCH STATES")
print("=" * 60)

# Get "inplay" matches
url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
params = {
    'api_token': api_key,
    'include': 'scores;participants;state;events;periods'
}

response = requests.get(url, params=params)
if response.status_code != 200:
    print(f"❌ API Error: {response.status_code}")
    exit()

matches = response.json().get('data', [])
print(f"📊 API returned {len(matches)} 'inplay' matches")
print()

# Analyze states
state_counts = defaultdict(int)
state_details = defaultdict(list)

truly_live = []
not_live = []

for i, match in enumerate(matches):
    match_id = match['id']
    
    # Get team names
    participants = match.get('participants', [])
    home_team = "Unknown"
    away_team = "Unknown"
    
    for participant in participants:
        meta = participant.get('meta', {})
        location = meta.get('location', 'unknown')
        name = participant.get('name', 'Unknown')
        
        if location == 'home':
            home_team = name
        elif location == 'away':
            away_team = name
    
    # Get state info
    state = match.get('state', {})
    state_id = state.get('id', 'unknown')
    state_name = state.get('name', 'unknown')
    state_short = state.get('short_name', 'unknown')
    minute = state.get('minute', 0)
    
    # Get current score
    scores = match.get('scores', [])
    home_score = 0
    away_score = 0
    
    for score_entry in scores:
        if score_entry.get('description') == 'CURRENT':
            score_data = score_entry.get('score', {})
            goals = score_data.get('goals', 0)
            participant = score_data.get('participant', '')
            
            if participant == 'home':
                home_score = goals
            elif participant == 'away':
                away_score = goals
    
    # Count states
    state_key = f"{state_name} ({state_short})"
    state_counts[state_key] += 1
    
    match_info = {
        'teams': f"{home_team} vs {away_team}",
        'score': f"{home_score}-{away_score}",
        'minute': minute,
        'state_id': state_id,
        'state_name': state_name,
        'short_name': state_short
    }
    
    state_details[state_key].append(match_info)
    
    # Determine if truly live
    # States that indicate active play: 
    # - "1st Half" 
    # - "2nd Half"
    # - "Extra Time 1st Half"
    # - "Extra Time 2nd Half"
    if state_short in ['1H', '2H', 'ET1', 'ET2'] and minute > 0:
        truly_live.append(match_info)
    else:
        not_live.append(match_info)

print("📊 STATE BREAKDOWN:")
print("-" * 40)

for state, count in sorted(state_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"   {state}: {count} matches")

print(f"\n🔍 DETAILED ANALYSIS:")
print("-" * 40)

print(f"✅ TRULY LIVE (actively playing): {len(truly_live)}")
for match in truly_live[:10]:  # Show first 10
    print(f"   ⚽ {match['teams']} | {match['score']} | {match['minute']}' | {match['short_name']}")

print(f"\n❌ NOT ACTUALLY LIVE: {len(not_live)}")

# Group not-live by state
not_live_by_state = defaultdict(list)
for match in not_live:
    state_key = f"{match['state_name']} ({match['short_name']})"
    not_live_by_state[state_key].append(match)

for state, matches in not_live_by_state.items():
    print(f"\n   📋 {state}: {len(matches)} matches")
    for match in matches[:3]:  # Show first 3 examples
        print(f"      {match['teams']} | {match['score']} | {match['minute']}'")
    if len(matches) > 3:
        print(f"      ... and {len(matches) - 3} more")

print(f"\n🎯 SUMMARY:")
print("-" * 40)
print(f"Total 'inplay' matches: {len(matches)}")
print(f"Actually live and playing: {len(truly_live)}")
print(f"Not actually live: {len(not_live)}")
print(f"Percentage truly live: {len(truly_live)/len(matches)*100:.1f}%")

if truly_live:
    print(f"\n✅ RECOMMENDATION: Filter for states: 1H, 2H, ET1, ET2 with minute > 0") 