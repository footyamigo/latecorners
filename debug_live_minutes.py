import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('SPORTMONKS_API_KEY')

print("🔍 DEBUGGING MINUTE EXTRACTION FOR LIVE MATCHES")
print("=" * 60)

url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
params = {
    'api_token': api_key,
    'include': 'scores;participants;state;events;periods'
}

response = requests.get(url, params=params)
matches = response.json().get('data', [])

print(f"📊 Found {len(matches)} total matches")
print()

live_matches_found = 0

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
    
    # Get state
    state = match.get('state', {})
    state_short = state.get('short_name', 'Unknown')
    
    # Only debug actively playing matches
    if state_short in ['1H', '1st', '2H', '2nd']:
        live_matches_found += 1
        
        if live_matches_found <= 5:  # Debug first 5 live matches
            print(f"🎯 LIVE MATCH {live_matches_found}: {home_team} vs {away_team}")
            print(f"   State: {state.get('name', 'Unknown')} ({state_short})")
            
            # Method 1: Check direct minute field
            direct_minute = match.get('minute', 'NOT_FOUND')
            print(f"   📊 Direct 'minute' field: {direct_minute}")
            
            # Method 2: Check state minute
            state_minute = state.get('minute', 'NOT_FOUND')
            print(f"   📊 State 'minute' field: {state_minute}")
            
            # Method 3: Check periods for ticking and minutes
            periods = match.get('periods', [])
            print(f"   📊 Periods ({len(periods)} total):")
            
            active_period_minute = None
            
            for i, period in enumerate(periods):
                ticking = period.get('ticking', False)
                minutes = period.get('minutes', 'NOT_FOUND')
                description = period.get('description', 'Unknown')
                
                print(f"      Period {i+1}: {description}")
                print(f"        - minutes: {minutes}")
                print(f"        - ticking: {ticking}")
                
                if ticking and minutes != 'NOT_FOUND':
                    active_period_minute = minutes
                    print(f"        ✅ ACTIVE PERIOD with minute: {minutes}")
            
            # Method 4: Check if our extraction function works
            extracted_minute = extract_proper_minute(match)
            print(f"   🎯 EXTRACTED MINUTE: {extracted_minute}")
            print()

print(f"\n📊 SUMMARY: Found {live_matches_found} actively playing matches")

def extract_proper_minute(match):
    """Proper minute extraction based on SportMonks data structure"""
    
    # Method 1: Try direct minute field
    direct_minute = match.get('minute')
    if direct_minute and direct_minute != 0:
        return direct_minute
    
    # Method 2: Try state minute
    state = match.get('state', {})
    state_minute = state.get('minute')
    if state_minute and state_minute != 0:
        return state_minute
    
    # Method 3: Use periods with ticking flag
    periods = match.get('periods', [])
    for period in periods:
        if period.get('ticking', False):
            period_minute = period.get('minutes', 0)
            description = period.get('description', '').lower()
            
            # Add 45 for second half
            if '2nd' in description or 'second' in description:
                return period_minute + 45
            else:
                return period_minute
    
    # Fallback: return 0
    return 0 