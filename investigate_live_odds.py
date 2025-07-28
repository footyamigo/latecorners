import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

def investigate_live_match_odds():
    """Investigate pre-match odds availability across live matches"""
    
    api_key = os.getenv('SPORTMONKS_API_KEY')
    
    print("🔍 INVESTIGATING PRE-MATCH ODDS ACROSS LIVE MATCHES")
    print("=" * 80)
    
    # Get all live matches
    url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
    params = {
        'api_token': api_key,
        'include': 'scores;participants;state;events;periods;league'
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"❌ Failed to get live matches: {response.status_code}")
        return
    
    data = response.json()
    matches = data.get('data', [])
    
    print(f"📊 Found {len(matches)} live matches")
    print()
    
    odds_results = []
    
    for i, match in enumerate(matches[:10]):  # Test first 10 matches
        match_id = match['id']
        
        # Get team names
        participants = match.get('participants', [])
        home_team = "Unknown"
        away_team = "Unknown"
        
        for participant in participants:
            meta = participant.get('meta', {})
            location = meta.get('location', 'unknown')
            name = participant.get('name', 'Unknown')
            
            if location == 'home':
                home_team = name
            elif location == 'away':
                away_team = name
        
        league_info = match.get('league', {})
        league_name = league_info.get('name', 'Unknown League')
        
        print(f"🔍 {i+1:2d}. Testing: {home_team} vs {away_team}")
        print(f"     League: {league_name} | Match ID: {match_id}")
        
        # Test different odds endpoints and includes
        odds_tests = [
            {
                'name': 'Basic Odds Include',
                'include': 'odds'
            },
            {
                'name': 'Detailed Odds Include', 
                'include': 'odds.bookmaker;odds.markets'
            },
            {
                'name': 'Odds with Selections',
                'include': 'odds.bookmaker;odds.markets.selections'
            },
            {
                'name': 'Pre-match Odds Only',
                'include': 'preMatchOdds'
            }
        ]
        
        found_odds = False
        
        for test in odds_tests:
            fixture_url = f"https://api.sportmonks.com/v3/football/fixtures/{match_id}"
            fixture_params = {
                'api_token': api_key,
                'include': test['include']
            }
            
            try:
                fixture_response = requests.get(fixture_url, params=fixture_params)
                
                if fixture_response.status_code == 200:
                    fixture_data = fixture_response.json()
                    
                    if 'data' in fixture_data:
                        fixture = fixture_data['data']
                        
                        # Check for odds data
                        odds_data = fixture.get('odds', [])
                        prematch_odds = fixture.get('preMatchOdds', [])
                        
                        if odds_data or prematch_odds:
                            print(f"     ✅ {test['name']}: Found {len(odds_data)} odds + {len(prematch_odds)} pre-match")
                            
                            # Analyze first odds entry
                            if odds_data:
                                sample_odds = odds_data[0]
                                print(f"        📊 Sample odds structure:")
                                print(f"        Keys: {list(sample_odds.keys())}")
                                
                                markets = sample_odds.get('markets', [])
                                if markets:
                                    sample_market = markets[0]
                                    print(f"        Market: {sample_market.get('name', 'Unknown')}")
                                    
                                    selections = sample_market.get('selections', [])
                                    if selections:
                                        print(f"        Selections: {len(selections)}")
                                        for sel in selections[:3]:
                                            label = sel.get('label', 'Unknown')
                                            odds = sel.get('odds', 0)
                                            print(f"          {label}: {odds}")
                                    
                                    found_odds = True
                                    break
                        else:
                            print(f"     ❌ {test['name']}: No odds found")
                
                else:
                    print(f"     ❌ {test['name']}: API error {fixture_response.status_code}")
            
            except Exception as e:
                print(f"     ❌ {test['name']}: Error - {e}")
        
        if found_odds:
            odds_results.append({
                'match_id': match_id,
                'teams': f"{home_team} vs {away_team}",
                'league': league_name,
                'has_odds': True
            })
        else:
            odds_results.append({
                'match_id': match_id,
                'teams': f"{home_team} vs {away_team}",
                'league': league_name,  
                'has_odds': False
            })
        
        print()
    
    # Summary
    print("📊 ODDS AVAILABILITY SUMMARY:")
    print("=" * 80)
    
    with_odds = [r for r in odds_results if r['has_odds']]
    without_odds = [r for r in odds_results if not r['has_odds']]
    
    print(f"✅ Matches WITH odds: {len(with_odds)}/{len(odds_results)}")
    for result in with_odds:
        print(f"   🟢 {result['teams']} ({result['league']})")
    
    print(f"\n❌ Matches WITHOUT odds: {len(without_odds)}/{len(odds_results)}")
    for result in without_odds:
        print(f"   🔴 {result['teams']} ({result['league']})")
    
    if with_odds:
        print(f"\n🎯 TESTING ENHANCED SYSTEM WITH ODDS-AVAILABLE MATCH:")
        test_match_id = with_odds[0]['match_id']
        test_odds_aware_system(test_match_id, api_key)

