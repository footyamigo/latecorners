#!/usr/bin/env python3

"""
FIXED test with proper Sportmonks includes to get live data
This uses the correct API parameters to retrieve live match information
"""

import sys
import json
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print("✅ Loaded .env file")
    else:
        print("❌ No .env file found!")
        sys.exit(1)
except ImportError:
    print("Installing python-dotenv...")
    import os
    os.system("pip install python-dotenv")
    from dotenv import load_dotenv
    load_dotenv()

def test_fixed_live_matches():
    try:
        import requests
        import os
        
        api_key = os.getenv('SPORTMONKS_API_KEY')
        if not api_key:
            print("❌ No SPORTMONKS_API_KEY found in .env file!")
            return False
        
        print("🔧 Testing FIXED Sportmonks API with proper includes...")
        print(f"🔑 API Key: {api_key[:10]}...")
        
        # FIXED: Add the proper includes to get live data + periods for minute
        url = "https://api.sportmonks.com/v3/football/livescores/inplay"
        params = {
            'api_token': api_key,
            'include': 'scores;participants;state;events;periods'  # 🎯 ADDED: periods for minute
        }
        
        print("📡 Calling API with proper includes...")
        print(f"🔗 URL: {url}")
        print(f"📋 Includes: scores, participants, state, events")
        
        response = requests.get(url, params=params)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            matches = data.get('data', [])
            
            print(f"✅ API call successful - found {len(matches)} live matches")
            
            if len(matches) > 0:
                print("\n🔍 FIXED: Live matches with proper data:")
                print("═" * 80)
                
                for i, match in enumerate(matches[:5]):  # Show first 5
                    fixture_id = match.get('id', 'Unknown')
                    
                    # Extract team names from participants
                    participants = match.get('participants', [])
                    home_team = "Unknown Home"
                    away_team = "Unknown Away"
                    
                    for participant in participants:
                        meta = participant.get('meta', {})
                        if meta.get('location') == 'home':
                            home_team = participant.get('name', 'Unknown Home')
                        elif meta.get('location') == 'away':
                            away_team = participant.get('name', 'Unknown Away')
                    
                    # Extract current score from scores - FIXED logic
                    scores = match.get('scores', [])
                    home_score = 0
                    away_score = 0
                    
                    # Find CURRENT score entries and match by participant
                    for score_entry in scores:
                        if score_entry.get('description') == 'CURRENT':
                            score_data = score_entry.get('score', {})
                            goals = score_data.get('goals', 0)
                            participant = score_data.get('participant', '')
                            
                            if participant == 'home':
                                home_score = goals
                            elif participant == 'away':
                                away_score = goals
                    
                    # Extract match state
                    state = match.get('state', {})
                    state_name = state.get('developer_name', state.get('short_name', 'Unknown')) if isinstance(state, dict) else 'Unknown'
                    
                    # Extract minute (this might be in different places) - FIXED to use periods
                    minute = 0
                    periods = match.get('periods', [])
                    
                    # Find the currently active period (ticking = true)
                    for period in periods:
                        if period.get('ticking', False):
                            base_minute = period.get('minutes', 0)
                            period_description = period.get('description', '')
                            
                            # Add offset for 2nd half (45 minutes)
                            if '2nd' in period_description.lower():
                                base_minute += 45
                            
                            minute = base_minute
                            break
                    
                    # Fallback to old method if no periods
                    if minute == 0:
                        minute = match.get('minute', 0)
                        if minute == 0:
                            state = match.get('state', {})
                            if isinstance(state, dict):
                                minute = state.get('minute', 0)
                    
                    print(f"{i+1:2d}. {home_team} vs {away_team}")
                    print(f"    Score: {home_score}-{away_score} | Minute: {minute}' | State: {state_name}")
                    print(f"    ID: {fixture_id}")
                    
                    # Check if this would qualify for our system
                    if minute >= 70 and state_name == 'INPLAY_2ND_HALF':
                        print("    🎯 ← WOULD BE MONITORED by our system!")
                    
                    # Show a sample of events if available
                    events = match.get('events', [])
                    if events:
                        print(f"    📊 Has {len(events)} events (goals, cards, subs)")
                    
                    print()
                
                # Summary
                qualifying_count = 0
                for match in matches:
                    minute = 0
                    periods = match.get('periods', [])
                    
                    # Find the currently active period (ticking = true)
                    for period in periods:
                        if period.get('ticking', False):
                            base_minute = period.get('minutes', 0)
                            period_description = period.get('description', '')
                            
                            # Add offset for 2nd half (45 minutes)
                            if '2nd' in period_description.lower():
                                base_minute += 45
                            
                            minute = base_minute
                            break
                    
                    state = match.get('state', {})
                    state_name = state.get('developer_name', '') if isinstance(state, dict) else ''
                    if minute >= 70 and state_name == 'INPLAY_2ND_HALF':
                        qualifying_count += 1
                
                print(f"🎯 SUMMARY:")
                print(f"   Total live matches: {len(matches)}")
                print(f"   Matches past 70': {qualifying_count}")
                print(f"   API Status: ✅ WORKING with live data!")
                
                # Show the raw structure of first match for debugging
                if len(matches) > 0:
                    print(f"\n📋 Raw structure of first match:")
                    print("─" * 40)
                    first_match = matches[0]
                    print(f"Available keys: {list(first_match.keys())}")
                    
                    if 'participants' in first_match:
                        print(f"Participants: {len(first_match.get('participants', []))} teams")
                    if 'scores' in first_match:
                        print(f"Scores: {len(first_match.get('scores', []))} score entries")
                    if 'state' in first_match:
                        print(f"State: {first_match.get('state', {})}")
                    if 'events' in first_match:
                        print(f"Events: {len(first_match.get('events', []))} events")
                
                return True
                
            else:
                print("⚠️ No live matches at the moment")
                print("   The API is working, but no matches are currently live")
                print("   Try again during peak football hours")
                return True
                
        elif response.status_code == 401:
            print("❌ API Authentication failed (401)")
            print("💡 Check your API key")
            return False
            
        elif response.status_code == 403:
            print("❌ API Access forbidden (403)")
            print("💡 Your plan might not include live data")
            return False
            
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing FIXED Sportmonks API with includes...")
    result = test_fixed_live_matches()
    
    if result:
        print("\n🎉 FIXED API test successful!")
        print("✅ Now getting real live match data")
    else:
        print("\n❌ API test failed")
        sys.exit(1) 