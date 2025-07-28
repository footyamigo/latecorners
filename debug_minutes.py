import os
import requests
from dotenv import load_dotenv

load_dotenv()
print("✅ Loaded .env file")

api_key = os.getenv('SPORTMONKS_API_KEY')
url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
params = {
    'api_token': api_key,
    'include': 'scores;participants;state;events;periods'
}

print("🔍 Getting live matches to debug minutes...")

response = requests.get(url, params=params)
data = response.json()
matches = data.get('data', [])

print(f"📊 Found {len(matches)} matches")

for match in matches:
    # Get team names
    participants = match.get('participants', [])
    home_team = "Unknown"
    away_team = "Unknown"
    
    for participant in participants:
        location = participant.get('meta', {}).get('location')
        if location == 'home':
            home_team = participant.get('name', 'Unknown')
        elif location == 'away':
            away_team = participant.get('name', 'Unknown')
    
    match_name = f"{home_team} vs {away_team}"
    
    # Focus on the problematic matches
    if "Zhenys" in match_name or "Okzhetpes" in match_name or "ABFF" in match_name:
        print(f"\n🎯 DEBUGGING: {match_name}")
        
        # Check direct minute field
        direct_minute = match.get('minute', 'N/A')
        print(f"   Direct 'minute' field: {direct_minute}")
        
        # Check periods
        periods = match.get('periods', [])
        print(f"   Periods count: {len(periods)}")
        
        for i, period in enumerate(periods):
            minutes = period.get('minutes', 'N/A')
            ticking = period.get('ticking', False)
            description = period.get('description', 'N/A')
            print(f"   Period {i+1}: {description}, minutes={minutes}, ticking={ticking}")
        
        # Get state
        state = match.get('state', {})
        state_name = state.get('developer_name', state.get('short_name', 'N/A'))
        print(f"   State: {state_name}") 