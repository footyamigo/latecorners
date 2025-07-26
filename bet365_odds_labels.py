import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

api_key = os.getenv('SPORTMONKS_API_KEY')

print("🎯 BET365 ODDS LABELS INVESTIGATION")
print("=" * 60)

# Get live matches
url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
params = {
    'api_token': api_key,
    'include': 'participants'
}

response = requests.get(url, params=params)
matches = response.json().get('data', [])

print(f"📊 Found {len(matches)} live matches")
print(f"🔍 Searching for bet365 (Bookmaker ID: 2) odds...")
print()

bet365_found = False

for match_idx, match in enumerate(matches[:10]):  # Check first 10 matches
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
        
        # Filter for bet365 only
        bet365_odds = [odds for odds in odds_data if odds.get('bookmaker_id') == 2]
        
        if bet365_odds:
            bet365_found = True
            print(f"✅ MATCH {match_idx + 1}: {home_team} vs {away_team}")
            print(f"   🏠 Home Team: {home_team} (ID: {home_id})")
            print(f"   🏃 Away Team: {away_team} (ID: {away_id})")
            print(f"   🎰 bet365 Odds Found: {len(bet365_odds)}")
            print()
            
            # Look for 1x2 / Match Winner odds from bet365
            bet365_1x2 = []
            
            for odds in bet365_odds:
                market_desc = odds.get('market_description', '').lower()
                
                if any(term in market_desc for term in ['1x2', 'match winner', 'full time result', 'match result']):
                    bet365_1x2.append(odds)
            
            if bet365_1x2:
                print(f"   🎯 bet365 1X2 ODDS ({len(bet365_1x2)} entries):")
                print("   " + "="*50)
                
                for i, odds in enumerate(bet365_1x2):
                    print(f"\n   #{i+1}:")
                    print(f"      Market Description: '{odds.get('market_description', 'N/A')}'")
                    print(f"      Label: '{odds.get('label', 'N/A')}'")
                    print(f"      Name: '{odds.get('name', 'N/A')}'")
                    print(f"      Value: {odds.get('value', 'N/A')}")
                    print(f"      Original Label: '{odds.get('original_label', 'N/A')}'")
                    print(f"      Bookmaker ID: {odds.get('bookmaker_id', 'N/A')}")
                    print(f"      Participants: {odds.get('participants', 'N/A')}")
                
                print(f"\n   📋 EXACT LABELS SUMMARY:")
                print("   " + "-"*30)
                
                labels_and_values = []
                for odds in bet365_1x2:
                    label = odds.get('label', 'N/A')
                    value = odds.get('value', 'N/A')
                    labels_and_values.append((label, value))
                
                # Sort by value to show pattern
                labels_and_values.sort(key=lambda x: float(x[1]) if x[1] != 'N/A' else 999)
                
                for label, value in labels_and_values:
                    print(f"      '{label}' = {value}")
                
                print(f"\n   🎯 MAPPING INTERPRETATION:")
                print("   " + "-"*30)
                
                home_odds = None
                away_odds = None
                draw_odds = None
                
                for odds in bet365_1x2:
                    label = odds.get('label', '').lower()
                    value = odds.get('value', 0)
                    
                    if label in ['1', 'home', '1x2 - home']:
                        home_odds = value
                        print(f"      🏠 {home_team}: {value} (label: '{odds.get('label')}')")
                    elif label in ['2', 'away', '1x2 - away']:
                        away_odds = value
                        print(f"      🏃 {away_team}: {value} (label: '{odds.get('label')}')")
                    elif label in ['x', 'draw', 'tie', '1x2 - draw']:
                        draw_odds = value
                        print(f"      🤝 Draw: {value} (label: '{odds.get('label')}')")
                
                if home_odds and away_odds:
                    if home_odds < away_odds:
                        favorite = home_team
                        favorite_odds = home_odds
                        underdog_odds = away_odds
                    else:
                        favorite = away_team
                        favorite_odds = away_odds
                        underdog_odds = home_odds
                    
                    odds_ratio = underdog_odds / favorite_odds
                    
                    print(f"\n   🏆 FAVORITE: {favorite} ({favorite_odds})")
                    print(f"   📊 Odds Ratio: {odds_ratio:.2f}x")
                
                print()
                break  # Stop after first match with bet365 1x2 odds
            else:
                print(f"   ❌ No 1X2 odds found for bet365")
                
                # Show what markets bet365 does have
                markets = set()
                for odds in bet365_odds:
                    markets.add(odds.get('market_description', 'Unknown'))
                
                print(f"   📋 bet365 markets available: {sorted(list(markets))[:5]}...")
        else:
            print(f"⏭️  MATCH {match_idx + 1}: {home_team} vs {away_team} - No bet365 odds")

if not bet365_found:
    print("❌ No bet365 odds found in first 10 matches")
    print("\n🔍 Let's check what bookmaker IDs are available:")
    
    # Show available bookmaker IDs
    if matches:
        match = matches[0]
        match_id = match['id']
        
        fixture_url = f"https://api.sportmonks.com/v3/football/fixtures/{match_id}"
        fixture_params = {
            'api_token': api_key,
            'include': 'odds'
        }
        
        fixture_response = requests.get(fixture_url, params=fixture_params)
        if fixture_response.status_code == 200:
            fixture_data = fixture_response.json()['data']
            odds_data = fixture_data.get('odds', [])
            
            bookmaker_ids = set()
            for odds in odds_data:
                bookmaker_ids.add(odds.get('bookmaker_id'))
            
            print(f"📊 Bookmaker IDs found: {sorted(list(bookmaker_ids))}") 