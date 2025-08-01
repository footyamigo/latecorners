#!/usr/bin/env python3
"""
Check All Pending Matches
========================
Quick check of all pending matches to see which are finished.
"""

import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def quick_check_match(fixture_id, teams):
    """Quick check if match is finished"""
    
    api_key = os.getenv('SPORTMONKS_API_KEY')
    url = f'https://api.sportmonks.com/v3/football/fixtures/{fixture_id}?include=statistics&api_token={api_key}'
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                fixture = data['data']
                starting_at = fixture.get('starting_at')
                
                if starting_at:
                    # Parse the match time
                    match_time = datetime.fromisoformat(starting_at.replace('Z', '+00:00'))
                    now = datetime.now(match_time.tzinfo)
                    time_diff = now - match_time
                    hours_since = time_diff.total_seconds() / 3600
                    
                    print(f"🔍 {teams} ({fixture_id})")
                    print(f"   Started: {starting_at}")
                    print(f"   Hours ago: {hours_since:.1f}")
                    
                    # If more than 2.5 hours, likely finished
                    if hours_since > 2.5:
                        print(f"   ✅ LIKELY FINISHED")
                        
                        # Get corner statistics
                        statistics = fixture.get('statistics', [])
                        total_corners = 0
                        for stat in statistics:
                            if stat.get('type', {}).get('id') == 34:
                                total_corners += stat.get('value', 0)
                        
                        print(f"   🏆 Total Corners: {total_corners}")
                        return True, total_corners
                    else:
                        print(f"   ⏳ Still ongoing")
                        return False, 0
                        
        return False, 0
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, 0

if __name__ == "__main__":
    # All pending matches from database
    matches = [
        (999999, "Test Team A vs Test Team B"),
        (19428967, "Independiente Medellín vs Jaguares"),
        (19467972, "Pachuca W vs Pumas UNAM W"),
        (19396363, "West Coast Rangers vs Auckland II")
    ]
    
    print("🔍 CHECKING ALL PENDING MATCHES")
    print("="*50)
    
    finished_matches = []
    
    for fixture_id, teams in matches:
        finished, corners = quick_check_match(fixture_id, teams)
        if finished:
            finished_matches.append((fixture_id, teams, corners))
        print()
    
    print(f"📊 SUMMARY:")
    print(f"   Total pending: {len(matches)}")
    print(f"   Likely finished: {len(finished_matches)}")
    
    if finished_matches:
        print(f"\n🎯 MATCHES READY FOR UPDATE:")
        for fixture_id, teams, corners in finished_matches:
            print(f"   {fixture_id}: {teams} - {corners} corners") 