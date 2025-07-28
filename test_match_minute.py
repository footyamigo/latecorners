#!/usr/bin/env python3

"""
Test script to find the current match minute from Sportmonks API
Testing different includes and endpoints to get the live match time
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

def test_match_minute():
    try:
        import requests
        import os
        
        api_key = os.getenv('SPORTMONKS_API_KEY')
        if not api_key:
            print("❌ No SPORTMONKS_API_KEY found in .env file!")
            return False
        
        print("⏰ Testing different ways to get match minute...")
        
        # First, get a live match ID
        url = "https://api.sportmonks.com/v3/football/livescores/inplay"
        params = {
            'api_token': api_key,
            'include': 'scores;participants;state'
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            matches = data.get('data', [])
            
            if len(matches) > 0:
                test_fixture_id = matches[0]['id']
                match_name = matches[0].get('name', 'Unknown match')
                print(f"🏆 Testing with: {match_name} (ID: {test_fixture_id})")
                
                # Test 1: Try with 'periods' include
                print("\n📅 Test 1: Trying 'periods' include...")
                try:
                    test_url = f"https://api.sportmonks.com/v3/football/fixtures/{test_fixture_id}"
                    test_params = {
                        'api_token': api_key,
                        'include': 'periods'
                    }
                    
                    test_response = requests.get(test_url, params=test_params)
                    
                    if test_response.status_code == 200:
                        test_data = test_response.json()
                        fixture = test_data.get('data', {})
                        periods = fixture.get('periods', [])
                        
                        print(f"✅ Periods include works! Found {len(periods)} periods")
                        for i, period in enumerate(periods):
                            print(f"   Period {i+1}: {json.dumps(period, indent=4)}")
                    else:
                        print(f"❌ Periods failed: {test_response.status_code}")
                        print(f"Error: {test_response.text[:200]}...")
                except Exception as e:
                    print(f"❌ Periods test error: {e}")
                
                # Test 2: Try with 'timeline' include
                print("\n⏱️ Test 2: Trying 'timeline' include...")
                try:
                    test_params = {
                        'api_token': api_key,
                        'include': 'timeline'
                    }
                    
                    test_response = requests.get(test_url, params=test_params)
                    
                    if test_response.status_code == 200:
                        test_data = test_response.json()
                        fixture = test_data.get('data', {})
                        timeline = fixture.get('timeline', [])
                        
                        print(f"✅ Timeline include works! Found {len(timeline)} timeline entries")
                        for i, entry in enumerate(timeline[:3]):  # Show first 3
                            print(f"   Entry {i+1}: {json.dumps(entry, indent=4)}")
                    else:
                        print(f"❌ Timeline failed: {test_response.status_code}")
                        print(f"Error: {test_response.text[:200]}...")
                except Exception as e:
                    print(f"❌ Timeline test error: {e}")
                
                # Test 3: Check if fixture data has minute info directly
                print("\n🔍 Test 3: Checking fixture data directly...")
                try:
                    test_params = {
                        'api_token': api_key,
                        'include': 'scores;participants;state;events'
                    }
                    
                    test_response = requests.get(test_url, params=test_params)
                    
                    if test_response.status_code == 200:
                        test_data = test_response.json()
                        fixture = test_data.get('data', {})
                        
                        print("🔍 Fixture top-level fields:")
                        for key in fixture.keys():
                            if 'minute' in key.lower() or 'time' in key.lower():
                                print(f"   {key}: {fixture[key]}")
                        
                        # Check events for minute info
                        events = fixture.get('events', [])
                        print(f"\n📋 Events ({len(events)} total):")
                        for i, event in enumerate(events[:3]):  # Show first 3
                            minute = event.get('minute', 'No minute')
                            event_type = event.get('type', {}).get('name', 'Unknown')
                            print(f"   Event {i+1}: {event_type} at minute {minute}")
                        
                        # Check state for minute info
                        state = fixture.get('state', {})
                        print(f"\n⏰ State info:")
                        print(f"   {json.dumps(state, indent=4)}")
                        
                    else:
                        print(f"❌ Fixture data failed: {test_response.status_code}")
                except Exception as e:
                    print(f"❌ Fixture data test error: {e}")
                
                # Test 4: Try different state includes
                print("\n🛰️ Test 4: Testing available includes from livescores...")
                try:
                    available_includes = [
                        'timeline', 'periods', 'events', 'statistics', 
                        'state', 'scores', 'participants'
                    ]
                    
                    for include in available_includes:
                        test_params = {
                            'api_token': api_key,
                            'include': include
                        }
                        
                        test_response = requests.get(test_url, params=test_params)
                        
                        if test_response.status_code == 200:
                            test_data = test_response.json()
                            fixture = test_data.get('data', {})
                            
                            if include in fixture and fixture[include]:
                                print(f"   ✅ {include}: Available ({len(fixture[include])} items)")
                                
                                # Look for minute info in each include
                                include_data = fixture[include]
                                if isinstance(include_data, list) and len(include_data) > 0:
                                    first_item = include_data[0]
                                    if isinstance(first_item, dict):
                                        minute_fields = [k for k in first_item.keys() if 'minute' in k.lower()]
                                        if minute_fields:
                                            print(f"      → Found minute fields: {minute_fields}")
                            else:
                                print(f"   ❌ {include}: Not available or empty")
                        else:
                            print(f"   ❌ {include}: Failed ({test_response.status_code})")
                
                except Exception as e:
                    print(f"❌ Include test error: {e}")
                
                return True
            else:
                print("❌ No live matches found")
                return False
        else:
            print(f"❌ Failed to get live matches: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = test_match_minute()
    
    if result:
        print("\n✅ Match minute test complete!")
    else:
        print("\n❌ Match minute test failed")
        sys.exit(1) 