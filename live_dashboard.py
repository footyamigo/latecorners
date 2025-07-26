import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()

def get_live_dashboard():
    """Get instant dashboard view of live matches"""
    
    api_key = os.getenv('SPORTMONKS_API_KEY')
    
    print("📊 LIVE MATCHES DASHBOARD")
    print("=" * 60)
    print(f"🕐 Updated: {datetime.now().strftime('%H:%M:%S on %Y-%m-%d')}")
    
    # Get live matches
    url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
    params = {
        'api_token': api_key,
        'include': 'scores;participants;state;periods;league;statistics'
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        matches = response.json().get('data', [])
        print(f"📡 Retrieved {len(matches)} inplay matches from API")
        
        # Filter for truly live matches (ticking only)
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
        
        # Group by state and minute ranges
        by_state = {}
        by_minute_range = {'Early (0-30)': [], 'Mid (31-60)': [], 'Late (61-90)': [], 'Extra (90+)': []}
        
        for match in live_matches:
            state = match['state']
            minute = match['minute']
            
            if state not in by_state:
                by_state[state] = []
            by_state[state].append(match)
            
            if minute <= 30:
                by_minute_range['Early (0-30)'].append(match)
            elif minute <= 60:
                by_minute_range['Mid (31-60)'].append(match)
            elif minute <= 90:
                by_minute_range['Late (61-90)'].append(match)
            else:
                by_minute_range['Extra (90+)'].append(match)
        
        # Display by state
        print(f"\n📊 BY MATCH STATE:")
        for state, matches in sorted(by_state.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"   {state}: {len(matches)} matches")
        
        # Display by minute ranges
        print(f"\n⏰ BY GAME TIME:")
        for time_range, matches in by_minute_range.items():
            if matches:
                print(f"   {time_range}: {len(matches)} matches")
        
        # Show all matches with priority indicators
        print(f"\n⚽ ALL LIVE MATCHES:")
        
        # Sort by priority: late game first, then by minute
        sorted_matches = sorted(live_matches, key=lambda x: (-x['minute'] if x['minute'] >= 70 else x['minute']))
        
        for i, match in enumerate(sorted_matches):
            # Priority indicators
            if match['minute'] >= 85:
                icon = "🔥"  # Critical late game
                priority = "CRITICAL"
            elif match['minute'] >= 75:
                icon = "⚡"  # Late game
                priority = "HIGH"
            elif match['minute'] >= 60:
                icon = "🟡"  # Second half
                priority = "MEDIUM"
            elif match['minute'] >= 45:
                icon = "🟢"  # Around half time
                priority = "NORMAL"
            else:
                icon = "🔵"  # Early game
                priority = "LOW"
            
            # Show interesting scorelines
            score_indicator = ""
            if match['home_score'] == match['away_score'] and match['minute'] >= 75:
                score_indicator = "🤝 DRAW"
            elif abs(match['home_score'] - match['away_score']) == 1 and match['minute'] >= 70:
                score_indicator = "🎯 CLOSE"
            
            print(f"   {i+1:2d}. {icon} {match['teams_display']} | {match['state']} | {match['minute']}' | {match['scoreline']} {score_indicator}")
            
            if priority in ['CRITICAL', 'HIGH']:
                print(f"       🏟️ {match['league']} | Priority: {priority}")
        
        # Save to file for other scripts to use
        save_dashboard_data(live_matches)
        
        # Summary stats
        print(f"\n📈 SUMMARY STATS:")
        print(f"   🔥 Critical (85+ min): {len([m for m in live_matches if m['minute'] >= 85])}")
        print(f"   ⚡ High Priority (75+ min): {len([m for m in live_matches if m['minute'] >= 75])}")
        print(f"   🤝 Draw Games: {len([m for m in live_matches if m['home_score'] == m['away_score']])}")
        print(f"   🎯 Close Games (1 goal diff): {len([m for m in live_matches if abs(m['home_score'] - m['away_score']) == 1])}")
        
        return live_matches
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def extract_match_data(match):
    """Extract match data"""
    
    try:
        match_id = match['id']
        
        # Get state and minute
        state = match.get('state', {})
        state_short = state.get('short_name', 'unknown')
        actual_minute = extract_match_minute(match)
        
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
        
        # Get league
        league_info = match.get('league', {})
        league_name = league_info.get('name', 'Unknown League')
        
        return {
            'match_id': match_id,
            'home_team': home_team,
            'away_team': away_team,
            'scoreline': f"{home_score}-{away_score}",
            'home_score': home_score,
            'away_score': away_score,
            'minute': actual_minute,
            'state': state_short,
            'league': league_name,
            'teams_display': f"{home_team} vs {away_team}",
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return None

def extract_match_minute(match):
    """Extract match minute"""
    periods = match.get('periods', [])
    for period in periods:
        if period.get('ticking', False):
            return period.get('minutes', 0)
    return 0

def save_dashboard_data(live_matches):
    """Save dashboard data for other scripts"""
    
    try:
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'total_live_matches': len(live_matches),
            'matches': live_matches,
            'summary': {
                'critical_late_game': len([m for m in live_matches if m['minute'] >= 85]),
                'high_priority': len([m for m in live_matches if m['minute'] >= 75]),
                'draw_games': len([m for m in live_matches if m['home_score'] == m['away_score']]),
                'close_games': len([m for m in live_matches if abs(m['home_score'] - m['away_score']) == 1])
            }
        }
        
        with open('dashboard_snapshot.json', 'w') as f:
            json.dump(dashboard_data, f, indent=2)
        
        print(f"\n💾 Dashboard data saved to dashboard_snapshot.json")
        
    except Exception as e:
        print(f"⚠️ Error saving dashboard data: {e}")

if __name__ == "__main__":
    get_live_dashboard() 