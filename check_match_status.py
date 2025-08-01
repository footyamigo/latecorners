#!/usr/bin/env python3
"""
Check Match Status
=================
Check the actual status of a specific match from SportMonks.
"""

import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def check_match_status(fixture_id):
    """Check the status of a specific match"""
    
    api_key = os.getenv('SPORTMONKS_API_KEY')
    if not api_key:
        print("❌ No API key found")
        return
    
    url = f'https://api.sportmonks.com/v3/football/fixtures/{fixture_id}?include=scores;statistics&api_token={api_key}'
    
    print(f'🔍 Checking fixture {fixture_id}...')
    
    try:
        response = requests.get(url)
        print(f'Status Code: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                fixture = data['data']
                
                # Check basic match info
                print(f"📅 Match Date: {fixture.get('starting_at')}")
                print(f"⏰ Current Time: {datetime.now()}")
                
                state = fixture.get('state', {})
                print(f"📊 State: {state}")
                print(f"🏆 Match Status: {state.get('state', 'Unknown')}")
                print(f"⏱️ Minute: {state.get('minute', 'Unknown')}")
                
                # Get scores
                scores = fixture.get('scores', [])
                current_score = None
                for score in scores:
                    if score.get('description') == 'CURRENT':
                        if not current_score:
                            current_score = {'home': 0, 'away': 0}
                        if score.get('score', {}).get('participant') == 'home':
                            current_score['home'] = score.get('score', {}).get('goals', 0)
                        elif score.get('score', {}).get('participant') == 'away':
                            current_score['away'] = score.get('score', {}).get('goals', 0)
                
                if current_score:
                    print(f"⚽ Current Score: {current_score['home']}-{current_score['away']}")
                
                # Check match timing
                starting_at = fixture.get('starting_at')
                if starting_at:
                    from datetime import datetime
                    match_time = datetime.fromisoformat(starting_at.replace('Z', '+00:00'))
                    now = datetime.now(match_time.tzinfo)
                    time_diff = now - match_time
                    
                    print(f"⏰ Time since start: {time_diff}")
                    
                    # If more than 2.5 hours since start, likely finished
                    if time_diff.total_seconds() > 9000:  # 2.5 hours
                        print("🏁 LIKELY FINISHED (>2.5 hours since start)")
                        
                        # Get corner statistics
                        statistics = fixture.get('statistics', [])
                        total_corners = 0
                        
                        for stat in statistics:
                            if stat.get('type', {}).get('id') == 34:  # Corner kicks
                                total_corners += stat.get('value', 0)
                        
                        print(f"🏆 Total Corners: {total_corners}")
                        return True, total_corners
                    else:
                        print("⏳ Match likely still ongoing")
                        return False, 0
                
                match_state = state.get('state')
                if match_state == 'FT':
                    print('✅ OFFICIALLY FINISHED!')
                    return True, 0
                elif match_state in ['LIVE', 'HT', '1H', '2H']:
                    print(f'⏳ Match ongoing: {match_state}')
                    return False, 0
                else:
                    print(f'📊 Match status: {match_state}')
                    return False, 0
                    
            else:
                print('No fixture data found')
                return False, 0
        else:
            print(f'Error: {response.text[:200]}')
            return False, 0
            
    except Exception as e:
        print(f'❌ Error: {e}')
        return False, 0

if __name__ == "__main__":
    # Check one of the pending matches
    fixture_id = 19428967  # Independiente Medellín vs Jaguares
    finished, corners = check_match_status(fixture_id)
    
    if finished:
        print(f"\n🎯 RESULT: Match is finished with {corners} total corners")
    else:
        print("\n⏳ RESULT: Match not finished yet") 