import os
import requests
from dotenv import load_dotenv
import json
import time

load_dotenv()

api_key = os.getenv('SPORTMONKS_API_KEY')

print("🔍 FINDING THE ACTUAL MATCH MINUTE FROM SPORTMONKS")
print("=" * 70)

# Get live matches with comprehensive includes
url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
params = {
    'api_token': api_key,
    'include': 'scores;participants;state;periods;events;league'
}

response = requests.get(url, params=params)
matches = response.json().get('data', [])

print(f"📊 Found {len(matches)} inplay matches")

# Find a live match and examine ALL fields
for i, match in enumerate(matches[:5]):
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
    
    state = match.get('state', {})
    state_short = state.get('short_name', 'Unknown')
    
    # Only examine matches that are actively playing
    if state_short in ['1H', '1st', '2H', '2nd']:
        print(f"\n🎯 LIVE MATCH: {home_team} vs {away_team}")
        print("=" * 50)
        
        # Show ALL state fields
        print("📊 COMPLETE STATE DATA:")
        for key, value in state.items():
            print(f"   {key}: {value}")
        
        # Show ALL match fields (top level)
        print("\n📊 ALL MATCH FIELDS:")
        for key in match.keys():
            if key not in ['participants', 'scores', 'periods', 'events']:
                print(f"   {key}: {match.get(key)}")
        
        # Check if periods have start times we can calculate from
        periods = match.get('periods', [])
        print(f"\n⏰ PERIOD TIMING ANALYSIS:")
        current_time = int(time.time())
        
        for j, period in enumerate(periods):
            print(f"   Period {j+1}:")
            started = period.get('started')
            ended = period.get('ended')
            
            if started:
                start_time = int(started)
                print(f"      Started: {started} ({time.ctime(start_time)})")
                
                if not ended:  # Currently active period
                    elapsed_seconds = current_time - start_time
                    elapsed_minutes = elapsed_seconds // 60
                    print(f"      🕒 CALCULATED ELAPSED: {elapsed_minutes} minutes")
                    
                    # Adjust for which half
                    if state_short in ['2H', '2nd']:
                        total_minutes = 45 + elapsed_minutes
                        print(f"      🎯 TOTAL MATCH TIME: ~{total_minutes} minutes")
                    else:
                        print(f"      🎯 1ST HALF TIME: ~{elapsed_minutes} minutes")
            
            if ended:
                end_time = int(ended)
                print(f"      Ended: {ended} ({time.ctime(end_time)})")
        
        # Check events for timing info
        events = match.get('events', [])
        if events:
            print(f"\n📝 RECENT EVENTS (for time reference):")
            for event in events[-3:]:  # Last 3 events
                event_minute = event.get('minute', 'N/A')
                event_type = event.get('type', {}).get('name', 'Unknown')
                print(f"   {event_type}: minute {event_minute}")
        
        break  # Stop after first live match

print(f"\n💡 SUGGESTIONS:")
print("=" * 30)
print("1. Use period start times + current time to calculate")
print("2. Look for minute in events data")
print("3. Check if there's a different API endpoint")
print("4. Use what SportMonks provides without calculation") 