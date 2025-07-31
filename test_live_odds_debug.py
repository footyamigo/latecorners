#!/usr/bin/env python3

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_odds_for_live_match():
    """Test what odds are actually available for the live match"""
    
    # The live match ID from your logs
    match_id = 19406130
    api_key = os.getenv('SPORTMONKS_API_KEY')
    
    print(f"🔍 Testing odds for live match {match_id} (Ekwendeni Hammers vs Big Bullets)")
    print(f"API Key: {api_key[:10]}..." if api_key else "❌ No API Key")
    
    # Test the same endpoint our dashboard uses
    url = f"https://api.sportmonks.com/v3/football/odds/inplay/fixtures/{match_id}"
    params = {'api_token': api_key}
    
    try:
        print(f"\n🌐 Making request to: {url}")
        response = requests.get(url, params=params, timeout=10)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            all_odds = data.get('data', [])
            
            print(f"📈 Total odds found: {len(all_odds)}")
            
            if all_odds:
                print("\n🎯 ODDS BREAKDOWN:")
                
                # Group by market and bookmaker
                markets = {}
                bookmakers = {}
                
                for odds in all_odds:
                    market_id = odds.get('market_id')
                    bookmaker_id = odds.get('bookmaker_id')
                    
                    # Count markets
                    if market_id not in markets:
                        markets[market_id] = 0
                    markets[market_id] += 1
                    
                    # Count bookmakers
                    if bookmaker_id not in bookmakers:
                        bookmakers[bookmaker_id] = 0
                    bookmakers[bookmaker_id] += 1
                
                print("📊 Markets found:")
                for market_id, count in sorted(markets.items()):
                    marker = " ⭐" if market_id == 61 else ""
                    print(f"   Market {market_id}: {count} odds{marker}")
                
                print("\n🏢 Bookmakers found:")
                for bookmaker_id, count in sorted(bookmakers.items()):
                    marker = " ⭐" if bookmaker_id == 2 else ""
                    name = "bet365" if bookmaker_id == 2 else f"Bookmaker {bookmaker_id}"
                    print(f"   {name}: {count} odds{marker}")
                
                # Check our specific requirement
                corner_odds = 0
                bet365_corner_odds = 0
                
                for odds in all_odds:
                    if odds.get('market_id') == 61:  # Asian Total Corners
                        corner_odds += 1
                        if odds.get('bookmaker_id') == 2:  # bet365
                            bet365_corner_odds += 1
                
                print(f"\n🎯 OUR REQUIREMENTS:")
                print(f"   Market 61 (Asian Total Corners): {corner_odds} odds")
                print(f"   bet365 Asian Corner odds: {bet365_corner_odds} odds")
                
                if bet365_corner_odds > 0:
                    print("✅ MATCH SHOULD SHOW 'WITH ODDS'!")
                else:
                    print("❌ No bet365 Asian corner odds - explaining dashboard '0 WITH ODDS'")
                    
                    if corner_odds > 0:
                        print("💡 Asian corner markets exist, but not from bet365")
                    else:
                        print("💡 No Asian corner markets at all - try other market types")
                
            else:
                print("❌ No odds data returned")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_odds_for_live_match() 