def test_odds_aware_system(match_id, api_key):
    """Test the odds-aware system with a match that has odds"""
    
    print(f"🎯 Testing match {match_id} with available odds...")
    
    # Get comprehensive fixture data
    fixture_url = f"https://api.sportmonks.com/v3/football/fixtures/{match_id}"
    fixture_params = {
        'api_token': api_key,
        'include': 'odds.bookmaker;odds.markets.selections;participants;scores;state;periods'
    }
    
    response = requests.get(fixture_url, params=fixture_params)
    if response.status_code == 200:
        fixture_data = response.json()['data']
        
        # Extract team info and score
        participants = fixture_data.get('participants', [])
        home_team = "Unknown"
        away_team = "Unknown"
        
        for participant in participants:
            meta = participant.get('meta', {})
            location = meta.get('location', 'unknown')
            name = participant.get('name', 'Unknown')
            
            if location == 'home':
                home_team = name
            elif location == 'away':
                away_team = name
        
        # Extract current score
        scores = fixture_data.get('scores', [])
        home_score = 0
        away_score = 0
        
        for score_entry in scores:
            if score_entry.get('description') == 'CURRENT':
                score_data = score_entry.get('score', {})
                goals = score_data.get('goals', 0)
                participant = score_data.get('participant', '')
                
                if participant == 'home':
                    home_score = goals
                elif participant == 'away':
                    away_score = goals
        
        # Extract odds
        odds_data = fixture_data.get('odds', [])
        home_odds = None
        away_odds = None
        
        for odds_entry in odds_data:
            markets = odds_entry.get('markets', [])
            
            for market in markets:
                market_name = market.get('name', '').lower()
                if '1x2' in market_name or 'match winner' in market_name or 'full time result' in market_name:
                    selections = market.get('selections', [])
                    
                    for selection in selections:
                        label = selection.get('label', '').lower()
                        odds = selection.get('odds', 0)
                        
                        if label in ['1', 'home', 'home win']:
                            home_odds = float(odds)
                        elif label in ['2', 'away', 'away win']:
                            away_odds = float(odds)
                    
                    if home_odds and away_odds:
                        break
            
            if home_odds and away_odds:
                break
        
        print(f"⚽ MATCH: {home_team} vs {away_team}")
        print(f"🏆 SCORE: {home_score}-{away_score}")
        
        if home_odds and away_odds:
            print(f"💰 PRE-MATCH ODDS:")
            print(f"   Home ({home_team}): {home_odds:.2f}")
            print(f"   Away ({away_team}): {away_odds:.2f}")
            
            # Determine favorite
            if home_odds < away_odds:
                favorite = 'home'
                favorite_team = home_team
                favorite_odds = home_odds
                underdog_odds = away_odds
            else:
                favorite = 'away' 
                favorite_team = away_team
                favorite_odds = away_odds
                underdog_odds = home_odds
            
            odds_ratio = underdog_odds / favorite_odds
            
            print(f"   🎯 FAVORITE: {favorite_team} ({favorite_odds:.2f})")
            print(f"   📊 Odds Ratio: {odds_ratio:.2f}x")
            
            # Analyze psychology
            if home_score != away_score:
                goal_diff = abs(home_score - away_score)
                
                if goal_diff == 1:
                    if (home_score > away_score and favorite == 'away') or (away_score > home_score and favorite == 'home'):
                        print(f"   🔥 FAVORITE TRAILING - CORNER GOLDMINE SETUP!")
                    else:
                        print(f"   🟡 Underdog trailing - moderate pressure expected")
                else:
                    print(f"   ⚠️ {goal_diff} goal difference - pressure depends on timing")
            else:
                print(f"   ⚡ Draw - both teams will push for winner")
        else:
            print(f"💰 PRE-MATCH ODDS: Could not extract 1x2 odds")
            print(f"   Raw odds data structure: {json.dumps(odds_data[0] if odds_data else {}, indent=2)[:500]}...")

if __name__ == "__main__":
    investigate_live_match_odds() 