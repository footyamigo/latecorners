#!/usr/bin/env python3

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def show_complete_corner_odds():
    """Show complete corner odds data to find the specific totals/lines"""
    
    fixture_id = 19468975
    api_key = os.getenv('SPORTMONKS_API_KEY')
    
    print(f"🔍 COMPLETE CORNER ODDS BREAKDOWN FOR MATCH {fixture_id}")
    print(f"=" * 70)
    
    url = f"https://api.sportmonks.com/v3/football/odds/inplay/fixtures/{fixture_id}"
    params = {'api_token': api_key}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            all_odds = response.json().get('data', [])
            
            # Find bet365 Asian corner odds
            bet365_asian_corners = [
                odds for odds in all_odds 
                if odds.get('market_id') == 61 and odds.get('bookmaker_id') == 2
            ]
            
            print(f"🎯 BET365 ASIAN CORNER ODDS (4 found):")
            print(f"=" * 50)
            
            for i, odds in enumerate(bet365_asian_corners, 1):
                print(f"\n{i}. COMPLETE ODDS OBJECT:")
                print(json.dumps(odds, indent=2))
                print(f"-" * 30)
            
            # Try to identify the lines/totals
            print(f"\n📊 ANALYSIS:")
            print(f"=" * 50)
            
            over_odds = [odds for odds in bet365_asian_corners if odds.get('label') == 'Over']
            under_odds = [odds for odds in bet365_asian_corners if odds.get('label') == 'Under']
            
            print(f"Over odds: {len(over_odds)}")
            for odds in over_odds:
                value = odds.get('value')
                print(f"   Over = {value}")
                
                # Look for any field that might indicate the total
                for key in odds.keys():
                    if key not in ['market_id', 'bookmaker_id', 'market_description', 'label', 'value', 'probability']:
                        print(f"   Additional field '{key}': {odds[key]}")
            
            print(f"\nUnder odds: {len(under_odds)}")
            for odds in under_odds:
                value = odds.get('value')
                print(f"   Under = {value}")
                
                # Look for any field that might indicate the total
                for key in odds.keys():
                    if key not in ['market_id', 'bookmaker_id', 'market_description', 'label', 'value', 'probability']:
                        print(f"   Additional field '{key}': {odds[key]}")
            
            # Try to pair them by matching odds or other criteria
            print(f"\n🤔 PAIRING ANALYSIS:")
            print(f"=" * 50)
            
            if len(over_odds) == 2 and len(under_odds) == 2:
                print(f"We have 2 Over and 2 Under - likely 2 different lines")
                
                # Check if there are any fields that help identify the lines
                all_fields = set()
                for odds in bet365_asian_corners:
                    all_fields.update(odds.keys())
                
                print(f"All available fields: {sorted(all_fields)}")
                
                # Look for patterns
                print(f"\nPossible line identification:")
                for odds in bet365_asian_corners:
                    label = odds.get('label')
                    value = odds.get('value')
                    prob = odds.get('probability')
                    
                    # Check for any numeric fields that might be the total
                    numeric_fields = {}
                    for key, val in odds.items():
                        if isinstance(val, (int, float)) and key not in ['market_id', 'bookmaker_id', 'value', 'probability']:
                            numeric_fields[key] = val
                    
                    print(f"   {label} {value} (prob: {prob}%) - Extra numbers: {numeric_fields}")
                    
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"💥 Exception: {e}")

if __name__ == "__main__":
    show_complete_corner_odds() 