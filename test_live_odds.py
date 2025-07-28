import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_live_odds_capabilities():
    """Test what live odds capabilities we have"""
    
    api_key = os.getenv('SPORTMONKS_API_KEY')
    
    print("🎯 TESTING LIVE ODDS CAPABILITIES")
    print("=" * 60)
    
    # Get live matches first
    url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
    params = {
        'api_token': api_key,
        'include': 'scores;participants;state;periods;statistics'
    }
    
    response = requests.get(url, params=params, timeout=30)
    matches = response.json().get('data', [])
    
    # Filter for truly live matches
    live_matches = []
    for match in matches:
        periods = match.get('periods', [])
        has_ticking = any(period.get('ticking', False) for period in periods)
        if has_ticking:
            live_matches.append(match)
    
    print(f"📊 Found {len(live_matches)} truly live matches")
    print(f"🔍 Testing odds for first 3 matches...\n")
    
    for i, match in enumerate(live_matches[:3]):
        match_id = match['id']
        
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
        
        print(f"🔍 {i+1}. {home_team} vs {away_team} (ID: {match_id})")
        
        # Test 1: Pre-match 1x2 odds (should work)
        print("   📊 Testing Pre-match 1x2 Odds:")
        prematch_odds = test_prematch_odds(match_id, api_key)
        if prematch_odds:
            print(f"      ✅ bet365 1x2: Home {prematch_odds['home']}, Away {prematch_odds['away']}")
        else:
            print(f"      ❌ No pre-match odds available")
        
        # Test 2: Live inplay odds
        print("   🔴 Testing Live Inplay Odds:")
        live_odds = test_live_inplay_odds(match_id, api_key)
        
        # Test 3: Asian corner odds (specific markets)
        print("   🎯 Testing Asian Corner Odds:")
        corner_odds = test_asian_corner_odds(match_id, api_key)
        
        print()

def test_prematch_odds(match_id, api_key):
    """Test pre-match odds (our current working method)"""
    
    try:
        fixture_url = f"https://api.sportmonks.com/v3/football/fixtures/{match_id}"
        fixture_params = {
            'api_token': api_key,
            'include': 'odds;participants;scores'
        }
        
        response = requests.get(fixture_url, params=fixture_params, timeout=15)
        if response.status_code != 200:
            return None
            
        fixture_data = response.json()['data']
        odds_data = fixture_data.get('odds', [])
        
        # Filter for bet365 1x2 odds
        bet365_odds = [odds for odds in odds_data if odds.get('bookmaker_id') == 2]
        
        home_odds = away_odds = None
        
        for odds in bet365_odds:
            market_desc = odds.get('market_description', '').lower()
            
            if any(term in market_desc for term in ['1x2', 'match winner', 'full time result', 'match result']):
                label = odds.get('label', '').lower()
                value = float(odds.get('value', 0))
                
                if label in ['home', '1', 'home win']:
                    home_odds = value
                elif label in ['away', '2', 'away win']:
                    away_odds = value
        
        if home_odds and away_odds:
            return {'home': home_odds, 'away': away_odds}
        
        return None
        
    except Exception as e:
        print(f"      ❌ Error: {e}")
        return None

def test_live_inplay_odds(match_id, api_key):
    """Test live inplay odds"""
    
    try:
        # Try different live odds endpoints
        endpoints = [
            f"https://api.sportmonks.com/v3/football/odds/inplay/fixtures/{match_id}",
            f"https://api.sportmonks.com/v3/football/livescores/inplay/{match_id}",
            f"https://api.sportmonks.com/v3/football/fixtures/{match_id}/odds"
        ]
        
        for endpoint in endpoints:
            try:
                params = {'api_token': api_key}
                response = requests.get(endpoint, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json().get('data', [])
                    if data:
                        print(f"      ✅ {endpoint.split('/')[-2:]}: {len(data)} odds found")
                        
                        # Check for bet365
                        bet365_count = 0
                        if isinstance(data, list):
                            bet365_count = len([odds for odds in data if odds.get('bookmaker_id') == 2])
                        
                        if bet365_count > 0:
                            print(f"         🎯 bet365 odds: {bet365_count} markets")
                        
                        return True
                else:
                    print(f"      ❌ {endpoint.split('/')[-2:]}: Status {response.status_code}")
                    
            except Exception as e:
                print(f"      ❌ {endpoint.split('/')[-2:]}: {e}")
        
        return False
        
    except Exception as e:
        print(f"      ❌ Live odds error: {e}")
        return False

def test_asian_corner_odds(match_id, api_key):
    """Test Asian corner odds (Markets 61 & 62)"""
    
    corner_markets = [
        (61, "Asian Total Corners"),
        (62, "Asian Handicap Corners")
    ]
    
    found_any = False
    
    for market_id, market_name in corner_markets:
        try:
            corner_url = f"https://api.sportmonks.com/v3/football/odds/inplay/fixtures/{match_id}/markets/{market_id}"
            params = {'api_token': api_key}
            
            response = requests.get(corner_url, params=params, timeout=10)
            
            if response.status_code == 200:
                corner_odds = response.json().get('data', [])
                bet365_corner = [odds for odds in corner_odds if odds.get('bookmaker_id') == 2]
                
                if bet365_corner:
                    print(f"      ✅ {market_name}: {len(bet365_corner)} bet365 odds")
                    found_any = True
                    
                    # Show sample
                    for odds in bet365_corner[:2]:
                        label = odds.get('label', 'N/A')
                        value = odds.get('value', 'N/A')
                        print(f"         📊 {label}: {value}")
                else:
                    print(f"      ⚠️ {market_name}: No bet365 odds")
            else:
                print(f"      ❌ {market_name}: Status {response.status_code}")
                
        except Exception as e:
            print(f"      ❌ {market_name}: {e}")
    
    return found_any

if __name__ == "__main__":
    test_live_odds_capabilities() 