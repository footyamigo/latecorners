import os
import requests
from dotenv import load_dotenv

load_dotenv()

def verify_live_match_count():
    """Verify live match count and confirm filtering logic"""
    
    api_key = os.getenv('SPORTMONKS_API_KEY')
    
    print("🔍 VERIFYING LIVE MATCH COUNT")
    print("=" * 50)
    
    # Get all inplay matches
    url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
    params = {
        'api_token': api_key,
        'include': 'scores;participants;state;periods;league;statistics'
    }
    
    response = requests.get(url, params=params, timeout=30)
    matches = response.json().get('data', [])
    
    print(f"📊 Total inplay matches from API: {len(matches)}")
    
    # Count matches by state and ticking
    states_with_ticking = {}
    all_ticking_matches = []
    our_filtered_matches = []
    
    for match in matches:
        state = match.get('state', {})
        state_short = state.get('short_name', 'unknown')
        
        periods = match.get('periods', [])
        has_ticking = any(period.get('ticking', False) for period in periods)
        actual_minute = extract_match_minute(match)
        
        # Track all matches with ticking
        if has_ticking:
            all_ticking_matches.append(match)
            
            if state_short not in states_with_ticking:
                states_with_ticking[state_short] = 0
            states_with_ticking[state_short] += 1
        
        # Apply OUR current filtering logic
        if state_short in ['1H', '1st', '2H', '2nd'] and has_ticking:
            our_filtered_matches.append(match)
    
    print(f"⚽ OUR CURRENT FILTER: {len(our_filtered_matches)} live matches")
    print(f"🔄 ALL TICKING MATCHES: {len(all_ticking_matches)} live matches")
    
    print(f"\n📊 MATCHES WITH TICKING BY STATE:")
    for state, count in sorted(states_with_ticking.items(), key=lambda x: x[1], reverse=True):
        included = "✅" if state in ['1H', '1st', '2H', '2nd'] else "❌"
        print(f"   {included} {state}: {count} matches")
    
    # Show some examples of our filtered matches
    print(f"\n⚽ OUR {len(our_filtered_matches)} LIVE MATCHES:")
    for i, match in enumerate(our_filtered_matches):
        # Get team names
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
        
        # Get current score
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
        
        state_short = match.get('state', {}).get('short_name', 'unknown')
        minute = extract_match_minute(match)
        scoreline = f"{home_score}-{away_score}"
        
        print(f"   {i+1:2d}. {home_team} vs {away_team} | {state_short} | {minute}' | {scoreline}")
    
    # Check if we should include other states
    excluded_ticking = len(all_ticking_matches) - len(our_filtered_matches)
    if excluded_ticking > 0:
        print(f"\n🤔 WE'RE EXCLUDING {excluded_ticking} MATCHES WITH TICKING:")
        for state, count in states_with_ticking.items():
            if state not in ['1H', '1st', '2H', '2nd']:
                print(f"   ❌ {state}: {count} matches (reason: not playing state)")
    
    return len(our_filtered_matches), len(all_ticking_matches)

def extract_match_minute(match):
    """Extract actual match minute from periods data"""
    periods = match.get('periods', [])
    for period in periods:
        if period.get('ticking', False):
            return period.get('minutes', 0)
    return 0

if __name__ == "__main__":
    our_count, all_ticking_count = verify_live_match_count()
    
    print(f"\n📊 SUMMARY:")
    print(f"   Our filter: {our_count} matches")
    print(f"   All ticking: {all_ticking_count} matches")
    
    if our_count >= 20:
        print(f"   ✅ Meeting user's expectation of 'over 20' matches")
    else:
        print(f"   ⚠️ Below user's expectation of 'over 20' matches")
    
    if all_ticking_count > our_count:
        print(f"   💡 We could include {all_ticking_count - our_count} more matches if we trust ticking over state") 