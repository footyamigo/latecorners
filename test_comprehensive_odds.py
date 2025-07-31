#!/usr/bin/env python3

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_comprehensive_odds():
    """Comprehensive test to debug odds API calls"""
    
    match_id = 19406130
    api_key = os.getenv('SPORTMONKS_API_KEY')
    
    print(f"🔍 COMPREHENSIVE ODDS TEST for match {match_id}")
    print(f"🔑 API Key: {api_key[:10]}..." if api_key else "❌ No API Key")
    
    # Test the exact endpoint from SportMonks documentation
    base_url = f"https://api.sportmonks.com/v3/football/odds/inplay/fixtures/{match_id}"
    
    # Test different parameter combinations
    test_cases = [
        # Case 1: Basic call (what we currently do)
        {
            "name": "Basic Call (Current)",
            "params": {"api_token": api_key}
        },
        
        # Case 2: Include market and bookmaker data
        {
            "name": "With Market & Bookmaker Includes", 
            "params": {
                "api_token": api_key,
                "include": "market,bookmaker"
            }
        },
        
        # Case 3: Include selections
        {
            "name": "With Selections",
            "params": {
                "api_token": api_key,
                "include": "selections"
            }
        },
        
        # Case 4: All includes
        {
            "name": "All Includes",
            "params": {
                "api_token": api_key,
                "include": "market,bookmaker,selections"
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"🧪 TEST {i}: {test_case['name']}")
        print(f"{'='*60}")
        
        try:
            # Make the request
            print(f"🌐 URL: {base_url}")
            print(f"📊 Params: {test_case['params']}")
            
            response = requests.get(base_url, params=test_case['params'], timeout=15)
            
            print(f"📡 Status Code: {response.status_code}")
            print(f"🕐 Response Time: {response.elapsed.total_seconds():.2f}s")
            
            if response.status_code == 200:
                data = response.json()
                
                # Analyze the response structure
                print(f"📋 Response Structure:")
                if 'data' in data:
                    odds_data = data['data']
                    print(f"   📈 Total odds: {len(odds_data)}")
                    
                    if odds_data:
                        print(f"   🎯 First odds sample:")
                        first_odds = odds_data[0]
                        
                        # Show key fields
                        key_fields = ['market_id', 'bookmaker_id', 'market_description', 'label', 'value']
                        for field in key_fields:
                            if field in first_odds:
                                print(f"      {field}: {first_odds[field]}")
                        
                        # Count markets and bookmakers
                        markets = set()
                        bookmakers = set()
                        corner_related = 0
                        
                        for odds in odds_data:
                            if 'market_id' in odds:
                                markets.add(odds['market_id'])
                            if 'bookmaker_id' in odds:
                                bookmakers.add(odds['bookmaker_id'])
                            
                            # Check for corner-related markets
                            market_desc = odds.get('market_description', '').lower()
                            if 'corner' in market_desc:
                                corner_related += 1
                        
                        print(f"   📊 Unique markets: {sorted(markets)}")
                        print(f"   🏢 Unique bookmakers: {sorted(bookmakers)}")
                        print(f"   ⚽ Corner-related odds: {corner_related}")
                        
                        # Check specifically for bet365 (ID 2) and Asian corners (ID 61)
                        bet365_odds = len([o for o in odds_data if o.get('bookmaker_id') == 2])
                        asian_corner_odds = len([o for o in odds_data if o.get('market_id') == 61])
                        bet365_asian_corners = len([o for o in odds_data if o.get('bookmaker_id') == 2 and o.get('market_id') == 61])
                        
                        print(f"   🎯 bet365 odds (ID 2): {bet365_odds}")
                        print(f"   🎯 Asian corner odds (ID 61): {asian_corner_odds}")  
                        print(f"   🎯 bet365 Asian corners: {bet365_asian_corners}")
                        
                        if bet365_asian_corners > 0:
                            print(f"   ✅ SHOULD SHOW 'WITH ODDS' IN DASHBOARD!")
                        else:
                            print(f"   ❌ Dashboard shows '0 WITH ODDS' correctly")
                            
                    else:
                        print(f"   ❌ No odds in response")
                        
                    # Show additional response fields
                    other_fields = [k for k in data.keys() if k != 'data']
                    if other_fields:
                        print(f"   📝 Other response fields: {other_fields}")
                        
                else:
                    print(f"   ❌ No 'data' field in response")
                    print(f"   📝 Response keys: {list(data.keys())}")
                    
            elif response.status_code == 429:
                print(f"   ⏱️ Rate limited")
            else:
                print(f"   ❌ Error response")
                print(f"   📄 Response text: {response.text[:200]}...")
                
        except Exception as e:
            print(f"   💥 Exception: {e}")
    
    print(f"\n{'='*60}")
    print(f"🎯 CONCLUSION")
    print(f"{'='*60}")
    print(f"If all tests show 0 odds but you confirmed odds exist:")
    print(f"1. Check if match is still live")
    print(f"2. Verify the exact fixture ID")
    print(f"3. Check if different endpoint/parameters needed")
    print(f"4. Verify API permissions for odds data")

if __name__ == "__main__":
    test_comprehensive_odds() 