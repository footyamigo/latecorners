import os
import requests
from dotenv import load_dotenv
import time
from datetime import datetime

load_dotenv()

def monitor_live_matches(check_interval=60):
    """Simple real-time monitor for live matches"""
    
    api_key = os.getenv('SPORTMONKS_API_KEY')
    previous_matches = set()
    check_count = 0
    
    print("🚀 SIMPLE LIVE MATCH MONITOR")
    print(f"⏰ Checking every {check_interval} seconds")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    try:
        while True:
            check_count += 1
            current_time = datetime.now().strftime('%H:%M:%S')
            
            print(f"\n🔍 CHECK #{check_count} - {current_time}")
            
            # Get live matches
            live_matches = get_current_live_matches(api_key)
            
            if live_matches is None:
                print("   ❌ API Error - skipping check")
                time.sleep(check_interval)
                continue
            
            # Extract match IDs and basic info
            current_matches = {}
            for match in live_matches:
                match_id = match['match_id']
                current_matches[match_id] = f"{match['teams_display']} | {match['minute']}' | {match['scoreline']}"
            
            current_match_ids = set(current_matches.keys())
            
            # Detect changes
            new_matches = current_match_ids - previous_matches
            ended_matches = previous_matches - current_match_ids
            
            # Display results
            print(f"   📊 Total Live: {len(current_matches)} matches")
            
            if new_matches:
                print(f"   🟢 NEW MATCHES ({len(new_matches)}):")
                for match_id in new_matches:
                    print(f"      🆕 {current_matches[match_id]}")
            
            if ended_matches:
                print(f"   🔴 ENDED MATCHES ({len(ended_matches)}):")
                for match_id in ended_matches:
                    print(f"      📄 Match ID: {match_id}")
            
            if not new_matches and not ended_matches:
                print(f"   ⚪ No changes since last check")
            
            # Show sample of current matches
            if current_matches:
                print(f"   ⚽ Current Live (first 5):")
                for i, (match_id, info) in enumerate(list(current_matches.items())[:5]):
                    print(f"      {i+1}. {info}")
                if len(current_matches) > 5:
                    print(f"      ... and {len(current_matches) - 5} more")
            
            # Update for next check
            previous_matches = current_match_ids
            
            print(f"   ⏰ Next check in {check_interval} seconds...")
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        print(f"\n🛑 Monitoring stopped. Total checks: {check_count}")

def get_current_live_matches(api_key):
    """Get current live matches"""
    
    url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
    params = {
        'api_token': api_key,
        'include': 'scores;participants;state;periods'
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        matches = response.json().get('data', [])
        live_matches = []
        
        for match in matches:
            # Use ticking-only filter
            periods = match.get('periods', [])
            has_ticking = any(period.get('ticking', False) for period in periods)
            
            if has_ticking:
                match_data = extract_basic_match_data(match)
                if match_data:
                    live_matches.append(match_data)
        
        return live_matches
        
    except Exception as e:
        print(f"   API Error: {e}")
        return None

def extract_basic_match_data(match):
    """Extract basic match data"""
    
    try:
        # Get teams
        participants = match.get('participants', [])
        home_team = away_team = "Unknown"
        
        for participant in participants:
            meta = participant.get('meta', {})
            location = meta.get('location', 'unknown')
            name = participant.get('name', 'Unknown')
            
            if location == 'home':
                home_team = name
            elif location == 'away':
                away_team = name
        
        # Get score
        scores = match.get('scores', [])
        home_score = away_score = 0
        
        for score_entry in scores:
            if score_entry.get('description') == 'CURRENT':
                score_data = score_entry.get('score', {})
                goals = score_data.get('goals', 0)
                participant = score_data.get('participant', '')
                
                if participant == 'home':
                    home_score = goals
                elif participant == 'away':
                    away_score = goals
        
        # Get minute
        periods = match.get('periods', [])
        minute = 0
        for period in periods:
            if period.get('ticking', False):
                minute = period.get('minutes', 0)
                break
        
        return {
            'match_id': match['id'],
            'teams_display': f"{home_team} vs {away_team}",
            'scoreline': f"{home_score}-{away_score}",
            'minute': minute
        }
        
    except Exception as e:
        return None

if __name__ == "__main__":
    import sys
    
    # Check for interval argument
    interval = 60
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except ValueError:
            print("Usage: python simple_live_monitor.py [interval_seconds]")
            sys.exit(1)
    
    monitor_live_matches(interval) 