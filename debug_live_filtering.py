import os
import requests
from dotenv import load_dotenv

load_dotenv()

def debug_live_match_filtering():
    """Debug why we're getting so few live matches"""
    
    api_key = os.getenv('SPORTMONKS_API_KEY')
    
    print("🔍 DEBUGGING LIVE MATCH FILTERING")
    print("=" * 60)
    
    # Get all inplay matches
    url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
    params = {
        'api_token': api_key,
        'include': 'scores;participants;state;periods;league;statistics'
    }
    
    response = requests.get(url, params=params, timeout=30)
    matches = response.json().get('data', [])
    
    print(f"📊 Retrieved {len(matches)} inplay matches from API")
    
    # Analyze all matches
    state_counts = {}
    ticking_analysis = {}
    minute_analysis = {}
    excluded_reasons = {}
    
    live_matches = []
    
    for match in matches:
        state = match.get('state', {})
        state_short = state.get('short_name', 'unknown')
        state_name = state.get('name', 'unknown')
        
        # Count states
        if state_short not in state_counts:
            state_counts[state_short] = 0
        state_counts[state_short] += 1
        
        # Check periods and ticking
        periods = match.get('periods', [])
        has_ticking = any(period.get('ticking', False) for period in periods)
        actual_minute = extract_match_minute(match)
        
        # Track ticking analysis
        ticking_key = f"{state_short}_ticking_{has_ticking}"
        if ticking_key not in ticking_analysis:
            ticking_analysis[ticking_key] = 0
        ticking_analysis[ticking_key] += 1
        
        # Track minute analysis
        minute_range = get_minute_range(actual_minute)
        if minute_range not in minute_analysis:
            minute_analysis[minute_range] = 0
        minute_analysis[minute_range] += 1
        
        # Apply our current filtering logic
        excluded_reason = None
        
        if state_short not in ['1H', '1st', '2H', '2nd']:
            excluded_reason = f"state_not_playing ({state_short})"
        elif not has_ticking:
            excluded_reason = "no_ticking_period"
        else:
            # This would be included
            match['_live_minute'] = actual_minute
            match['_live_state'] = state_short
            live_matches.append(match)
        
        if excluded_reason:
            if excluded_reason not in excluded_reasons:
                excluded_reasons[excluded_reason] = []
            
            # Get team names for context
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
            
            excluded_reasons[excluded_reason].append({
                'teams': f"{home_team} vs {away_team}",
                'state': f"{state_short} ({state_name})",
                'minute': actual_minute,
                'has_ticking': has_ticking
            })
    
    print(f"⚽ Found {len(live_matches)} truly live matches")
    print()
    
    # Show analysis
    print("📊 STATE ANALYSIS:")
    for state, count in sorted(state_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {state}: {count} matches")
    
    print(f"\n🔄 TICKING ANALYSIS:")
    for key, count in sorted(ticking_analysis.items(), key=lambda x: x[1], reverse=True):
        print(f"   {key}: {count} matches")
    
    print(f"\n⏰ MINUTE ANALYSIS:")
    for minute_range, count in sorted(minute_analysis.items()):
        print(f"   {minute_range}: {count} matches")
    
    print(f"\n❌ EXCLUSION ANALYSIS:")
    total_excluded = sum(len(matches) for matches in excluded_reasons.values())
    print(f"   Total excluded: {total_excluded}")
    
    for reason, matches in excluded_reasons.items():
        print(f"   \n   {reason}: {len(matches)} matches")
        # Show first few examples
        for i, match in enumerate(matches[:3]):
            print(f"     {i+1}. {match['teams']} | {match['state']} | {match['minute']}' | Ticking: {match['has_ticking']}")
        if len(matches) > 3:
            print(f"     ... and {len(matches) - 3} more")
    
    # Check if we should include more states
    print(f"\n🤔 POTENTIAL IMPROVEMENTS:")
    
    # Check HT matches with ticking
    ht_ticking = [match for match in matches 
                  if match.get('state', {}).get('short_name') == 'HT' 
                  and any(period.get('ticking', False) for period in match.get('periods', []))]
    
    if ht_ticking:
        print(f"   🔍 Found {len(ht_ticking)} HT matches with ticking periods - should we include these?")
    
    # Check other states with ticking
    other_ticking = [match for match in matches 
                     if match.get('state', {}).get('short_name') not in ['1H', '1st', '2H', '2nd', 'HT']
                     and any(period.get('ticking', False) for period in match.get('periods', []))]
    
    if other_ticking:
        states = set(match.get('state', {}).get('short_name') for match in other_ticking)
        print(f"   🔍 Found {len(other_ticking)} matches in other states with ticking: {states}")
    
    # Show what we'd get if we just used "any ticking period" logic
    all_ticking = [match for match in matches 
                   if any(period.get('ticking', False) for period in match.get('periods', []))]
    
    print(f"   💡 If we included ALL matches with ticking periods: {len(all_ticking)} matches")
    print(f"   📈 This would increase from {len(live_matches)} to {len(all_ticking)} live matches")

def extract_match_minute(match):
    """Extract actual match minute from periods data"""
    periods = match.get('periods', [])
    for period in periods:
        if period.get('ticking', False):
            return period.get('minutes', 0)
    return 0

def get_minute_range(minute):
    """Get minute range for analysis"""
    if minute == 0:
        return "0 (just started)"
    elif minute <= 15:
        return "1-15"
    elif minute <= 30:
        return "16-30"
    elif minute <= 45:
        return "31-45"
    elif minute <= 60:
        return "46-60"
    elif minute <= 75:
        return "61-75"
    elif minute <= 90:
        return "76-90"
    else:
        return "90+"

if __name__ == "__main__":
    debug_live_match_filtering() 