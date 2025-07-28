import os
import requests
from dotenv import load_dotenv

load_dotenv()

def find_missing_live_matches():
    """Find why we're missing live matches that should total ~36"""
    
    api_key = os.getenv('SPORTMONKS_API_KEY')
    
    print("🔍 FINDING MISSING LIVE MATCHES")
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
    
    # Different filtering approaches
    current_filter = []  # Our current logic
    ticking_only_filter = []  # Just trust ticking
    expanded_state_filter = []  # Include more states
    
    all_states = set()
    ticking_by_state = {}
    
    for match in matches:
        state = match.get('state', {})
        state_short = state.get('short_name', 'unknown')
        state_name = state.get('name', 'unknown')
        
        all_states.add(state_short)
        
        periods = match.get('periods', [])
        has_ticking = any(period.get('ticking', False) for period in periods)
        actual_minute = extract_match_minute(match)
        
        # Track ticking by state
        if has_ticking:
            if state_short not in ticking_by_state:
                ticking_by_state[state_short] = []
            
            # Get team names for examples
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
            
            ticking_by_state[state_short].append({
                'teams': f"{home_team} vs {away_team}",
                'minute': actual_minute,
                'state_name': state_name
            })
        
        # Apply different filters
        
        # 1. Our current filter
        if state_short in ['1H', '1st', '2H', '2nd'] and has_ticking:
            current_filter.append(match)
        
        # 2. Just trust ticking (any state with ticking = live)
        if has_ticking:
            ticking_only_filter.append(match)
        
        # 3. Expanded states (include ET, PEN, BREAK, etc)
        if state_short in ['1H', '1st', '2H', '2nd', 'ET', 'PEN', 'BREAK', 'SUSP', 'INT'] and has_ticking:
            expanded_state_filter.append(match)
    
    print(f"\n📊 FILTERING COMPARISON:")
    print(f"   Current filter (1st/2nd + ticking): {len(current_filter)} matches")
    print(f"   Ticking only filter (any ticking): {len(ticking_only_filter)} matches")
    print(f"   Expanded state filter: {len(expanded_state_filter)} matches")
    print(f"   Target expectation: ~36 matches")
    
    print(f"\n🔄 ALL STATES WITH TICKING PERIODS:")
    for state, matches in sorted(ticking_by_state.items(), key=lambda x: len(x[1]), reverse=True):
        count = len(matches)
        included_current = "✅" if state in ['1H', '1st', '2H', '2nd'] else "❌"
        print(f"   {included_current} {state}: {count} matches")
        
        # Show examples
        for i, match in enumerate(matches[:2]):  # Show first 2 examples
            print(f"      {i+1}. {match['teams']} | {match['minute']}' | ({match['state_name']})")
        if count > 2:
            print(f"      ... and {count - 2} more")
    
    # Recommendation
    missing_matches = len(ticking_only_filter) - len(current_filter)
    
    print(f"\n💡 RECOMMENDATION:")
    if len(ticking_only_filter) >= 35:
        print(f"   🎯 Using 'ticking only' filter gives us {len(ticking_only_filter)} matches (close to target ~36)")
        print(f"   📈 This would add {missing_matches} more matches to our current {len(current_filter)}")
        print(f"   🔧 Consider changing filter to: has_ticking = True (ignore state names)")
    else:
        print(f"   🤔 Even 'ticking only' gives us {len(ticking_only_filter)} matches (below target)")
        print(f"   🔍 May need to investigate other criteria or API limitations")
    
    # Show what states we'd add
    if missing_matches > 0:
        excluded_states = set(ticking_by_state.keys()) - set(['1H', '1st', '2H', '2nd'])
        if excluded_states:
            print(f"\n🔄 STATES WE'RE CURRENTLY EXCLUDING:")
            for state in sorted(excluded_states):
                count = len(ticking_by_state[state])
                print(f"   ❌ {state}: {count} matches with ticking")

def extract_match_minute(match):
    """Extract actual match minute from periods data"""
    periods = match.get('periods', [])
    for period in periods:
        if period.get('ticking', False):
            return period.get('minutes', 0)
    return 0

if __name__ == "__main__":
    find_missing_live_matches() 