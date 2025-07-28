import os
import requests
from dotenv import load_dotenv

load_dotenv()

def debug_odds_fetching():
    """Debug why bet365 odds aren't being found"""
    
    api_key = os.getenv('SPORTMONKS_API_KEY')
    
    print("🔍 DEBUGGING ODDS FETCHING ISSUE")
    print("=" * 50)
    
    # Get a few live matches
    url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
    params = {
        'api_token': api_key,
        'include': 'participants'
    }
    
    response = requests.get(url, params=params)
    matches = response.json().get('data', [])
    
    print(f"📊 Testing odds fetch for first 3 matches...")
    
    for i, match in enumerate(matches[:3]):
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
        
        print(f"\n🔍 {i+1}. {home_team} vs {away_team} (ID: {match_id})")
        
        # Test current method from live_data_collector
        print("   Testing current method:")
        current_result = test_current_method(match_id, api_key)
        print(f"   Result: {'✅ Found odds' if current_result else '❌ No odds'}")
        
        # Test working method from parse_flat_odds
        print("   Testing working method:")
        working_result = test_working_method(match_id, api_key)
        print(f"   Result: {'✅ Found odds' if working_result else '❌ No odds'}")
        
        if working_result and not current_result:
            print("   🔍 DIFFERENCE FOUND - Working method succeeds, current fails!")
            
        if i == 0 and not working_result:
            print("   🔍 Even working method fails - checking all odds for this match...")
            check_all_odds_structure(match_id, api_key)

def test_current_method(match_id, api_key):
    """Test current method from live_data_collector"""
    
    try:
        fixture_url = f"https://api.sportmonks.com/v3/football/fixtures/{match_id}"
        fixture_params = {
            'api_token': api_key,
            'include': 'odds',
            'select': 'odds'
        }
        
        response = requests.get(fixture_url, params=fixture_params, timeout=15)
        if response.status_code != 200:
            print(f"      ❌ Status code: {response.status_code}")
            return False
            
        fixture_data = response.json()['data']
        odds_data = fixture_data.get('odds', [])
        
        # Filter for bet365 1x2 odds
        bet365_odds = [odds for odds in odds_data if odds.get('bookmaker_id') == 2]
        
        print(f"      Total odds: {len(odds_data)}, bet365 odds: {len(bet365_odds)}")
        
        if not bet365_odds:
            return False
            
        for odds in bet365_odds:
            market_desc = odds.get('market_description', '').lower()
            if 'full time result' in market_desc:
                return True
        
        return False
        
    except Exception as e:
        print(f"      ❌ Error: {e}")
        return False

def test_working_method(match_id, api_key):
    """Test working method from parse_flat_odds"""
    
    try:
        fixture_url = f"https://api.sportmonks.com/v3/football/fixtures/{match_id}"
        fixture_params = {
            'api_token': api_key,
            'include': 'odds;participants;scores'
        }
        
        response = requests.get(fixture_url, params=fixture_params, timeout=15)
        if response.status_code != 200:
            print(f"      ❌ Status code: {response.status_code}")
            return False
            
        fixture_data = response.json()['data']
        odds_data = fixture_data.get('odds', [])
        
        print(f"      Total odds: {len(odds_data)}")
        
        if not odds_data:
            return False
            
        # Look for any match winner odds
        for odds in odds_data:
            market_desc = odds.get('market_description', '').lower()
            if any(term in market_desc for term in ['1x2', 'match winner', 'full time result', 'match result']):
                bookmaker_id = odds.get('bookmaker_id', 0)
                if bookmaker_id == 2:  # bet365
                    return True
        
        return False
        
    except Exception as e:
        print(f"      ❌ Error: {e}")
        return False

def check_all_odds_structure(match_id, api_key):
    """Check the complete odds structure for debugging"""
    
    try:
        fixture_url = f"https://api.sportmonks.com/v3/football/fixtures/{match_id}"
        fixture_params = {
            'api_token': api_key,
            'include': 'odds'
        }
        
        response = requests.get(fixture_url, params=fixture_params, timeout=15)
        if response.status_code != 200:
            print(f"      ❌ API Error: {response.status_code}")
            return
            
        fixture_data = response.json()['data']
        odds_data = fixture_data.get('odds', [])
        
        print(f"   📊 Complete odds analysis:")
        print(f"      Total odds entries: {len(odds_data)}")
        
        if not odds_data:
            print(f"      ❌ No odds data at all for this match")
            return
        
        # Analyze bookmakers
        bookmaker_ids = set()
        market_types = set()
        
        for odds in odds_data:
            bookmaker_ids.add(odds.get('bookmaker_id', 'unknown'))
            market_types.add(odds.get('market_description', 'unknown'))
        
        print(f"      Bookmaker IDs: {sorted(list(bookmaker_ids))}")
        print(f"      bet365 (ID 2) present: {'Yes' if 2 in bookmaker_ids else 'No'}")
        print(f"      Market types: {sorted(list(market_types))[:5]}...")  # First 5
        
        # Check for bet365 specifically
        bet365_odds = [odds for odds in odds_data if odds.get('bookmaker_id') == 2]
        if bet365_odds:
            print(f"      bet365 odds count: {len(bet365_odds)}")
            print(f"      bet365 markets: {[odds.get('market_description', 'unknown') for odds in bet365_odds[:3]]}")
        else:
            print(f"      ❌ No bet365 odds found")
        
    except Exception as e:
        print(f"      ❌ Error: {e}")

if __name__ == "__main__":
    debug_odds_fetching() 