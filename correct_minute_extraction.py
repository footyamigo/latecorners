import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_correct_match_minute(match):
    """Extract the correct match minute from SportMonks data"""
    
    # Method 1: Check periods for the ticking (active) period
    periods = match.get('periods', [])
    for period in periods:
        if period.get('ticking', False):
            # SportMonks gives us the total match minute directly!
            return period.get('minutes', 0)
    
    # Method 2: Try direct minute field (fallback)
    direct_minute = match.get('minute')
    if direct_minute and direct_minute != 0:
        return direct_minute
    
    # Method 3: Try state minute (fallback)
    state = match.get('state', {})
    state_minute = state.get('minute')
    if state_minute and state_minute != 0:
        return state_minute
    
    return 0

def test_correct_extraction():
    """Test the correct minute extraction with live matches"""
    
    api_key = os.getenv('SPORTMONKS_API_KEY')
    
    print("🎯 TESTING CORRECT MINUTE EXTRACTION")
    print("=" * 60)
    
    url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
    params = {
        'api_token': api_key,
        'include': 'scores;participants;state;periods'
    }
    
    response = requests.get(url, params=params)
    matches = response.json().get('data', [])
    
    print(f"📊 Found {len(matches)} total matches")
    
    live_count = 0
    
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
        
        # Only show actively playing matches
        if state_short in ['1H', '1st', '2H', '2nd']:
            live_count += 1
            
            if live_count <= 10:  # Show first 10
                # Extract minute correctly
                match_minute = get_correct_match_minute(match)
                
                print(f"\n⚽ {home_team} vs {away_team}")
                print(f"   State: {state.get('name', 'Unknown')} ({state_short})")
                print(f"   🕒 MATCH MINUTE: {match_minute}'")
                
                # Show periods for verification
                periods = match.get('periods', [])
                for i, period in enumerate(periods):
                    ticking = period.get('ticking', False)
                    minutes = period.get('minutes', 0)
                    description = period.get('description', 'Unknown')
                    
                    if ticking:
                        print(f"   ✅ Active: {description} - {minutes}'")
                    else:
                        print(f"   ⏸️ Ended: {description} - {minutes}'")
    
    print(f"\n📊 Found {live_count} live matches with proper timing!")

if __name__ == "__main__":
    test_correct_extraction() 