#!/usr/bin/env python3

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def compare_odds_endpoints():
    """Compare odds between fixture endpoint vs in-play odds endpoint"""
    
    api_key = os.getenv('SPORTMONKS_API_KEY')
    
    print(f"🎯 COMPARING ODDS ENDPOINTS")
    print(f"Goal: See if fixture endpoint has odds when in-play endpoint doesn't\n")
    
    # Get some live matches to test
    live_url = "https://api.sportmonks.com/v3/football/livescores/inplay"
    live_params = {"api_token": api_key}
    
    try:
        live_response = requests.get(live_url, params=live_params, timeout=10)
        
        if live_response.status_code == 200:
            live_data = live_response.json()
            live_matches = live_data.get('data', [])
            
            print(f"📡 Found {len(live_matches)} live matches")
            
            # Test first match with both endpoints
            if live_matches:
                test_match = live_matches[0]
                fixture_id = test_match.get('id')
                
                print(f"\n🧪 Testing fixture {fixture_id} with BOTH endpoints:")
                print(f"=" * 60)
                
                # Test 1: In-play odds endpoint (currently failing)
                print(f"🔴 TEST 1: In-play odds endpoint")
                test_inplay_odds(fixture_id, api_key)
                
                print(f"\n" + "=" * 60)
                
                # Test 2: Regular fixture endpoint with odds include
                print(f"🟢 TEST 2: Regular fixture endpoint with odds")
                test_fixture_odds(fixture_id, api_key)
                
            else:
                print("❌ No live matches to test")
                
        else:
            print(f"❌ Failed to get live matches: {live_response.status_code}")
            
    except Exception as e:
        print(f"💥 Exception: {e}")

def test_inplay_odds(fixture_id, api_key):
    """Test in-play odds endpoint (currently failing)"""
    
    url = f"https://api.sportmonks.com/v3/football/odds/inplay/fixtures/{fixture_id}"
    params = {"api_token": api_key}
    
    try:
        print(f"🌐 URL: {url}")
        response = requests.get(url, params=params, timeout=10)
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and data['data']:
                odds_count = len(data['data'])
                print(f"✅ SUCCESS: {odds_count} odds found")
                
                # Check for our target odds
                bet365_asian_corners = [
                    odds for odds in data['data'] 
                    if odds.get('bookmaker_id') == 2 and odds.get('market_id') == 61
                ]
                print(f"🎯 bet365 Asian corners: {len(bet365_asian_corners)}")
                
            else:
                print(f"❌ FAILED: No odds data")
                if 'message' in data:
                    print(f"   Message: {data['message']}")
                    
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            print(f"   Response: {response.text[:100]}")
            
    except Exception as e:
        print(f"💥 Exception: {e}")

def test_fixture_odds(fixture_id, api_key):
    """Test regular fixture endpoint with odds include"""
    
    url = f"https://api.sportmonks.com/v3/football/fixtures/{fixture_id}"
    params = {
        "api_token": api_key,
        "include": "odds"
    }
    
    try:
        print(f"🌐 URL: {url}")
        print(f"📋 Include: odds")
        response = requests.get(url, params=params, timeout=15)
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data:
                fixture_data = data['data']
                
                if 'odds' in fixture_data and fixture_data['odds']:
                    odds_count = len(fixture_data['odds'])
                    print(f"✅ SUCCESS: {odds_count} odds found in fixture data")
                    
                    # Check for our target odds
                    all_odds = fixture_data['odds']
                    bet365_asian_corners = [
                        odds for odds in all_odds 
                        if odds.get('bookmaker_id') == 2 and odds.get('market_id') == 61
                    ]
                    print(f"🎯 bet365 Asian corners: {len(bet365_asian_corners)}")
                    
                    if bet365_asian_corners:
                        print(f"🎉 FOUND TARGET ODDS! Our system should work with fixture endpoint")
                        
                        # Show sample
                        sample = bet365_asian_corners[0]
                        print(f"   Sample: {sample.get('market_description', 'Unknown')} = {sample.get('value', 'N/A')}")
                        
                    # Show breakdown of what's available
                    markets = {}
                    bookmakers = {}
                    
                    for odds in all_odds:
                        market_id = odds.get('market_id')
                        bookmaker_id = odds.get('bookmaker_id')
                        
                        if market_id not in markets:
                            markets[market_id] = 0
                        markets[market_id] += 1
                        
                        if bookmaker_id not in bookmakers:
                            bookmakers[bookmaker_id] = 0
                        bookmakers[bookmaker_id] += 1
                    
                    print(f"\n📊 BREAKDOWN:")
                    print(f"   Markets: {dict(sorted(markets.items()))}")
                    print(f"   Bookmakers: {dict(sorted(bookmakers.items()))}")
                    
                    # Highlight key IDs
                    if 2 in bookmakers:
                        print(f"   ✅ bet365 (ID 2): {bookmakers[2]} odds")
                    if 61 in markets:
                        print(f"   ✅ Asian corners (ID 61): {markets[61]} odds")
                        
                else:
                    print(f"❌ FAILED: No odds in fixture data")
                    print(f"   Available keys: {list(fixture_data.keys())}")
                    
            else:
                print(f"❌ FAILED: No data in response")
                print(f"   Response keys: {list(data.keys())}")
                
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            print(f"   Response: {response.text[:100]}")
            
    except Exception as e:
        print(f"💥 Exception: {e}")

if __name__ == "__main__":
    compare_odds_endpoints() 