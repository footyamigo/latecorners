import os
import requests
from dotenv import load_dotenv
import json

try:
    load_dotenv()
    print("✅ Loaded .env file")

    api_key = os.getenv('SPORTMONKS_API_KEY')
    if not api_key:
        print("❌ No API key found")
        exit()

    # Get live matches first
    print("🔍 Getting live matches...")
    url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
    params = {
        'api_token': api_key,
        'include': 'scores;participants;state;events;periods'
    }

    response = requests.get(url, params=params)
    print(f"Live matches API status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ API Error: {response.text}")
        exit()
    
    data = response.json()
    matches = data.get('data', [])
    print(f"📊 Found {len(matches)} live matches")
    
    if not matches:
        print("❌ No live matches available for testing")
        exit()

    # Test fixture stats for first match  
    test_match_id = matches[0]['id']
    print(f"\n📈 Testing fixture stats for match {test_match_id}...")
    
    fixture_url = f"https://api.sportmonks.com/v3/football/fixtures/{test_match_id}"
    fixture_params = {
        'api_token': api_key,
        'include': 'statistics'  # Just statistics for now
    }
    
    fixture_response = requests.get(fixture_url, params=fixture_params)
    print(f"Fixture API status: {fixture_response.status_code}")
    
    if fixture_response.status_code != 200:
        print(f"❌ Fixture API Error: {fixture_response.text}")
        exit()
    
    fixture_data = fixture_response.json()
    
    if 'data' not in fixture_data:
        print("❌ No fixture data in response")
        print(f"Response keys: {list(fixture_data.keys())}")
        exit()
    
    fixture = fixture_data['data']
    statistics = fixture.get('statistics', [])
    
    print(f"📊 Found {len(statistics)} statistics")
    
    if statistics:
        print("\n🔍 First 5 statistics:")
        for i, stat in enumerate(statistics[:5]):
            stat_type = stat.get('type', {})
            print(f"   {i+1}. {stat_type.get('name', 'Unknown')} (ID: {stat_type.get('id', 'N/A')}) = {stat.get('value', 0)} [{stat.get('participant', 'unknown')}]")
    else:
        print("❌ No statistics found")
        print(f"Fixture keys: {list(fixture.keys())}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 