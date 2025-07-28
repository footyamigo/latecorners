import os
import requests
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

api_key = os.getenv('SPORTMONKS_API_KEY')

print("🔍 EXTRACTING ACTUAL LIVE MATCH TIMES FROM PERIODS")
print("=" * 70)

# Get "inplay" matches
url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
params = {
    'api_token': api_key,
    'include': 'scores;participants;state;periods'
}

response = requests.get(url, params=params)
if response.status_code != 200:
    print(f"❌ API Error: {response.status_code}")
    exit()

matches = response.json().get('data', [])
print(f"📊 Found {len(matches)} inplay matches")
print()

def extract_match_minute(periods, state_short):
    """Extract actual match minute from periods data"""
    
    if not periods:
        return 0
    
    # Find the current period
    current_period = None
    for period in periods:
        if period.get('is_current', False):
            current_period = period
            break
    
    if not current_period:
        # If no current period, try to find the latest one
        current_period = periods[-1] if periods else None
    
    if not current_period:
        return 0
    
    # Extract minute from current period
    minute = current_period.get('minute', 0)
    
    # For 2nd half, add 45 minutes
    if state_short == '2H' or state_short == '2nd':
        minute += 45
    
    return minute

# Analyze live matches with proper timing
truly_live = []
halftime_matches = []
not_started = []
finished = []

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
    state_name = state.get('name', 'unknown')
    state_short = state.get('short_name', 'unknown')
    
    # Get periods and extract actual minute
    periods = match.get('periods', [])
    actual_minute = extract_match_minute(periods, state_short)
    
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
    
    match_info = {
        'match_id': match_id,
        'teams': f"{home_team} vs {away_team}",
        'score': f"{home_score}-{away_score}",
        'minute': actual_minute,
        'state_name': state_name,
        'state_short': state_short,
        'periods': periods
    }
    
    # Categorize matches
    if state_short in ['1H', '1st'] and actual_minute > 0:
        truly_live.append(match_info)
    elif state_short in ['2H', '2nd'] and actual_minute > 45:
        truly_live.append(match_info)
    elif state_short in ['HT']:
        halftime_matches.append(match_info)
    elif state_short in ['NS']:
        not_started.append(match_info)
    elif state_short in ['FT']:
        finished.append(match_info)
    else:
        # Check periods for more details
        if actual_minute > 0:
            truly_live.append(match_info)

print(f"⚽ TRULY LIVE MATCHES (actively playing): {len(truly_live)}")
print("=" * 50)

for i, match in enumerate(truly_live[:10]):  # Show first 10
    print(f"{i+1:2d}. {match['teams']}")
    print(f"    Score: {match['score']} | Minute: {match['minute']}' | State: {match['state_short']}")
    
    # Show periods details for verification
    if match['periods']:
        current_period = None
        for period in match['periods']:
            if period.get('is_current', False):
                current_period = period
                break
        
        if current_period:
            print(f"    Period: {current_period.get('name', 'Unknown')} | Period Minute: {current_period.get('minute', 0)}")
    print()

print(f"⏸️ HALFTIME MATCHES: {len(halftime_matches)}")
for match in halftime_matches[:3]:  # Show first 3
    print(f"   {match['teams']} | {match['score']} | {match['state_short']}")

print(f"\n⏳ NOT STARTED: {len(not_started)}")
print(f"✅ FINISHED: {len(finished)}")

print(f"\n🎯 SUMMARY:")
print("-" * 30)
print(f"Total inplay matches: {len(matches)}")
print(f"Actually live & playing: {len(truly_live)}")
print(f"Halftime breaks: {len(halftime_matches)}")
print(f"Not started: {len(not_started)}")
print(f"Finished: {len(finished)}")

if truly_live:
    print(f"\n🔥 WE HAVE {len(truly_live)} TRULY LIVE MATCHES FOR CORNER BETTING!")
else:
    print(f"\n❌ No truly live matches found at this moment") 