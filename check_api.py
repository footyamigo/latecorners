#!/usr/bin/env python3

import requests
import json

def check_api_response():
    """Check what the API returns for live matches"""
    
    try:
        response = requests.get('http://localhost:8080/api/live-matches')
        data = response.json()
        
        print(f"🔍 API RESPONSE CHECK")
        print(f"=" * 50)
        print(f"Total matches: {len(data['matches'])}")
        
        # Look for Khan Tengri match specifically
        khan_match = None
        for match in data['matches']:
            if 'Khan Tengri' in match.get('home_team', ''):
                khan_match = match
                break
        
        if khan_match:
            print(f"\n🎯 KHAN TENGRI MATCH FOUND:")
            print(f"   ID: {khan_match.get('match_id')}")
            print(f"   Teams: {khan_match.get('home_team')} vs {khan_match.get('away_team')}")
            print(f"   Minute: {khan_match.get('minute')}")
            print(f"   Has corner_odds: {'corner_odds' in khan_match}")
            
            if 'corner_odds' in khan_match:
                corner_odds = khan_match['corner_odds']
                print(f"\n📊 CORNER ODDS DATA:")
                print(f"   Available: {corner_odds.get('available')}")
                print(f"   Count: {corner_odds.get('count')}")
                print(f"   Active count: {corner_odds.get('active_count')}")
                print(f"   Full data: {corner_odds}")
            else:
                print(f"\n❌ NO CORNER_ODDS DATA ATTACHED TO MATCH")
                print(f"   Available keys: {list(khan_match.keys())}")
        else:
            print(f"\n❌ Khan Tengri match not found")
            print(f"Available matches:")
            for match in data['matches'][:3]:
                print(f"   - {match.get('home_team')} vs {match.get('away_team')} ({match.get('minute')}')")
                
    except Exception as e:
        print(f"💥 Error: {e}")

if __name__ == "__main__":
    check_api_response() 