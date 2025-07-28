import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

def test_specific_match_corner_odds():
    """Test Asian corner odds for North Lakes United W vs Sunshine Coast Wanderers W"""
    
    api_key = os.getenv('SPORTMONKS_API_KEY')
    
    print("🎯 TESTING ASIAN CORNER ODDS")
    print("=" * 60)
    print("🔍 Looking for: North Lakes United W vs Sunshine Coast Wanderers W")
    
    # First, find the specific match
    url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
    params = {
        'api_token': api_key,
        'include': 'participants;state;periods'
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        matches = response.json().get('data', [])
        
        print(f"📊 Found {len(matches)} inplay matches")
        
        # Find the specific match
        target_match = None
        for match in matches:
            participants = match.get('participants', [])
            home_team = away_team = ""
            
            for participant in participants:
                meta = participant.get('meta', {})
                location = meta.get('location', 'unknown')
                name = participant.get('name', 'Unknown')
                
                if location == 'home':
                    home_team = name
                elif location == 'away':
                    away_team = name
            
            # Check if this is our target match
            if ("North Lakes" in home_team and "Sunshine Coast" in away_team) or \
               ("Sunshine Coast" in home_team and "North Lakes" in away_team):
                target_match = match
                print(f"✅ FOUND TARGET MATCH: {home_team} vs {away_team}")
                print(f"   Match ID: {match['id']}")
                break
        
        if not target_match:
            print("❌ Target match not found in current live matches")
            print("\n🔍 Available matches:")
            for i, match in enumerate(matches[:10]):
                participants = match.get('participants', [])
                home_team = away_team = ""
                
                for participant in participants:
                    meta = participant.get('meta', {})
                    location = meta.get('location', 'unknown')
                    name = participant.get('name', 'Unknown')
                    
                    if location == 'home':
                        home_team = name
                    elif location == 'away':
                        away_team = name
                
                print(f"   {i+1}. {home_team} vs {away_team}")
            return
        
        match_id = target_match['id']
        
        # Test Asian corner markets
        print(f"\n🎯 TESTING ASIAN CORNER MARKETS FOR MATCH {match_id}:")
        
        # Market 61: Asian Total Corners
        print("\n📊 Market 61: Asian Total Corners")
        test_corner_market(match_id, 61, api_key)
        
        # Market 62: Asian Handicap Corners  
        print("\n📊 Market 62: Asian Handicap Corners")
        test_corner_market(match_id, 62, api_key)
        
        # Also test general inplay odds for this match
        print(f"\n🔴 TESTING GENERAL INPLAY ODDS:")
        test_general_inplay_odds(match_id, api_key)
        
    except Exception as e:
        print(f"❌ Error: {e}")

def test_corner_market(match_id, market_id, api_key):
    """Test a specific corner market"""
    
    try:
        corner_url = f"https://api.sportmonks.com/v3/football/odds/inplay/fixtures/{match_id}/markets/{market_id}"
        params = {'api_token': api_key}
        
        print(f"   🔗 URL: {corner_url}")
        
        response = requests.get(corner_url, params=params, timeout=15)
        print(f"   📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            corner_odds = response.json().get('data', [])
            print(f"   📊 Total odds entries: {len(corner_odds)}")
            
            if corner_odds:
                # Check for bet365
                bet365_odds = [odds for odds in corner_odds if odds.get('bookmaker_id') == 2]
                print(f"   🎯 bet365 odds: {len(bet365_odds)}")
                
                if bet365_odds:
                    print(f"   ✅ BET365 CORNER ODDS FOUND!")
                    for i, odds in enumerate(bet365_odds):
                        print(f"      {i+1}. Label: {odds.get('label', 'N/A')}")
                        print(f"         Value: {odds.get('value', 'N/A')}")
                        print(f"         Total: {odds.get('total', 'N/A')}")
                        print(f"         Handicap: {odds.get('handicap', 'N/A')}")
                        print(f"         Market Description: {odds.get('market_description', 'N/A')}")
                        print()
                else:
                    print(f"   ❌ No bet365 odds found")
                    
                # Show other bookmakers for reference
                other_bookmakers = set()
                for odds in corner_odds:
                    bookmaker_id = odds.get('bookmaker_id')
                    if bookmaker_id and bookmaker_id != 2:
                        other_bookmakers.add(bookmaker_id)
                
                if other_bookmakers:
                    print(f"   📋 Other bookmakers available: {sorted(list(other_bookmakers))}")
            else:
                print(f"   ❌ No odds data returned")
        else:
            print(f"   ❌ API Error: {response.status_code}")
            if response.status_code == 404:
                print(f"   ℹ️ Market {market_id} may not be available for this match")
            elif response.status_code == 422:
                print(f"   ℹ️ Invalid request - check market ID or match ID")
    
    except Exception as e:
        print(f"   ❌ Exception: {e}")

def test_general_inplay_odds(match_id, api_key):
    """Test general inplay odds to see what's available"""
    
    try:
        inplay_url = f"https://api.sportmonks.com/v3/football/odds/inplay/fixtures/{match_id}"
        params = {'api_token': api_key}
        
        response = requests.get(inplay_url, params=params, timeout=15)
        print(f"   📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            odds_data = response.json().get('data', [])
            print(f"   📊 Total inplay odds: {len(odds_data)}")
            
            if odds_data:
                # Analyze available markets
                markets = {}
                bet365_markets = {}
                
                for odds in odds_data:
                    market_desc = odds.get('market_description', 'Unknown')
                    bookmaker_id = odds.get('bookmaker_id', 0)
                    
                    if market_desc not in markets:
                        markets[market_desc] = 0
                    markets[market_desc] += 1
                    
                    if bookmaker_id == 2:  # bet365
                        if market_desc not in bet365_markets:
                            bet365_markets[market_desc] = 0
                        bet365_markets[market_desc] += 1
                
                print(f"\n   📋 ALL AVAILABLE MARKETS:")
                for market, count in sorted(markets.items()):
                    bet365_count = bet365_markets.get(market, 0)
                    bet365_status = f"(bet365: {bet365_count})" if bet365_count > 0 else "(no bet365)"
                    print(f"      {market}: {count} {bet365_status}")
                
                # Look specifically for corner-related markets
                print(f"\n   🎯 CORNER-RELATED MARKETS:")
                corner_markets = [market for market in markets.keys() if 'corner' in market.lower()]
                if corner_markets:
                    for market in corner_markets:
                        bet365_count = bet365_markets.get(market, 0)
                        print(f"      ✅ {market} (bet365: {bet365_count})")
                else:
                    print(f"      ❌ No corner-related markets found")
            else:
                print(f"   ❌ No inplay odds data")
        else:
            print(f"   ❌ API Error: {response.status_code}")
    
    except Exception as e:
        print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    test_specific_match_corner_odds() 