#!/usr/bin/env python3

"""
Test script to see ALL live matches (no filtering)
This helps verify the Sportmonks API is working with real live data
"""

import sys
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print("✅ Loaded .env file")
    else:
        print("❌ No .env file found!")
        sys.exit(1)
except ImportError:
    print("Installing python-dotenv...")
    import os
    os.system("pip install python-dotenv")
    from dotenv import load_dotenv
    load_dotenv()

def test_all_live_matches():
    try:
        import requests
        import time
        import os
        
        api_key = os.getenv('SPORTMONKS_API_KEY')
        if not api_key:
            print("❌ No SPORTMONKS_API_KEY found in .env file!")
            return False
        
        print("🧪 Testing Sportmonks API with ALL live matches...")
        print(f"🔑 API Key: {api_key[:10]}... (showing first 10 chars)")
        
        # Make direct API call to see ALL live matches
        url = "https://api.sportmonks.com/v3/football/livescores/inplay"
        params = {'api_token': api_key}
        
        print("📡 Calling Sportmonks API...")
        response = requests.get(url, params=params)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            matches = data.get('data', [])
            
            print(f"✅ API call successful - found {len(matches)} total live matches")
            
            if len(matches) > 0:
                print("\n📋 ALL Live Matches (no filtering):")
                print("─" * 80)
                
                for i, match in enumerate(matches[:10]):  # Show first 10
                    fixture_id = match.get('id', 'Unknown')
                    minute = match.get('minute', 0)
                    state = match.get('state', {}).get('short_name', 'Unknown')
                    
                    # Try to get team info
                    participants = match.get('participants', [])
                    home_team = "Unknown"
                    away_team = "Unknown"
                    
                    for participant in participants:
                        if participant.get('meta', {}).get('location') == 'home':
                            home_team = participant.get('name', 'Home Team')
                        else:
                            away_team = participant.get('name', 'Away Team')
                    
                    # Get score
                    scores = match.get('scores', [])
                    score = "0-0"
                    for score_data in scores:
                        if score_data.get('description') == 'CURRENT':
                            goals = score_data.get('score', {}).get('goals', {})
                            home_score = goals.get('home', 0)
                            away_score = goals.get('away', 0)
                            score = f"{home_score}-{away_score}"
                            break
                    
                    print(f"{i+1:2d}. {home_team} vs {away_team}")
                    print(f"    Score: {score} | Minute: {minute}' | State: {state} | ID: {fixture_id}")
                    
                    # Highlight matches that would qualify for monitoring
                    if minute >= 70 and state in ['2H', 'HT']:
                        print("    🎯 ← This match would be monitored by our system!")
                    
                    print()
                
                if len(matches) > 10:
                    print(f"... and {len(matches) - 10} more matches")
                
                # Count matches that would qualify for our system
                qualifying_matches = 0
                for match in matches:
                    minute = match.get('minute', 0)
                    state = match.get('state', {}).get('short_name', '')
                    if minute >= 70 and state in ['2H', 'HT']:
                        qualifying_matches += 1
                
                print(f"\n🎯 Summary:")
                print(f"   Total live matches: {len(matches)}")
                print(f"   Matches past 70': {qualifying_matches}")
                print(f"   API Status: ✅ Working perfectly!")
                
                return True
                
            else:
                print("⚠️ No live matches at the moment")
                print("   This could mean:")
                print("   - No football matches are currently being played")
                print("   - Your API subscription might not include live data")
                print("   - Try again during peak football hours")
                return True  # API is working, just no matches
                
        elif response.status_code == 401:
            print("❌ API Authentication failed (401)")
            print("💡 Check your API key:")
            print(f"   Current key: {api_key[:10]}...")
            print("   Make sure it's active and has the right permissions")
            return False
            
        elif response.status_code == 403:
            print("❌ API Access forbidden (403)")
            print("💡 Subscription issue:")
            print("   Your plan might not include Live Scores API")
            print("   Check your Sportmonks subscription")
            return False
            
        elif response.status_code == 429:
            print("❌ Rate limit exceeded (429)")
            print("💡 Too many requests - try again in a few minutes")
            return False
            
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    result = test_all_live_matches()
    
    if result:
        print("\n🎉 Sportmonks API is working!")
        print("✅ Ready to proceed with full testing")
    else:
        print("\n❌ API test failed - check your setup")
        sys.exit(1) 