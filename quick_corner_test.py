import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('SPORTMONKS_API_KEY')

print("🎯 QUICK ASIAN CORNER TEST")
print("=" * 50)

# Get live matches and find North Lakes vs Sunshine Coast
url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
params = {'api_token': api_key, 'include': 'participants'}

response = requests.get(url, params=params)
matches = response.json().get('data', [])

print(f"📊 Found {len(matches)} matches")

# Look for the specific match
target_match_id = None
for match in matches:
    participants = match.get('participants', [])
    teams = []
    for p in participants:
        teams.append(p.get('name', ''))
    
    match_str = ' vs '.join(teams)
    
    if 'North Lakes' in match_str and 'Sunshine Coast' in match_str:
        target_match_id = match['id']
        print(f"✅ FOUND: {match_str}")
        print(f"   Match ID: {target_match_id}")
        break

if target_match_id:
    print(f"\n🎯 Testing Asian corner markets for match {target_match_id}:")
    
    # Test Market 61: Asian Total Corners
    print("\n📊 Market 61 (Asian Total Corners):")
    url_61 = f"https://api.sportmonks.com/v3/football/odds/inplay/fixtures/{target_match_id}/markets/61"
    try:
        resp = requests.get(url_61, params={'api_token': api_key})
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json().get('data', [])
            bet365 = [x for x in data if x.get('bookmaker_id') == 2]
            print(f"   Total odds: {len(data)}, bet365: {len(bet365)}")
            if bet365:
                for odd in bet365[:3]:  # Show first 3
                    print(f"      {odd.get('label')}: {odd.get('value')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test Market 62: Asian Handicap Corners  
    print("\n📊 Market 62 (Asian Handicap Corners):")
    url_62 = f"https://api.sportmonks.com/v3/football/odds/inplay/fixtures/{target_match_id}/markets/62"
    try:
        resp = requests.get(url_62, params={'api_token': api_key})
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json().get('data', [])
            bet365 = [x for x in data if x.get('bookmaker_id') == 2]
            print(f"   Total odds: {len(data)}, bet365: {len(bet365)}")
            if bet365:
                for odd in bet365[:3]:  # Show first 3
                    print(f"      {odd.get('label')}: {odd.get('value')}")
    except Exception as e:
        print(f"   Error: {e}")

else:
    print("❌ Match not found. Available matches:")
    for i, match in enumerate(matches[:5]):
        participants = match.get('participants', [])
        teams = []
        for p in participants:
            teams.append(p.get('name', ''))
        print(f"   {i+1}. {' vs '.join(teams)}") 