#!/usr/bin/env python3

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_alternative_odds_endpoints():
    """Test different SportMonks endpoints to find odds"""
    
    match_id = 19406130
    api_key = os.getenv('SPORTMONKS_API_KEY')
    
    print(f"🔍 Testing alternative odds endpoints for match {match_id}")
    
    # Test different endpoints
    endpoints_to_test = [
        # Current endpoint (already tested)
        f"https://api.sportmonks.com/v3/football/odds/inplay/fixtures/{match_id}",
        
        # Alternative odds endpoints
        f"https://api.sportmonks.com/v3/football/odds/fixtures/{match_id}",
        f"https://api.sportmonks.com/v3/football/fixtures/{match_id}?include=odds",
        f"https://api.sportmonks.com/v3/football/fixtures/{match_id}?include=odds.bookmaker,odds.market",
    ]
    
    for i, url in enumerate(endpoints_to_test, 1):
        print(f"\n🔗 Endpoint {i}: {url}")
        
        try:
            params = {'api_token': api_key}
            response = requests.get(url, params=params, timeout=10)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for odds in different data structures
                odds_found = 0
                
                # Direct odds array
                if 'data' in data and isinstance(data['data'], list):
                    odds_found = len(data['data'])
                    print(f"   Direct odds: {odds_found}")
                
                # Nested odds in fixture data
                elif 'data' in data and isinstance(data['data'], dict):
                    fixture_data = data['data']
                    if 'odds' in fixture_data:
                        if isinstance(fixture_data['odds'], list):
                            odds_found = len(fixture_data['odds'])
                            print(f"   Nested odds: {odds_found}")
                        else:
                            print(f"   Odds structure: {type(fixture_data['odds'])}")
                    else:
                        print("   No 'odds' key in fixture data")
                        print(f"   Available keys: {list(fixture_data.keys())}")
                
                if odds_found > 0:
                    print(f"   ✅ FOUND {odds_found} odds!")
                    
                    # Show sample odds structure
                    sample_odds = None
                    if isinstance(data['data'], list) and data['data']:
                        sample_odds = data['data'][0]
                    elif isinstance(data['data'], dict) and 'odds' in data['data'] and data['data']['odds']:
                        sample_odds = data['data']['odds'][0]
                    
                    if sample_odds:
                        print(f"   Sample odds: {sample_odds}")
                        
                        # Check for corner markets
                        market_id = sample_odds.get('market_id')
                        bookmaker_id = sample_odds.get('bookmaker_id')
                        print(f"   Market ID: {market_id}, Bookmaker ID: {bookmaker_id}")
                
            else:
                print(f"   ❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print(f"\n🤔 Summary:")
    print(f"If all endpoints return 0 odds, this match likely has no betting markets available.")
    print(f"Try testing with a more popular match (Premier League, etc.) to verify the system works.")

if __name__ == "__main__":
    test_alternative_odds_endpoints() 