import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

class LiveOddsResolver:
    def __init__(self):
        self.api_key = os.getenv('SPORTMONKS_API_KEY')
        self.base_url = "https://api.sportmonks.com/v3/football"
        
    def test_match_id(self, match_id):
        """Test all aspects of live odds for a specific match"""
        
        print(f"🎯 RESOLVING LIVE ODDS FOR MATCH {match_id}")
        print("=" * 70)
        
        # Step 1: Get all available markets
        print("\n📊 STEP 1: Getting all available markets")
        corner_markets = self.get_all_markets()
        
        # Step 2: Test the correct inplay odds endpoint
        print(f"\n📊 STEP 2: Testing correct inplay odds endpoint")
        self.test_inplay_odds_endpoint(match_id)
        
        # Step 3: Test specific corner markets if found
        print(f"\n📊 STEP 3: Testing corner markets")
        if corner_markets:
            for market_id, market_name in corner_markets:
                self.test_specific_market(match_id, market_id, market_name)
        
        # Step 4: Check bookmakers
        print(f"\n📊 STEP 4: Checking available bookmakers")
        self.check_bookmakers()
        
    def get_all_markets(self):
        """Get all available markets and find corner-related ones"""
        
        url = f"{self.base_url}/markets"
        params = {'api_token': self.api_key}
        
        try:
            print(f"🌐 Fetching: {url}")
            response = requests.get(url, params=params, timeout=30)
            print(f"📡 Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json().get('data', [])
                print(f"📊 Total markets: {len(data)}")
                
                # Find corner-related markets
                corner_markets = []
                for market in data:
                    name = market.get('name', '').lower()
                    market_id = market.get('id')
                    dev_name = market.get('developer_name', '').lower()
                    
                    if 'corner' in name or 'corner' in dev_name:
                        corner_markets.append((market_id, market.get('name', 'Unknown')))
                        print(f"   ✅ Corner Market Found: ID {market_id} - {market.get('name')}")
                
                if not corner_markets:
                    print("   ❌ No corner-related markets found")
                    print("   📋 Sample markets (first 10):")
                    for i, market in enumerate(data[:10]):
                        print(f"      {market.get('id')}: {market.get('name', 'N/A')}")
                
                return corner_markets
                
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                return []
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return []
    
    def test_inplay_odds_endpoint(self, match_id):
        """Test the correct inplay odds endpoint structure"""
        
        # Correct endpoint from documentation
        url = f"{self.base_url}/odds/inplay/fixtures/{match_id}"
        params = {'api_token': self.api_key}
        
        try:
            print(f"🌐 Fetching: {url}")
            response = requests.get(url, params=params, timeout=30)
            print(f"📡 Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json().get('data', [])
                print(f"📊 Total inplay odds: {len(data)}")
                
                if data:
                    # Analyze available markets and bookmakers
                    markets = {}
                    bookmakers = {}
                    corner_odds = []
                    
                    for odds in data:
                        market_desc = odds.get('market_description', 'Unknown')
                        market_id = odds.get('market_id')
                        bookmaker_id = odds.get('bookmaker_id')
                        
                        # Track markets
                        if market_desc not in markets:
                            markets[market_desc] = {'count': 0, 'market_id': market_id}
                        markets[market_desc]['count'] += 1
                        
                        # Track bookmakers
                        if bookmaker_id not in bookmakers:
                            bookmakers[bookmaker_id] = 0
                        bookmakers[bookmaker_id] += 1
                        
                        # Look for corner odds
                        if 'corner' in market_desc.lower():
                            corner_odds.append({
                                'market_desc': market_desc,
                                'market_id': market_id,
                                'bookmaker_id': bookmaker_id,
                                'label': odds.get('label'),
                                'value': odds.get('value'),
                                'total': odds.get('total'),
                                'handicap': odds.get('handicap')
                            })
                    
                    print(f"\n🎯 CORNER ODDS FOUND: {len(corner_odds)}")
                    for corner in corner_odds:
                        print(f"   ✅ {corner['market_desc']} (ID: {corner['market_id']})")
                        print(f"      Bookmaker: {corner['bookmaker_id']} | {corner['label']}: {corner['value']}")
                        if corner['total']: print(f"      Total: {corner['total']}")
                        if corner['handicap']: print(f"      Handicap: {corner['handicap']}")
                        print()
                    
                    print(f"\n📋 ALL AVAILABLE MARKETS:")
                    for market, info in sorted(markets.items(), key=lambda x: x[1]['count'], reverse=True)[:15]:
                        print(f"   {market} (ID: {info['market_id']}): {info['count']} odds")
                    
                    print(f"\n📋 AVAILABLE BOOKMAKERS:")
                    for bookmaker_id, count in sorted(bookmakers.items(), key=lambda x: x[1], reverse=True):
                        status = "✅ bet365" if bookmaker_id == 2 else ""
                        print(f"   {bookmaker_id}: {count} odds {status}")
                    
                    # Show sample bet365 odds
                    bet365_odds = [odds for odds in data if odds.get('bookmaker_id') == 2]
                    if bet365_odds:
                        print(f"\n🎯 BET365 SAMPLE ODDS:")
                        for i, odds in enumerate(bet365_odds[:3]):
                            print(f"   {i+1}. {odds.get('market_description')} | {odds.get('label')}: {odds.get('value')}")
                    
                else:
                    print("❌ No inplay odds data returned")
            
            elif response.status_code == 404:
                print("❌ Match not found or no inplay odds available")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text[:500]}")
        
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    def test_specific_market(self, match_id, market_id, market_name):
        """Test a specific market for the match"""
        
        # Test market-specific endpoint
        url = f"{self.base_url}/odds/inplay/fixtures/{match_id}/markets/{market_id}"
        params = {'api_token': self.api_key}
        
        try:
            print(f"🔍 Testing Market {market_id}: {market_name}")
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json().get('data', [])
                bet365_odds = [odds for odds in data if odds.get('bookmaker_id') == 2]
                
                print(f"   ✅ Success: {len(data)} total odds, {len(bet365_odds)} bet365 odds")
                
                if bet365_odds:
                    print(f"   🎯 BET365 ODDS:")
                    for i, odds in enumerate(bet365_odds[:3]):
                        print(f"      {i+1}. {odds.get('label')}: {odds.get('value')}")
                        if odds.get('total'): print(f"         Total: {odds.get('total')}")
                        if odds.get('handicap'): print(f"         Handicap: {odds.get('handicap')}")
                
            elif response.status_code == 404:
                print(f"   ❌ Market not available for this match")
            else:
                print(f"   ❌ Error: {response.status_code}")
        
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    def check_bookmakers(self):
        """Check available bookmakers"""
        
        url = f"{self.base_url}/bookmakers"
        params = {'api_token': self.api_key}
        
        try:
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json().get('data', [])
                print(f"📊 Total bookmakers: {len(data)}")
                
                # Find bet365
                bet365_found = False
                for bookmaker in data:
                    name = bookmaker.get('name', '').lower()
                    bookmaker_id = bookmaker.get('id')
                    
                    if 'bet365' in name or bookmaker_id == 2:
                        print(f"   ✅ bet365 found: ID {bookmaker_id} - {bookmaker.get('name')}")
                        bet365_found = True
                
                if not bet365_found:
                    print("   ❌ bet365 not found")
                    print("   📋 Available bookmakers (first 10):")
                    for bookmaker in data[:10]:
                        print(f"      {bookmaker.get('id')}: {bookmaker.get('name', 'N/A')}")
            
            else:
                print(f"❌ Error fetching bookmakers: {response.status_code}")
        
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    def test_bet365_specific(self, match_id):
        """Test bet365-specific endpoint"""
        
        url = f"{self.base_url}/odds/inplay/fixtures/{match_id}/bookmakers/2"
        params = {'api_token': self.api_key}
        
        try:
            print(f"\n📊 TESTING BET365-SPECIFIC ENDPOINT")
            print(f"🌐 URL: {url}")
            
            response = requests.get(url, params=params, timeout=15)
            print(f"📡 Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json().get('data', [])
                print(f"📊 Total bet365 odds: {len(data)}")
                
                corner_odds = [odds for odds in data if 'corner' in odds.get('market_description', '').lower()]
                print(f"🎯 Corner odds from bet365: {len(corner_odds)}")
                
                for corner in corner_odds:
                    print(f"   ✅ {corner.get('market_description')} | {corner.get('label')}: {corner.get('value')}")
            
            else:
                print(f"❌ Error: {response.status_code}")
        
        except Exception as e:
            print(f"❌ Exception: {e}")

def main():
    """Main function to test live odds resolution"""
    
    resolver = LiveOddsResolver()
    
    # Test with the match that should have corner odds
    match_id = "19471693"  # The match from the screenshot
    
    print("🔍 LIVE ODDS RESOLUTION SCRIPT")
    print("=" * 50)
    print("This script will help us find the correct corner odds structure")
    print()
    
    resolver.test_match_id(match_id)
    
    # Also test bet365-specific endpoint
    resolver.test_bet365_specific(match_id)
    
    print("\n" + "=" * 70)
    print("✅ LIVE ODDS RESOLUTION COMPLETE")
    print("Check the output above to find the correct market IDs and structure")

if __name__ == "__main__":
    main() 