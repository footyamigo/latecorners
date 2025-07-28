import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

api_key = os.getenv('SPORTMONKS_API_KEY')

print("🔍 CHECKING SPORTMONKS ACTUAL TIME DATA")
print("=" * 60)

# Get live matches
url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
params = {
    'api_token': api_key,
    'include': 'scores;participants;state;periods'
}

response = requests.get(url, params=params)
matches = response.json().get('data', [])

print(f"📊 Found {len(matches)} inplay matches")
print("\n🕒 TIME DATA ANALYSIS:")
print("=" * 50)

for i, match in enumerate(matches[:10]):  # Check first 10 matches
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
    state_name = state.get('name', 'Unknown')
    state_short = state.get('short_name', 'Unknown')
    state_minute = state.get('minute', 'N/A')  # Direct from state
    
    print(f"\n{i+1:2d}. {home_team} vs {away_team}")
    print(f"    State: {state_name} ({state_short})")
    print(f"    State Minute: {state_minute}")
    
    # Get periods data
    periods = match.get('periods', [])
    print(f"    Periods Count: {len(periods)}")
    
    for j, period in enumerate(periods):
        print(f"    Period {j+1}:")
        print(f"      Name: {period.get('name', 'Unknown')}")
        print(f"      Minute: {period.get('minute', 'N/A')}")
        print(f"      Is Current: {period.get('is_current', False)}")
        print(f"      Started: {period.get('started', 'N/A')}")
        print(f"      Ended: {period.get('ended', 'N/A')}")
    
    # Show only matches that are actually playing
    if state_short in ['1H', '1st', '2H', '2nd'] and periods:
        print(f"    🎯 PLAYING MATCH - What time should we use?")
        print(f"       State minute: {state_minute}")
        
        current_period = None
        for period in periods:
            if period.get('is_current', False):
                current_period = period
                break
        
        if current_period:
            period_minute = current_period.get('minute', 'N/A')
            print(f"       Current period minute: {period_minute}")
            print(f"       🤔 Which is correct?")

print(f"\n💡 WHAT TIME SHOULD WE USE?")
print("=" * 40)
print("Option 1: state.minute (direct from match state)")
print("Option 2: current_period.minute (from periods)")
print("Option 3: Some combination/calculation")
print("\nLet's see which makes more sense...") 