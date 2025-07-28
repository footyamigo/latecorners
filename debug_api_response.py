#!/usr/bin/env python3

"""
Debug script to examine the raw Sportmonks API response
This helps us understand the actual data structure and fix our parsing
"""

import sys
import json
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

def debug_api_response():
    try:
        import requests
        import os
        
        api_key = os.getenv('SPORTMONKS_API_KEY')
        if not api_key:
            print("❌ No SPORTMONKS_API_KEY found in .env file!")
            return False
        
        print("🔍 Examining raw Sportmonks API response...")
        print(f"🔑 API Key: {api_key[:10]}...")
        
        # Make API call
        url = "https://api.sportmonks.com/v3/football/livescores/inplay"
        params = {'api_token': api_key}
        
        print("📡 Calling API...")
        response = requests.get(url, params=params)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Got response with {len(data.get('data', []))} matches")
            
            # Show the structure of the first match
            matches = data.get('data', [])
            if len(matches) > 0:
                print("\n🔍 RAW STRUCTURE of first match:")
                print("=" * 60)
                
                first_match = matches[0]
                print(json.dumps(first_match, indent=2))
                
                print("\n" + "=" * 60)
                print("🗂️ AVAILABLE KEYS in match object:")
                print(list(first_match.keys()))
                
                # Check if participants exist and show structure
                if 'participants' in first_match:
                    print(f"\n👥 PARTICIPANTS structure:")
                    participants = first_match.get('participants', [])
                    if participants:
                        print(f"   Number of participants: {len(participants)}")
                        print("   First participant keys:", list(participants[0].keys()) if participants else "None")
                        print("   First participant:", json.dumps(participants[0], indent=4) if participants else "None")
                
                # Check state structure
                if 'state' in first_match:
                    print(f"\n⏰ STATE structure:")
                    state = first_match.get('state', {})
                    print("   State keys:", list(state.keys()) if isinstance(state, dict) else f"State type: {type(state)}")
                    print("   State data:", json.dumps(state, indent=4))
                
                # Check scores structure
                if 'scores' in first_match:
                    print(f"\n⚽ SCORES structure:")
                    scores = first_match.get('scores', [])
                    print(f"   Number of score entries: {len(scores)}")
                    if scores:
                        print("   First score keys:", list(scores[0].keys()) if scores else "None")
                        print("   First score:", json.dumps(scores[0], indent=4) if scores else "None")
                
                # Show a few more matches for comparison
                print(f"\n📋 QUICK VIEW of all {len(matches)} matches:")
                print("-" * 60)
                for i, match in enumerate(matches[:10]):  # Show first 10
                    match_id = match.get('id', 'No ID')
                    minute = match.get('minute', 'No minute')
                    state = match.get('state', {})
                    state_name = state.get('short_name', 'No state') if isinstance(state, dict) else str(state)
                    
                    print(f"{i+1:2d}. ID: {match_id} | Minute: {minute} | State: {state_name}")
                
                return True
            else:
                print("❌ No matches in response")
                print("Raw response:", json.dumps(data, indent=2)[:500] + "...")
                return False
                
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Debug error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting API response debug...")
    result = debug_api_response()
    
    if result:
        print("\n✅ Debug complete - check the structure above!")
    else:
        print("\n❌ Debug failed")
        sys.exit(1) 