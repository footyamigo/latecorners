#!/usr/bin/env python3

"""
Test to show only TRULY LIVE matches (actively playing)
Not just matches in the "inplay" endpoint
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

def test_truly_live_matches():
    try:
        import requests
        import os
        
        api_key = os.getenv('SPORTMONKS_API_KEY')
        if not api_key:
            print("❌ No SPORTMONKS_API_KEY found in .env file!")
            return False
        
        print("⚽ Testing for TRULY LIVE (actively playing) matches...")
        
        # Get all "inplay" matches first
        url = "https://api.sportmonks.com/v3/football/livescores/inplay"
        params = {
            'api_token': api_key,
            'include': 'scores;participants;state;events;periods'
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            all_matches = data.get('data', [])
            
            print(f"📊 Total 'inplay' endpoint matches: {len(all_matches)}")
            
            # Define truly active states (including half-time)
            TRULY_LIVE_STATES = {
                'INPLAY_1ST_HALF',     # Playing 1st half
                'INPLAY_2ND_HALF',     # Playing 2nd half
                'HT',                  # Half-time break (will resume)
                'INPLAY_ET',           # Extra time
                'INPLAY_PENALTIES'     # Penalty shootout
            }
            
            # Filter for truly active matches
            truly_live_matches = []
            state_counts = {}
            
            for match in all_matches:
                state = match.get('state', {})
                if isinstance(state, dict):
                    state_name = state.get('developer_name', '')
                    
                    # Count all states
                    state_counts[state_name] = state_counts.get(state_name, 0) + 1
                    
                    # Keep only truly live matches
                    if state_name in TRULY_LIVE_STATES:
                        truly_live_matches.append(match)
            
            print(f"⚽ TRULY LIVE matches: {len(truly_live_matches)}")
            print("\n📋 All states found:")
            for state, count in sorted(state_counts.items()):
                emoji = "🔴" if state in TRULY_LIVE_STATES else "⚫"
                print(f"   {emoji} {state}: {count} matches")
            
            if len(truly_live_matches) > 0:
                print(f"\n🎮 TRULY LIVE matches:")
                print("═" * 60)
                
                for i, match in enumerate(truly_live_matches):
                    fixture_id = match.get('id', 'Unknown')
                    
                    # Extract team names
                    participants = match.get('participants', [])
                    home_team = "Unknown Home"
                    away_team = "Unknown Away"
                    
                    for participant in participants:
                        meta = participant.get('meta', {})
                        if meta.get('location') == 'home':
                            home_team = participant.get('name', 'Unknown Home')
                        elif meta.get('location') == 'away':
                            away_team = participant.get('name', 'Unknown Away')
                    
                    # Extract current score
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
                    
                    # Extract minute from periods
                    minute = 0
                    periods = match.get('periods', [])
                    
                    for period in periods:
                        if period.get('ticking', False):
                            base_minute = period.get('minutes', 0)
                            period_description = period.get('description', '')
                            
                            # Add offset for 2nd half
                            if '2nd' in period_description.lower():
                                base_minute += 45
                            
                            minute = base_minute
                            break
                    
                    # Extract state
                    state = match.get('state', {})
                    state_name = state.get('developer_name', '') if isinstance(state, dict) else ''
                    
                    print(f"{i+1:2d}. {home_team} vs {away_team}")
                    print(f"    Score: {home_score}-{away_score} | Minute: {minute}' | State: {state_name}")
                    print(f"    ID: {fixture_id}")
                    
                    # Check if would qualify for our late corner system
                    if state_name == 'INPLAY_2ND_HALF' and minute >= 70:
                        print("    🎯 ← PERFECT FOR LATE CORNER SYSTEM!")
                    elif state_name == 'INPLAY_2ND_HALF':
                        print("    ⏰ ← 2nd half (will qualify at 70+ minutes)")
                    
                    print()
                    
            else:
                print("\n⚠️ No truly live matches at the moment")
                print("   All matches are in non-playing states (HT, NS, etc.)")
                
            return True
            
        else:
            print(f"❌ API call failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = test_truly_live_matches()
    
    if result:
        print("\n✅ Truly live match test complete!")
        print("💡 This shows the real number of actively playing matches")
    else:
        print("\n❌ Test failed")
        sys.exit(1) 