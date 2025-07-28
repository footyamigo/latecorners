import os
import requests
from dotenv import load_dotenv

load_dotenv()

def investigate_all_live_criteria():
    """Investigate all possible criteria that could indicate live matches"""
    
    api_key = os.getenv('SPORTMONKS_API_KEY')
    
    print("🔍 INVESTIGATING ALL LIVE MATCH CRITERIA")
    print("=" * 60)
    
    # Get all inplay matches
    url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
    params = {
        'api_token': api_key,
        'include': 'scores;participants;state;periods;league;statistics'
    }
    
    response = requests.get(url, params=params, timeout=30)
    matches = response.json().get('data', [])
    
    print(f"📊 Total inplay matches from API: {len(matches)}")
    
    # Different potential live criteria
    criteria_results = {
        'has_ticking': [],
        'playing_states_any_minute': [],
        'playing_states_minute_gt_0': [],
        'any_minute_gt_0': [],
        'has_recent_events': [],
        'status_inplay': []
    }
    
    all_states = set()
    state_analysis = {}
    
    for match in matches:
        state = match.get('state', {})
        state_short = state.get('short_name', 'unknown')
        state_name = state.get('name', 'unknown')
        state_id = state.get('id', 'unknown')
        
        all_states.add(state_short)
        
        if state_short not in state_analysis:
            state_analysis[state_short] = {
                'total': 0,
                'with_ticking': 0,
                'with_minute_gt_0': 0,
                'examples': []
            }
        
        state_analysis[state_short]['total'] += 1
        
        periods = match.get('periods', [])
        has_ticking = any(period.get('ticking', False) for period in periods)
        actual_minute = extract_match_minute(match)
        
        # Get team names and score
        participants = match.get('participants', [])
        home_team = away_team = "Unknown"
        home_score = away_score = 0
        
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
        for score_entry in scores:
            if score_entry.get('description') == 'CURRENT':
                score_data = score_entry.get('score', {})
                goals = score_data.get('goals', 0)
                participant = score_data.get('participant', '')
                
                if participant == 'home':
                    home_score = goals
                elif participant == 'away':
                    away_score = goals
        
        match_info = {
            'teams': f"{home_team} vs {away_team}",
            'state': f"{state_short} ({state_name})",
            'minute': actual_minute,
            'score': f"{home_score}-{away_score}",
            'has_ticking': has_ticking,
            'periods_count': len(periods)
        }
        
        # Update state analysis
        if has_ticking:
            state_analysis[state_short]['with_ticking'] += 1
        if actual_minute > 0:
            state_analysis[state_short]['with_minute_gt_0'] += 1
        
        if len(state_analysis[state_short]['examples']) < 2:
            state_analysis[state_short]['examples'].append(match_info)
        
        # Apply different criteria
        
        # 1. Has ticking period (our current main criteria)
        if has_ticking:
            criteria_results['has_ticking'].append(match_info)
        
        # 2. Playing states regardless of minute
        if state_short in ['1H', '1st', '2H', '2nd', 'ET', 'PEN', 'BREAK', 'SUSP', 'INT']:
            criteria_results['playing_states_any_minute'].append(match_info)
        
        # 3. Playing states with minute > 0
        if state_short in ['1H', '1st', '2H', '2nd', 'ET', 'PEN', 'BREAK', 'SUSP', 'INT'] and actual_minute > 0:
            criteria_results['playing_states_minute_gt_0'].append(match_info)
        
        # 4. Any match with minute > 0 (regardless of state)
        if actual_minute > 0:
            criteria_results['any_minute_gt_0'].append(match_info)
        
        # 5. Check if match has recent events (potential live indicator)
        events = match.get('events', [])
        if events:  # Has events (could indicate recent activity)
            criteria_results['has_recent_events'].append(match_info)
        
        # 6. Check for specific status indicators
        if state_id in [1, 2, 3, 4, 5]:  # Common live state IDs
            criteria_results['status_inplay'].append(match_info)
    
    print(f"\n📊 DIFFERENT LIVE CRITERIA RESULTS:")
    print(f"   Current (has_ticking): {len(criteria_results['has_ticking'])} matches")
    print(f"   Playing states (any minute): {len(criteria_results['playing_states_any_minute'])} matches")
    print(f"   Playing states (minute > 0): {len(criteria_results['playing_states_minute_gt_0'])} matches")
    print(f"   Any match (minute > 0): {len(criteria_results['any_minute_gt_0'])} matches")
    print(f"   Has recent events: {len(criteria_results['has_recent_events'])} matches")
    print(f"   Status inplay: {len(criteria_results['status_inplay'])} matches")
    print(f"   🎯 Target: ~36 matches")
    
    print(f"\n📊 STATE ANALYSIS:")
    for state, data in sorted(state_analysis.items(), key=lambda x: x[1]['total'], reverse=True):
        total = data['total']
        ticking = data['with_ticking']
        minute_gt_0 = data['with_minute_gt_0']
        print(f"   {state}: {total} total | {ticking} ticking | {minute_gt_0} minute>0")
        
        for example in data['examples']:
            tick_icon = "🔄" if example['has_ticking'] else "⏸️"
            print(f"      {tick_icon} {example['teams']} | {example['minute']}' | {example['score']}")
    
    # Find the best criteria that gets us closest to 36
    best_criteria = None
    best_count = 0
    target = 36
    
    for criteria_name, matches in criteria_results.items():
        count = len(matches)
        if abs(count - target) < abs(best_count - target):
            best_criteria = criteria_name
            best_count = count
    
    print(f"\n💡 RECOMMENDATION:")
    print(f"   🎯 Best criteria: '{best_criteria}' gives {best_count} matches")
    
    if best_count >= 35:
        print(f"   ✅ This meets your expectation of ~36 matches")
        print(f"   🔧 Consider updating filter logic to use this criteria")
    else:
        print(f"   ⚠️ Still below target - may need combination of criteria or different approach")
    
    # Show what we'd get with the best criteria
    if best_criteria and best_count > 28:
        print(f"\n🔍 MATCHES WITH '{best_criteria}' CRITERIA:")
        matches = criteria_results[best_criteria]
        for i, match in enumerate(matches[:10]):  # Show first 10
            print(f"   {i+1:2d}. {match['teams']} | {match['state']} | {match['minute']}' | {match['score']}")
        if len(matches) > 10:
            print(f"   ... and {len(matches) - 10} more")

def extract_match_minute(match):
    """Extract actual match minute from periods data"""
    periods = match.get('periods', [])
    for period in periods:
        if period.get('ticking', False):
            return period.get('minutes', 0)
    
    # Fallback - check if any period has minutes
    for period in periods:
        minutes = period.get('minutes', 0)
        if minutes > 0:
            return minutes
    
    return 0

if __name__ == "__main__":
    investigate_all_live_criteria() 