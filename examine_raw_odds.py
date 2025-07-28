import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

api_key = os.getenv('SPORTMONKS_API_KEY')

print("🔍 EXAMINING RAW ODDS STRUCTURE")
print("=" * 60)

# Get first live match with odds
url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
params = {
    'api_token': api_key,
    'include': 'participants'
}

response = requests.get(url, params=params)
matches = response.json().get('data', [])

if matches:
    match = matches[0]  # First match
    match_id = match['id']
    
    # Get team info
    participants = match.get('participants', [])
    home_team = "Unknown"
    away_team = "Unknown"
    home_id = None
    away_id = None
    
    for participant in participants:
        meta = participant.get('meta', {})
        location = meta.get('location', 'unknown')
        name = participant.get('name', 'Unknown')
        p_id = participant.get('id')
        
        if location == 'home':
            home_team = name
            home_id = p_id
        elif location == 'away':
            away_team = name
            away_id = p_id
    
    print(f"⚽ MATCH: {home_team} vs {away_team}")
    print(f"🏠 Home ID: {home_id} | 🏃 Away ID: {away_id}")
    print()
    
    # Get odds
    fixture_url = f"https://api.sportmonks.com/v3/football/fixtures/{match_id}"
    fixture_params = {
        'api_token': api_key,
        'include': 'odds'
    }
    
    fixture_response = requests.get(fixture_url, params=fixture_params)
    if fixture_response.status_code == 200:
        fixture_data = fixture_response.json()['data']
        odds_data = fixture_data.get('odds', [])
        
        print(f"📊 Found {len(odds_data)} odds entries")
        
        if odds_data:
            # Look for 1x2 odds and show their exact structure
            match_winner_count = 0
            
            print(f"\n🎯 EXAMINING 1X2 ODDS STRUCTURE:")
            print("-" * 50)
            
            for i, odds in enumerate(odds_data):
                market_desc = odds.get('market_description', '').lower()
                
                if any(term in market_desc for term in ['1x2', 'match winner', 'full time result']):
                    match_winner_count += 1
                    
                    if match_winner_count <= 5:  # Show first 5 match winner odds
                        print(f"\n#{match_winner_count}:")
                        print(f"  Market: {odds.get('market_description', 'N/A')}")
                        print(f"  Label: '{odds.get('label', 'N/A')}'")
                        print(f"  Value: {odds.get('value', 'N/A')}")
                        print(f"  Name: {odds.get('name', 'N/A')}")
                        print(f"  Participants: {odds.get('participants', 'N/A')}")
                        print(f"  Bookmaker ID: {odds.get('bookmaker_id', 'N/A')}")
                        
                        # Check if participants contains our team IDs
                        participants_field = str(odds.get('participants', ''))
                        if str(home_id) in participants_field:
                            print(f"  ✅ CONTAINS HOME TEAM ID ({home_id})")
                        if str(away_id) in participants_field:
                            print(f"  ✅ CONTAINS AWAY TEAM ID ({away_id})")
            
            print(f"\n📊 Total 1X2 odds found: {match_winner_count}")
            
            # Try to group by unique values to see pattern
            print(f"\n🔍 ANALYZING ODDS PATTERNS:")
            print("-" * 50)
            
            values_found = {}
            labels_found = set()
            
            for odds in odds_data:
                market_desc = odds.get('market_description', '').lower()
                
                if any(term in market_desc for term in ['1x2', 'match winner', 'full time result']):
                    value = odds.get('value', 0)
                    label = odds.get('label', 'unknown')
                    
                    labels_found.add(label)
                    
                    if value not in values_found:
                        values_found[value] = []
                    values_found[value].append(label)
            
            print(f"Unique labels: {sorted(labels_found)}")
            print(f"Unique values with their labels:")
            
            for value in sorted(values_found.keys()):
                labels = list(set(values_found[value]))  # Remove duplicates
                print(f"  {value}: {labels}")
            
            # Show our best guess for home/away mapping
            print(f"\n🎯 BEST GUESS MAPPING:")
            print("-" * 50)
            
            # Look for most common pattern
            for odds in odds_data:
                market_desc = odds.get('market_description', '').lower()
                
                if '1x2' in market_desc or 'match winner' in market_desc:
                    label = odds.get('label', '').lower()
                    value = odds.get('value', 0)
                    
                    if label == '1' or label == 'home':
                        print(f"  Home ({home_team}): {value} (via label '{label}')")
                        break
            
            for odds in odds_data:
                market_desc = odds.get('market_description', '').lower()
                
                if '1x2' in market_desc or 'match winner' in market_desc:
                    label = odds.get('label', '').lower()
                    value = odds.get('value', 0)
                    
                    if label == '2' or label == 'away':
                        print(f"  Away ({away_team}): {value} (via label '{label}')")
                        break
        else:
            print("❌ No odds data found")
    else:
        print(f"❌ API error: {fixture_response.status_code}")
else:
    print("❌ No live matches found") 