import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

def verify_odds_team_mapping():
    """Carefully verify that odds labels correspond to actual home/away teams"""
    
    api_key = os.getenv('SPORTMONKS_API_KEY')
    
    print("🔍 VERIFYING ODDS-TO-TEAM MAPPING")
    print("=" * 80)
    
    # Get live matches
    url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
    params = {
        'api_token': api_key,
        'include': 'scores;participants;state;events;periods;league'
    }
    
    response = requests.get(url, params=params)
    matches = response.json().get('data', [])
    
    # Test first match with odds
    for i, match in enumerate(matches[:3]):
        match_id = match['id']
        
        # Get team names and their participant IDs
        participants = match.get('participants', [])
        home_team = "Unknown"
        away_team = "Unknown"
        home_participant_id = None
        away_participant_id = None
        
        for participant in participants:
            meta = participant.get('meta', {})
            location = meta.get('location', 'unknown')
            name = participant.get('name', 'Unknown')
            participant_id = participant.get('id')
            
            if location == 'home':
                home_team = name
                home_participant_id = participant_id
            elif location == 'away':
                away_team = name
                away_participant_id = participant_id
        
        print(f"\n🔍 {i+1}. {home_team} vs {away_team}")
        print(f"   Home ID: {home_participant_id} | Away ID: {away_participant_id}")
        
        # Get odds data
        fixture_url = f"https://api.sportmonks.com/v3/football/fixtures/{match_id}"
        fixture_params = {
            'api_token': api_key,
            'include': 'odds;participants;scores'
        }
        
        fixture_response = requests.get(fixture_url, params=fixture_params)
        if fixture_response.status_code == 200:
            fixture_data = fixture_response.json()['data']
            odds_data = fixture_data.get('odds', [])
            
            if odds_data:
                print(f"   📊 Found {len(odds_data)} odds entries")
                
                # Look for 1x2 odds and examine their structure
                match_winner_odds = []
                
                for idx, odds in enumerate(odds_data[:20]):  # Check first 20 odds
                    market_desc = odds.get('market_description', '').lower()
                    
                    if any(term in market_desc for term in ['1x2', 'match winner', 'full time result', 'match result']):
                        print(f"\n   📋 Odds Entry #{idx + 1}:")
                        print(f"      Market: {odds.get('market_description', 'Unknown')}")
                        print(f"      Label: {odds.get('label', 'Unknown')}")
                        print(f"      Value: {odds.get('value', 0)}")
                        print(f"      Name: {odds.get('name', 'Unknown')}")
                        print(f"      Participants: {odds.get('participants', 'None')}")
                        print(f"      Original Label: {odds.get('original_label', 'None')}")
                        
                        # Check if participants field contains team IDs
                        participants_field = odds.get('participants', '')
                        if participants_field:
                            print(f"      🎯 Participants field: {participants_field}")
                            
                            # Try to match participant IDs
                            if str(home_participant_id) in str(participants_field):
                                print(f"      ✅ MATCHES HOME TEAM: {home_team}")
                            elif str(away_participant_id) in str(participants_field):
                                print(f"      ✅ MATCHES AWAY TEAM: {away_team}")
                            else:
                                print(f"      ❓ No participant ID match found")
                        
                        match_winner_odds.append(odds)
                
                if match_winner_odds:
                    print(f"\n   🎯 ANALYSIS OF {len(match_winner_odds)} MATCH WINNER ODDS:")
                    
                    # Group by unique odds values to identify distinct outcomes
                    odds_groups = {}
                    for mw_odds in match_winner_odds:
                        value = float(mw_odds.get('value', 0))
                        label = mw_odds.get('label', 'Unknown')
                        participants = mw_odds.get('participants', '')
                        
                        key = f"{value:.2f}"
                        if key not in odds_groups:
                            odds_groups[key] = []
                        
                        odds_groups[key].append({
                            'label': label,
                            'participants': participants,
                            'original': mw_odds
                        })
                    
                    print(f"   📊 Unique odds values found: {len(odds_groups)}")
                    
                    for odds_value, entries in odds_groups.items():
                        print(f"\n   💰 Odds {odds_value}:")
                        for entry in entries:
                            print(f"      Label: {entry['label']} | Participants: {entry['participants']}")
                    
                    # Try to determine correct mapping
                    print(f"\n   🎯 ATTEMPTING CORRECT MAPPING:")
                    
                    home_odds = None
                    away_odds = None
                    draw_odds = None
                    
                    for mw_odds in match_winner_odds:
                        label = mw_odds.get('label', '').lower()
                        value = float(mw_odds.get('value', 0))
                        participants = str(mw_odds.get('participants', ''))
                        
                        # Method 1: Check participant IDs
                        if str(home_participant_id) in participants:
                            home_odds = value
                            print(f"      ✅ Home ({home_team}): {value:.2f} (via participant ID)")
                        elif str(away_participant_id) in participants:
                            away_odds = value
                            print(f"      ✅ Away ({away_team}): {value:.2f} (via participant ID)")
                        
                        # Method 2: Check standard labels as fallback
                        elif label in ['1', 'home'] and home_odds is None:
                            home_odds = value
                            print(f"      🟡 Home ({home_team}): {value:.2f} (via label '{label}' - verify!)")
                        elif label in ['2', 'away'] and away_odds is None:
                            away_odds = value
                            print(f"      🟡 Away ({away_team}): {value:.2f} (via label '{label}' - verify!)")
                        elif label in ['x', 'draw', 'tie']:
                            draw_odds = value
                            print(f"      ✅ Draw: {value:.2f} (via label '{label}')")
                    
                    if home_odds and away_odds:
                        print(f"\n   🎉 SUCCESSFULLY MAPPED ODDS:")
                        print(f"      {home_team}: {home_odds:.2f}")
                        print(f"      {away_team}: {away_odds:.2f}")
                        if draw_odds:
                            print(f"      Draw: {draw_odds:.2f}")
                        
                        # Determine favorite
                        if home_odds < away_odds:
                            print(f"      🎯 FAVORITE: {home_team} ({home_odds:.2f})")
                        else:
                            print(f"      🎯 FAVORITE: {away_team} ({away_odds:.2f})")
                    else:
                        print(f"   ❌ COULD NOT RELIABLY MAP HOME/AWAY ODDS")
                        print(f"      Found home_odds: {home_odds}")
                        print(f"      Found away_odds: {away_odds}")
                
                break  # Stop after first match with odds
            else:
                print(f"   ❌ No odds data found")

if __name__ == "__main__":
    verify_odds_team_mapping() 