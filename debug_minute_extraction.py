import os
import requests
from dotenv import load_dotenv
import json

def debug_minute_extraction():
    """Debug minute extraction for specific matches"""
    load_dotenv()
    
    api_key = os.getenv('SPORTMONKS_API_KEY')
    if not api_key:
        print("❌ SPORTMONKS_API_KEY not found in .env")
        return
    
    print("✅ Loaded .env file")
    print("🔍 Debugging minute extraction...")
    
    # Get live matches with all relevant includes
    url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
    params = {
        'api_token': api_key,
        'include': 'scores;participants;state;events;periods'
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        matches = data.get('data', [])
        print(f"📊 Found {len(matches)} total matches")
        
        # Focus on specific problematic matches
        for match in matches:
            match_id = match.get('id')
            
            # Extract basic info
            participants = match.get('participants', [])
            home_team = "Unknown"
            away_team = "Unknown"
            
            for participant in participants:
                if participant.get('meta', {}).get('location') == 'home':
                    home_team = participant.get('name', 'Unknown')
                elif participant.get('meta', {}).get('location') == 'away':
                    away_team = participant.get('name', 'Unknown')
            
            # Get state
            state = match.get('state', {})
            state_name = state.get('developer_name', state.get('short_name', ''))
            
            # Check if this is one of our target matches
            match_name = f"{home_team} vs {away_team}"
            if "Zhenys" in match_name or "Okzhetpes" in match_name or "ABFF" in match_name:
                print(f"\n🎯 DEBUGGING: {match_name}")
                print(f"   Match ID: {match_id}")
                print(f"   State: {state_name}")
                
                # Debug the minute field directly
                direct_minute = match.get('minute', 'NOT_FOUND')
                print(f"   Direct minute field: {direct_minute}")
                
                # Debug periods structure
                periods = match.get('periods', [])
                print(f"   Periods count: {len(periods)}")
                
                for i, period in enumerate(periods):
                    print(f"   Period {i+1}:")
                    print(f"     - minutes: {period.get('minutes', 'NOT_FOUND')}")
                    print(f"     - ticking: {period.get('ticking', 'NOT_FOUND')}")
                    print(f"     - description: {period.get('description', 'NOT_FOUND')}")
                    print(f"     - started: {period.get('started', 'NOT_FOUND')}")
                    print(f"     - ended: {period.get('ended', 'NOT_FOUND')}")
                
                # Show what our extraction method would return
                extracted_minute = extract_minute_debug(match)
                print(f"   🔍 Our extraction result: {extracted_minute}")
                
                # Show full match structure for this specific match
                print(f"\n📋 FULL MATCH STRUCTURE for {match_name}:")
                print(json.dumps(match, indent=2)[:2000] + "..." if len(json.dumps(match)) > 2000 else json.dumps(match, indent=2))
                
    except Exception as e:
        print(f"❌ Error: {e}")

def extract_minute_debug(match):
    """Debug version of minute extraction"""
    print(f"     🔍 Extracting minute...")
    
    periods = match.get('periods', [])
    print(f"     🔍 Found {len(periods)} periods")
    
    for i, period in enumerate(periods):
        ticking = period.get('ticking', False)
        print(f"     🔍 Period {i+1} ticking: {ticking}")
        
        if ticking:
            base_minute = period.get('minutes', 0)
            description = period.get('description', '')
            print(f"     🔍 Active period: {description}, minutes: {base_minute}")
            
            if '2nd' in description.lower():
                final_minute = base_minute + 45
                print(f"     🔍 2nd half detected, adding 45: {final_minute}")
                return final_minute
            else:
                print(f"     🔍 1st half or other, returning: {base_minute}")
                return base_minute
    
    # Fallback
    fallback = match.get('minute', 0)
    print(f"     🔍 No ticking period, fallback to: {fallback}")
    return fallback

if __name__ == "__main__":
    debug_minute_extraction() 