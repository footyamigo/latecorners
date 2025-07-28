#!/usr/bin/env python3

"""
Simple test with one include to verify syntax
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

def test_simple_include():
    try:
        import requests
        import os
        
        api_key = os.getenv('SPORTMONKS_API_KEY')
        if not api_key:
            print("❌ No SPORTMONKS_API_KEY found in .env file!")
            return False
        
        print("🧪 Testing simple include syntax...")
        print(f"🔑 API Key: {api_key[:10]}...")
        
        # Test with just scores include first
        url = "https://api.sportmonks.com/v3/football/livescores/inplay"
        params = {
            'api_token': api_key,
            'include': 'scores'  # Start with just one include
        }
        
        print("📡 Testing with 'scores' include only...")
        response = requests.get(url, params=params)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            matches = data.get('data', [])
            print(f"✅ 'scores' include works! Found {len(matches)} matches")
            
            if len(matches) > 0:
                first_match = matches[0]
                print(f"Available keys in match: {list(first_match.keys())}")
                
                if 'scores' in first_match:
                    print("✅ 'scores' data is present!")
                    scores = first_match.get('scores', [])
                    print(f"   Found {len(scores)} score entries")
                else:
                    print("❌ 'scores' data missing")
            
            # Now test with participants
            print("\n📡 Testing with 'participants' include...")
            params['include'] = 'participants'
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                matches = data.get('data', [])
                if len(matches) > 0:
                    first_match = matches[0]
                    if 'participants' in first_match:
                        print("✅ 'participants' include works!")
                        participants = first_match.get('participants', [])
                        print(f"   Found {len(participants)} participants")
                        if participants:
                            print(f"   First participant: {participants[0].get('name', 'Unknown')}")
                    else:
                        print("❌ 'participants' data missing")
            
            # Now test combined
            print("\n📡 Testing combined includes...")
            params['include'] = 'scores,participants'  # Try comma first
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                print("✅ Comma separator works!")
                return True
            else:
                print(f"❌ Comma failed: {response.status_code}")
                # Try semicolon
                params['include'] = 'scores;participants'
                response = requests.get(url, params=params)
                
                if response.status_code == 200:
                    print("✅ Semicolon separator works!")
                    return True
                else:
                    print(f"❌ Semicolon failed: {response.status_code}")
                    print(f"Response: {response.text[:200]}...")
                    return False
            
        else:
            print(f"❌ Basic API call failed: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    result = test_simple_include()
    
    if result:
        print("\n✅ Include syntax test successful!")
    else:
        print("\n❌ Include syntax test failed")
        sys.exit(1) 