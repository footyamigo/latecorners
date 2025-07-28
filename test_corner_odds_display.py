import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

class CornerOddsDisplayer:
    def __init__(self):
        self.api_key = os.getenv('SPORTMONKS_API_KEY')
        self.base_url = "https://api.sportmonks.com/v3/football"
    
    def find_target_match(self):
        """Find the North Lakes vs Sunshine Coast match"""
        url = f"{self.base_url}/livescores/inplay"
        params = {
            'api_token': self.api_key,
            'include': 'participants;state;periods'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code != 200:
                print(f"❌ API Error: {response.status_code}")
                return None
                
            matches = response.json().get('data', [])
            print(f"🔍 Searching through {len(matches)} live matches...")
            
            for match in matches:
                participants = match.get('participants', [])
                home_team = ""
                away_team = ""
                
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
                    print(f"✅ FOUND TARGET MATCH!")
                    print(f"   🏠 Home: {home_team}")
                    print(f"   🚗 Away: {away_team}")
                    print(f"   🆔 Match ID: {match['id']}")
                    return match['id']
            
            print("❌ Target match not found in current live matches")
            print("\n📋 Available matches (first 10):")
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
                
                print(f"   {i+1:2d}. {home_team} vs {away_team}")
            
            return None
            
        except Exception as e:
            print(f"❌ Error finding match: {e}")
            return None
    
    def get_asian_corner_odds(self, match_id):
        """Get Asian corner odds for the match"""
        print(f"\n🎯 FETCHING ASIAN CORNER ODDS FOR MATCH {match_id}")
        print("=" * 70)
        
        # Market 61: Asian Total Corners
        print("\n📊 MARKET 61: ASIAN TOTAL CORNERS")
        print("-" * 40)
        self._fetch_market_odds(match_id, 61, "Asian Total Corners")
        
        # Market 62: Asian Handicap Corners
        print("\n📊 MARKET 62: ASIAN HANDICAP CORNERS")
        print("-" * 40)
        self._fetch_market_odds(match_id, 62, "Asian Handicap Corners")
        
        # Also get general inplay odds to see what's available
        print("\n🔍 ALL INPLAY ODDS FOR THIS MATCH:")
        print("-" * 40)
        self._get_all_inplay_odds(match_id)
    
    def _fetch_market_odds(self, match_id, market_id, market_name):
        """Fetch odds for a specific market"""
        url = f"{self.base_url}/odds/inplay/fixtures/{match_id}/markets/{market_id}"
        params = {'api_token': self.api_key}
        
        try:
            response = requests.get(url, params=params, timeout=15)
            print(f"🌐 API URL: {url}")
            print(f"📡 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                odds_data = response.json().get('data', [])
                print(f"📊 Total odds entries: {len(odds_data)}")
                
                if not odds_data:
                    print("❌ No odds data available for this market")
                    return
                
                # Filter for bet365 (bookmaker_id = 2)
                bet365_odds = [odds for odds in odds_data if odds.get('bookmaker_id') == 2]
                print(f"🎯 bet365 odds: {len(bet365_odds)}")
                
                if bet365_odds:
                    print(f"\n✅ BET365 {market_name.upper()} ODDS:")
                    for i, odds in enumerate(bet365_odds, 1):
                        print(f"   {i:2d}. Label: {odds.get('label', 'N/A')}")
                        print(f"       Value (Decimal): {odds.get('value', 'N/A')}")
                        print(f"       Total: {odds.get('total', 'N/A')}")
                        print(f"       Handicap: {odds.get('handicap', 'N/A')}")
                        print(f"       Market Desc: {odds.get('market_description', 'N/A')}")
                        print()
                else:
                    print("❌ No bet365 odds found for this market")
                    
                    # Show what bookmakers are available
                    bookmaker_ids = set(odds.get('bookmaker_id') for odds in odds_data if odds.get('bookmaker_id'))
                    if bookmaker_ids:
                        print(f"📋 Available bookmakers: {sorted(list(bookmaker_ids))}")
                        
                        # Show sample from first available bookmaker
                        sample_odds = odds_data[0]
                        print(f"\n📝 SAMPLE ODDS (Bookmaker {sample_odds.get('bookmaker_id')}):")
                        print(f"   Label: {sample_odds.get('label', 'N/A')}")
                        print(f"   Value: {sample_odds.get('value', 'N/A')}")
                        print(f"   Total: {sample_odds.get('total', 'N/A')}")
                        print(f"   Handicap: {sample_odds.get('handicap', 'N/A')}")
            
            elif response.status_code == 404:
                print(f"❌ Market {market_id} not found for this match")
            elif response.status_code == 422:
                print(f"❌ Invalid request - check market ID or match ID")
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ Exception fetching market {market_id}: {e}")
    
    def _get_all_inplay_odds(self, match_id):
        """Get all available inplay odds to see what markets exist"""
        url = f"{self.base_url}/odds/inplay/fixtures/{match_id}"
        params = {'api_token': self.api_key}
        
        try:
            response = requests.get(url, params=params, timeout=15)
            print(f"📡 Status: {response.status_code}")
            
            if response.status_code == 200:
                odds_data = response.json().get('data', [])
                print(f"📊 Total inplay odds: {len(odds_data)}")
                
                if not odds_data:
                    print("❌ No inplay odds available")
                    return
                
                # Analyze markets
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
                
                print(f"\n📋 ALL AVAILABLE MARKETS:")
                for market, count in sorted(markets.items()):
                    bet365_count = bet365_markets.get(market, 0)
                    status = f"✅ bet365: {bet365_count}" if bet365_count > 0 else "❌ no bet365"
                    print(f"   {market}: {count} ({status})")
                
                # Highlight corner markets
                corner_markets = [m for m in markets.keys() if 'corner' in m.lower()]
                if corner_markets:
                    print(f"\n🎯 CORNER-RELATED MARKETS:")
                    for market in corner_markets:
                        bet365_count = bet365_markets.get(market, 0)
                        status = "✅" if bet365_count > 0 else "❌"
                        print(f"   {status} {market} (bet365: {bet365_count})")
            else:
                print(f"❌ Error getting inplay odds: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception getting inplay odds: {e}")

def main():
    print("🎯 ASIAN CORNER ODDS DISPLAY")
    print("=" * 50)
    print("🔍 Looking for: North Lakes United W vs Sunshine Coast Wanderers W")
    
    displayer = CornerOddsDisplayer()
    
    # Find the match
    match_id = displayer.find_target_match()
    
    if match_id:
        # Get the corner odds
        displayer.get_asian_corner_odds(match_id)
    else:
        print("\n❌ Cannot proceed without match ID")

if __name__ == "__main__":
    main() 