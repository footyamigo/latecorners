import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

def debug_corner_odds():
    """Debug corner odds APIs to find the correct structure"""
    
    api_key = os.getenv('SPORTMONKS_API_KEY')
    match_id = "19339501"  # North Lakes vs Sunshine Coast match ID
    
    print("🔍 DEBUGGING CORNER ODDS APIs")
    print("=" * 60)
    print(f"🎯 Target Match ID: {match_id}")
    
    # Test 1: General inplay odds for the match
    print("\n📊 TEST 1: General Inplay Odds")
    print("-" * 40)
    test_general_inplay_odds(match_id, api_key)
    
    # Test 2: Try different market IDs
    print("\n📊 TEST 2: Testing Market IDs")
    print("-" * 40)
    market_ids_to_test = [61, 62, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    for market_id in market_ids_to_test:
        test_market_id(match_id, market_id, api_key)
    
    # Test 3: Check available markets
    print("\n📊 TEST 3: Get All Available Markets")
    print("-" * 40)
    get_all_markets(api_key)
    
    # Test 4: Check available bookmakers
    print("\n📊 TEST 4: Get All Bookmakers")
    print("-" * 40)
    get_all_bookmakers(api_key)

def test_general_inplay_odds(match_id, api_key):
    """Test general inplay odds endpoint"""
    
    url = f"https://api.sportmonks.com/v3/football/odds/inplay/fixtures/{match_id}"
    params = {'api_token': api_key}
    
    try:
        response = requests.get(url, params=params, timeout=15)
        print(f"🌐 URL: {url}")
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json().get('data', [])
            print(f"📊 Total odds: {len(data)}")
            
            if data:
                # Analyze markets and bookmakers
                markets = {}
                bookmakers = {}
                corner_related = []
                
                for odds in data:
                    market_desc = odds.get('market_description', 'Unknown')
                    bookmaker_id = odds.get('bookmaker_id', 0)
                    
                    if market_desc not in markets:
                        markets[market_desc] = 0
                    markets[market_desc] += 1
                    
                    if bookmaker_id not in bookmakers:
                        bookmakers[bookmaker_id] = 0
                    bookmakers[bookmaker_id] += 1
                    
                    # Look for corner-related odds
                    if 'corner' in market_desc.lower():
                        corner_related.append({
                            'market': market_desc,
                            'bookmaker': bookmaker_id,
                            'label': odds.get('label', 'N/A'),
                            'value': odds.get('value', 'N/A')
                        })
                
                print(f"🎯 CORNER ODDS FOUND: {len(corner_related)}")
                for corner in corner_related:
                    print(f"   ✅ {corner['market']} | {corner['label']}: {corner['value']} (Bookmaker: {corner['bookmaker']})")
                
                print(f"\n📋 TOP MARKETS:")
                for market, count in sorted(markets.items(), key=lambda x: x[1], reverse=True)[:10]:
                    print(f"   {market}: {count}")
                
                print(f"\n📋 BOOKMAKERS:")
                for bookmaker, count in sorted(bookmakers.items(), key=lambda x: x[1], reverse=True)[:10]:
                    print(f"   {bookmaker}: {count}")
            else:
                print("❌ No odds data")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
    
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_market_id(match_id, market_id, api_key):
    """Test specific market ID"""
    
    url = f"https://api.sportmonks.com/v3/football/odds/inplay/fixtures/{match_id}/markets/{market_id}"
    params = {'api_token': api_key}
    
    try:
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json().get('data', [])
            if data:
                print(f"   ✅ Market {market_id}: {len(data)} odds")
                # Show first example
                sample = data[0]
                print(f"      Example: {sample.get('market_description', 'N/A')} | {sample.get('label', 'N/A')}")
            else:
                print(f"   ❌ Market {market_id}: No data")
        elif response.status_code == 404:
            print(f"   ❌ Market {market_id}: Not found")
        else:
            print(f"   ❌ Market {market_id}: Error {response.status_code}")
    
    except Exception as e:
        print(f"   ❌ Market {market_id}: Exception")

def get_all_markets(api_key):
    """Get all available markets from SportMonks"""
    
    url = "https://api.sportmonks.com/v3/football/markets"
    params = {'api_token': api_key}
    
    try:
        response = requests.get(url, params=params, timeout=15)
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json().get('data', [])
            print(f"📊 Total markets: {len(data)}")
            
            corner_markets = []
            for market in data:
                name = market.get('name', '')
                market_id = market.get('id', '')
                if 'corner' in name.lower():
                    corner_markets.append(f"ID {market_id}: {name}")
            
            print(f"🎯 CORNER MARKETS FOUND:")
            for corner in corner_markets:
                print(f"   ✅ {corner}")
                
        else:
            print(f"❌ Error: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Exception: {e}")

def get_all_bookmakers(api_key):
    """Get all available bookmakers"""
    
    url = "https://api.sportmonks.com/v3/football/bookmakers"
    params = {'api_token': api_key}
    
    try:
        response = requests.get(url, params=params, timeout=15)
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json().get('data', [])
            print(f"📊 Total bookmakers: {len(data)}")
            
            # Look for bet365
            bet365_found = False
            for bookmaker in data:
                name = bookmaker.get('name', '')
                bookmaker_id = bookmaker.get('id', '')
                if 'bet365' in name.lower() or bookmaker_id == 2:
                    print(f"   ✅ bet365 found: ID {bookmaker_id} - {name}")
                    bet365_found = True
            
            if not bet365_found:
                print("   ❌ bet365 not found in bookmakers list")
                print("   📋 Available bookmakers (first 10):")
                for i, bookmaker in enumerate(data[:10]):
                    print(f"      {bookmaker.get('id', 'N/A')}: {bookmaker.get('name', 'N/A')}")
                
        else:
            print(f"❌ Error: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    debug_corner_odds() 