#!/usr/bin/env python3

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def show_detailed_odds():
    """Show detailed corner odds with market names and values"""
    
    fixture_id = 19468975
    api_key = os.getenv('SPORTMONKS_API_KEY')
    
    print(f"🔍 DETAILED ODDS ANALYSIS FOR MATCH {fixture_id}")
    print(f"=" * 70)
    
    # Use the same endpoint our dashboard uses
    url = f"https://api.sportmonks.com/v3/football/odds/inplay/fixtures/{fixture_id}"
    params = {'api_token': api_key}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        print(f"📡 API Status: {response.status_code}")
        
        if response.status_code == 200:
            all_odds = response.json().get('data', [])
            
            print(f"📊 Total odds found: {len(all_odds)}")
            
            if all_odds:
                # Separate odds by categories
                bet365_asian_corners = []
                other_corner_markets = []
                bet365_other_markets = []
                other_odds = []
                
                for odds in all_odds:
                    market_id = odds.get('market_id')
                    bookmaker_id = odds.get('bookmaker_id')
                    
                    if market_id == 61 and bookmaker_id == 2:  # bet365 Asian corners
                        bet365_asian_corners.append(odds)
                    elif market_id == 61:  # Other bookmaker Asian corners
                        other_corner_markets.append(odds)
                    elif bookmaker_id == 2:  # bet365 other markets
                        bet365_other_markets.append(odds)
                    else:  # Everything else
                        other_odds.append(odds)
                
                # Show bet365 Asian corners (our target)
                print(f"\n🎯 BET365 ASIAN CORNER ODDS (Market ID 61, Bookmaker ID 2):")
                print(f"Found {len(bet365_asian_corners)} odds")
                print(f"-" * 50)
                
                for i, odds in enumerate(bet365_asian_corners, 1):
                    market_desc = odds.get('market_description', 'Unknown Market')
                    label = odds.get('label', 'Unknown Label')
                    value = odds.get('value', 'N/A')
                    probability = odds.get('probability', 'N/A')
                    
                    print(f"{i}. Market: {market_desc}")
                    print(f"   Label: {label}")
                    print(f"   Value: {value}")
                    print(f"   Probability: {probability}")
                    print()
                
                # Show other corner markets for comparison
                if other_corner_markets:
                    print(f"📊 OTHER ASIAN CORNER MARKETS (Market ID 61, Other Bookmakers):")
                    print(f"Found {len(other_corner_markets)} odds")
                    print(f"-" * 50)
                    
                    for odds in other_corner_markets:
                        bookmaker_id = odds.get('bookmaker_id')
                        market_desc = odds.get('market_description', 'Unknown')
                        label = odds.get('label', 'Unknown')
                        value = odds.get('value', 'N/A')
                        
                        print(f"Bookmaker {bookmaker_id}: {market_desc} - {label} = {value}")
                
                # Show bet365 other markets
                if bet365_other_markets:
                    print(f"\n🏢 OTHER BET365 MARKETS (Bookmaker ID 2, Other Markets):")
                    print(f"Found {len(bet365_other_markets)} odds")
                    print(f"-" * 50)
                    
                    # Group by market
                    markets = {}
                    for odds in bet365_other_markets:
                        market_id = odds.get('market_id')
                        if market_id not in markets:
                            markets[market_id] = []
                        markets[market_id].append(odds)
                    
                    for market_id, market_odds in markets.items():
                        print(f"Market {market_id}: {len(market_odds)} odds")
                        sample = market_odds[0]
                        print(f"   Sample: {sample.get('market_description', 'Unknown')} - {sample.get('label', 'Unknown')} = {sample.get('value', 'N/A')}")
                
                # Summary
                print(f"\n" + "=" * 70)
                print(f"📋 SUMMARY:")
                print(f"   🎯 bet365 Asian corners (what we need): {len(bet365_asian_corners)}")
                print(f"   📊 Other Asian corner bookmakers: {len(other_corner_markets)}")
                print(f"   🏢 bet365 other markets: {len(bet365_other_markets)}")
                print(f"   📈 All other odds: {len(other_odds)}")
                print(f"   🔢 Total: {len(all_odds)}")
                
                if bet365_asian_corners:
                    print(f"\n✅ SUCCESS: Our system should detect and use these odds!")
                else:
                    print(f"\n❌ ISSUE: No bet365 Asian corner odds found")
                    
            else:
                print(f"❌ No odds data in response")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"💥 Exception: {e}")

if __name__ == "__main__":
    show_detailed_odds() 