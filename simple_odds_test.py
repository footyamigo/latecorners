import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_live_odds():
    api_key = os.getenv('SPORTMONKS_API_KEY')
    match_id = "19471693"  # The match from the screenshot
    
    print(f"🎯 Testing Live Odds for Match {match_id}")
    print("=" * 50)
    
    # Test the correct inplay odds endpoint from SportMonks documentation
    url = f"https://api.sportmonks.com/v3/football/odds/inplay/fixtures/{match_id}"
    params = {'api_token': api_key}
    
    try:
        print(f"🌐 URL: {url}")
        response = requests.get(url, params=params, timeout=30)
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json().get('data', [])
            print(f"📊 Total odds returned: {len(data)}")
            
            if data:
                # Analyze markets
                markets = {}
                corner_odds = []
                bet365_odds = []
                
                for odds in data:
                    market_desc = odds.get('market_description', 'Unknown')
                    bookmaker_id = odds.get('bookmaker_id', 0)
                    
                    if market_desc not in markets:
                        markets[market_desc] = 0
                    markets[market_desc] += 1
                    
                    # Check for corner odds
                    if 'corner' in market_desc.lower():
                        corner_odds.append(odds)
                    
                    # Check for bet365 odds
                    if bookmaker_id == 2:
                        bet365_odds.append(odds)
                
                print(f"\n🎯 CORNER ODDS FOUND: {len(corner_odds)}")
                for corner in corner_odds:
                    print(f"   ✅ {corner.get('market_description')} | Bookmaker: {corner.get('bookmaker_id')}")
                    print(f"      Label: {corner.get('label')} | Value: {corner.get('value')}")
                    if corner.get('total'): print(f"      Total: {corner.get('total')}")
                    if corner.get('handicap'): print(f"      Handicap: {corner.get('handicap')}")
                    print()
                
                print(f"🎯 BET365 ODDS FOUND: {len(bet365_odds)}")
                bet365_corner = [odds for odds in bet365_odds if 'corner' in odds.get('market_description', '').lower()]
                print(f"🎯 BET365 CORNER ODDS: {len(bet365_corner)}")
                
                for corner in bet365_corner:
                    print(f"   ✅ {corner.get('market_description')}")
                    print(f"      Label: {corner.get('label')} | Value: {corner.get('value')}")
                    if corner.get('total'): print(f"      Total: {corner.get('total')}")
                    if corner.get('handicap'): print(f"      Handicap: {corner.get('handicap')}")
                
                print(f"\n📋 TOP 10 AVAILABLE MARKETS:")
                for market, count in sorted(markets.items(), key=lambda x: x[1], reverse=True)[:10]:
                    print(f"   {market}: {count} odds")
                
                # Show all bookmakers
                bookmakers = {}
                for odds in data:
                    bid = odds.get('bookmaker_id', 0)
                    if bid not in bookmakers:
                        bookmakers[bid] = 0
                    bookmakers[bid] += 1
                
                print(f"\n📋 AVAILABLE BOOKMAKERS:")
                for bid, count in sorted(bookmakers.items(), key=lambda x: x[1], reverse=True):
                    status = " ✅ (bet365)" if bid == 2 else ""
                    print(f"   Bookmaker {bid}: {count} odds{status}")
            
            else:
                print("❌ No odds data returned")
        
        elif response.status_code == 404:
            print("❌ Match not found or no inplay odds available")
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text[:300]}")
    
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_live_odds() 