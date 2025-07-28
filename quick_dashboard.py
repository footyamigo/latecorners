import os
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def show_live_dashboard():
    """Quick dashboard view of current live matches"""
    
    api_key = os.getenv('SPORTMONKS_API_KEY')
    
    print("📊 LIVE MATCHES DASHBOARD")
    print("=" * 50)
    print(f"🕐 {datetime.now().strftime('%H:%M:%S on %Y-%m-%d')}")
    
    # Get live matches
    url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
    params = {
        'api_token': api_key,
        'include': 'scores;participants;state;periods;league'
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        matches = response.json().get('data', [])
        print(f"📡 API returned {len(matches)} inplay matches")
        
        # Filter for truly live matches
        live_matches = []
        
        for match in matches:
            periods = match.get('periods', [])
            has_ticking = any(period.get('ticking', False) for period in periods)
            
            if has_ticking:
                match_data = extract_match_data(match)
                if match_data:
                    live_matches.append(match_data)
        
        print(f"⚽ Found {len(live_matches)} truly live matches")
        
        if not live_matches:
            print("\n❌ No live matches currently active")
            return
        
        # Sort by priority (late game first)
        live_matches.sort(key=lambda x: (-x['minute'] if x['minute'] >= 70 else x['minute']))
        
        print(f"\n⚽ ALL LIVE MATCHES:")
        
        for i, match in enumerate(live_matches):
            # Priority indicators
            if match['minute'] >= 85:
                icon = "🔥"
            elif match['minute'] >= 75:
                icon = "⚡"
            elif match['minute'] >= 60:
                icon = "🟡"
            else:
                icon = "🟢"
            
            print(f"   {i+1:2d}. {icon} {match['teams']} | {match['state']} | {match['minute']}' | {match['score']}")
        
        # Quick stats
        late_games = len([m for m in live_matches if m['minute'] >= 75])
        draws = len([m for m in live_matches if m['home_score'] == m['away_score']])
        close_games = len([m for m in live_matches if abs(m['home_score'] - m['away_score']) == 1])
        
        print(f"\n📊 QUICK STATS:")
        print(f"   🔥 Late games (75+ min): {late_games}")
        print(f"   🤝 Draws: {draws}")
        print(f"   🎯 Close games (1 goal diff): {close_games}")
        
        return live_matches
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def extract_match_data(match):
    """Extract match data"""
    
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
        
        # Get minute and state
        state = match.get('state', {}).get('short_name', 'unknown')
        
        periods = match.get('periods', [])
        minute = 0
        for period in periods:
            if period.get('ticking', False):
                minute = period.get('minutes', 0)
                break
        
        return {
            'match_id': match['id'],
            'teams': f"{home_team} vs {away_team}",
            'score': f"{home_score}-{away_score}",
            'home_score': home_score,
            'away_score': away_score,
            'minute': minute,
            'state': state
        }
        
    except Exception as e:
        return None

if __name__ == "__main__":
    show_live_dashboard() 