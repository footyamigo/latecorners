import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_correct_match_minute(match):
    """Extract the correct match minute from SportMonks data"""
    
    # Check periods for the ticking (active) period
    periods = match.get('periods', [])
    for period in periods:
        if period.get('ticking', False):
            return period.get('minutes', 0)
    
    return 0

def corrected_live_filtering():
    """Show the corrected filtering that includes ALL live matches"""
    
    api_key = os.getenv('SPORTMONKS_API_KEY')
    
    print("🎯 CORRECTED LIVE MATCH FILTERING (Include ALL ticking matches)")
    print("=" * 80)
    
    url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
    params = {
        'api_token': api_key,
        'include': 'scores;participants;state;periods'
    }
    
    response = requests.get(url, params=params)
    matches = response.json().get('data', [])
    
    print(f"📊 Total 'inplay' matches from API: {len(matches)}")
    
    # NEW CORRECTED FILTERING LOGIC
    truly_live_matches = []
    
    for match in matches:
        # Get team names
        participants = match.get('participants', [])
        home_team = "Unknown"
        away_team = "Unknown"
        
        for participant in participants:
            location = participant.get('meta', {}).get('location')
            if location == 'home':
                home_team = participant.get('name', 'Unknown')
            elif location == 'away':
                away_team = participant.get('name', 'Unknown')
        
        teams = f"{home_team} vs {away_team}"
        
        # Get state
        state = match.get('state', {})
        state_short = state.get('short_name', 'Unknown')
        
        # CORRECTED LOGIC: Include if playing state AND has ticking period
        if state_short in ['1H', '1st', '2H', '2nd']:
            periods = match.get('periods', [])
            has_ticking = any(period.get('ticking', False) for period in periods)
            
            if has_ticking:  # Include regardless of minute!
                minute = get_correct_match_minute(match)
                truly_live_matches.append({
                    'teams': teams,
                    'state': state_short,
                    'minute': minute,
                    'match_id': match.get('id')
                })
    
    print(f"✅ TRULY LIVE MATCHES: {len(truly_live_matches)}")
    print("=" * 50)
    
    # Group by minute to show the range
    minute_groups = {}
    for match in truly_live_matches:
        minute = match['minute']
        if minute not in minute_groups:
            minute_groups[minute] = []
        minute_groups[minute].append(match)
    
    # Show matches by minute
    for minute in sorted(minute_groups.keys()):
        matches_at_minute = minute_groups[minute]
        print(f"\n🕒 MINUTE {minute}: {len(matches_at_minute)} matches")
        
        for match in matches_at_minute[:3]:  # Show first 3 per minute
            print(f"   ⚽ {match['teams']} ({match['state']})")
        
        if len(matches_at_minute) > 3:
            print(f"   ... and {len(matches_at_minute) - 3} more")
    
    print(f"\n📊 SUMMARY:")
    print(f"Total live matches: {len(truly_live_matches)}")
    print(f"Minute range: {min(minute_groups.keys())} - {max(minute_groups.keys())}")
    print(f"Matches at minute 0 (just started): {len(minute_groups.get(0, []))}")
    print(f"Late matches (80+ min): {len([m for m in truly_live_matches if m['minute'] >= 80])}")
    
    return truly_live_matches

def test_with_corner_system(live_matches, api_key):
    """Test a few live matches with corner system"""
    
    print(f"\n🎯 TESTING CORNER SYSTEM WITH CORRECTED LIVE MATCHES")
    print("=" * 60)
    
    # Test first 5 matches
    for i, match_info in enumerate(live_matches[:5]):
        print(f"\n{i+1}. {match_info['teams']} | {match_info['minute']}' | {match_info['state']}")
        
        # Quick bet365 odds check
        fixture_url = f"https://api.sportmonks.com/v3/football/fixtures/{match_info['match_id']}"
        fixture_params = {
            'api_token': api_key,
            'include': 'odds'
        }
        
        try:
            fixture_response = requests.get(fixture_url, params=fixture_params)
            if fixture_response.status_code == 200:
                fixture_data = fixture_response.json()['data']
                odds_data = fixture_data.get('odds', [])
                
                bet365_odds = [odds for odds in odds_data if odds.get('bookmaker_id') == 2]
                
                if bet365_odds:
                    print(f"   ✅ Has bet365 odds ({len(bet365_odds)} markets)")
                else:
                    print(f"   ❌ No bet365 odds")
            else:
                print(f"   ⚠️ API error getting odds")
        except:
            print(f"   ⚠️ Error checking odds")

if __name__ == "__main__":
    api_key = os.getenv('SPORTMONKS_API_KEY')
    live_matches = corrected_live_filtering()
    test_with_corner_system(live_matches, api_key) 