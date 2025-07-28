#!/usr/bin/env python3

"""
Debug script to examine the actual structure of scores data
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

def debug_scores_structure():
    try:
        import requests
        import os
        
        api_key = os.getenv('SPORTMONKS_API_KEY')
        if not api_key:
            print("❌ No SPORTMONKS_API_KEY found in .env file!")
            return False
        
        print("🔍 Debugging scores structure...")
        
        url = "https://api.sportmonks.com/v3/football/livescores/inplay"
        params = {
            'api_token': api_key,
            'include': 'scores;participants;state'
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            matches = data.get('data', [])
            
            print(f"✅ Found {len(matches)} matches")
            
            if len(matches) > 0:
                first_match = matches[0]
                
                print("\n🏆 FIRST MATCH STRUCTURE:")
                print("=" * 60)
                print(f"Match ID: {first_match.get('id')}")
                print(f"Match name: {first_match.get('name', 'Unknown')}")
                
                # Debug participants
                print(f"\n👥 PARTICIPANTS ({len(first_match.get('participants', []))}):")
                participants = first_match.get('participants', [])
                for i, participant in enumerate(participants):
                    print(f"   {i+1}. {json.dumps(participant, indent=6)}")
                
                # Debug scores - this is where the error is happening
                print(f"\n⚽ SCORES ({len(first_match.get('scores', []))}):")
                scores = first_match.get('scores', [])
                for i, score in enumerate(scores):
                    print(f"   {i+1}. {json.dumps(score, indent=6)}")
                    
                    # Try to access the 'score' field that's causing the error
                    if isinstance(score, dict) and 'score' in score:
                        score_field = score.get('score')
                        print(f"      → 'score' field type: {type(score_field)}")
                        print(f"      → 'score' field value: {score_field}")
                        
                        if isinstance(score_field, dict):
                            print(f"      → 'score' field keys: {list(score_field.keys())}")
                        
                # Debug state
                print(f"\n⏰ STATE:")
                state = first_match.get('state')
                print(f"   Type: {type(state)}")
                print(f"   Value: {json.dumps(state, indent=4)}")
                
                print(f"\n📋 ALL MATCH KEYS:")
                print(f"   {list(first_match.keys())}")
                
                return True
            else:
                print("❌ No matches found")
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
    result = debug_scores_structure()
    
    if result:
        print("\n✅ Debug complete!")
    else:
        print("\n❌ Debug failed")
        sys.exit(1) 