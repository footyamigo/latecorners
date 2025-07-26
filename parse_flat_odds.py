import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

def parse_flat_odds_structure():
    """Parse the flat odds structure to extract 1x2 match winner odds"""
    
    api_key = os.getenv('SPORTMONKS_API_KEY')
    
    print("🔍 PARSING FLAT ODDS STRUCTURE FOR 1X2 EXTRACTION")
    print("=" * 80)
    
    # Get live matches
    url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
    params = {
        'api_token': api_key,
        'include': 'scores;participants;state;events;periods;league'
    }
    
    response = requests.get(url, params=params)
    matches = response.json().get('data', [])
    
    for i, match in enumerate(matches[:5]):  # Test first 5 matches
        match_id = match['id']
        
        # Get team names
        participants = match.get('participants', [])
        home_team = "Unknown"
        away_team = "Unknown"
        
        for participant in participants:
            meta = participant.get('meta', {})
            location = meta.get('location', 'unknown')
            name = participant.get('name', 'Unknown')
            
            if location == 'home':
                home_team = name
            elif location == 'away':
                away_team = name
        
        print(f"\n🔍 {i+1}. {home_team} vs {away_team} (ID: {match_id})")
        
        # Get odds with basic include
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
                
                # Analyze market types available
                market_types = set()
                for odds in odds_data:
                    market_desc = odds.get('market_description', '').lower()
                    market_types.add(market_desc)
                
                print(f"   📋 Market types: {sorted(list(market_types))[:10]}...")  # Show first 10
                
                # Look for 1x2 / match winner odds
                match_winner_odds = []
                
                for odds in odds_data:
                    market_desc = odds.get('market_description', '').lower()
                    label = odds.get('label', '').lower()
                    value = odds.get('value', 0)
                    
                    # Check if this is a match winner market
                    if any(term in market_desc for term in ['1x2', 'match winner', 'full time result', 'match result']):
                        match_winner_odds.append({
                            'market': market_desc,
                            'label': label,
                            'value': value,
                            'odds': odds
                        })
                
                if match_winner_odds:
                    print(f"   🎯 Found {len(match_winner_odds)} match winner odds:")
                    
                    home_odds = None
                    away_odds = None
                    draw_odds = None
                    
                    for mw_odds in match_winner_odds:
                        label = mw_odds['label']
                        value = float(mw_odds['value'])
                        
                        print(f"      {label}: {value:.2f}")
                        
                        # Try to identify home/away/draw
                        if label in ['1', 'home', 'home win', home_team.lower()]:
                            home_odds = value
                        elif label in ['2', 'away', 'away win', away_team.lower()]:
                            away_odds = value
                        elif label in ['x', 'draw', 'tie']:
                            draw_odds = value
                    
                    if home_odds and away_odds:
                        print(f"   ✅ EXTRACTED ODDS:")
                        print(f"      Home ({home_team}): {home_odds:.2f}")
                        print(f"      Away ({away_team}): {away_odds:.2f}")
                        if draw_odds:
                            print(f"      Draw: {draw_odds:.2f}")
                        
                        # Determine favorite
                        if home_odds < away_odds:
                            favorite = 'home'
                            favorite_team = home_team
                            favorite_odds = home_odds
                            underdog_odds = away_odds
                        else:
                            favorite = 'away'
                            favorite_team = away_team
                            favorite_odds = away_odds
                            underdog_odds = home_odds
                        
                        odds_ratio = underdog_odds / favorite_odds
                        
                        if odds_ratio >= 3.0:
                            confidence = 'HEAVY'
                        elif odds_ratio >= 2.0:
                            confidence = 'STRONG'
                        elif odds_ratio >= 1.5:
                            confidence = 'MODERATE'
                        else:
                            confidence = 'SLIGHT'
                        
                        print(f"      🎯 FAVORITE: {favorite_team} ({confidence} favorite)")
                        print(f"      📊 Odds Ratio: {odds_ratio:.2f}x")
                        
                        # Test enhanced corner system with this data
                        print(f"      🎯 TESTING ENHANCED PSYCHOLOGY:")
                        test_enhanced_psychology_with_odds(fixture_data, home_odds, away_odds, favorite, confidence)
                        
                        break  # Found valid odds, stop here
                    else:
                        print(f"   ❌ Could not extract home/away odds from labels")
                else:
                    print(f"   ❌ No match winner odds found")
                    
                    # Show sample odds structure for debugging
                    if odds_data:
                        sample = odds_data[0]
                        print(f"   📋 Sample odds entry:")
                        for key, value in sample.items():
                            if key in ['market_description', 'label', 'value', 'name']:
                                print(f"      {key}: {value}")
            else:
                print(f"   ❌ No odds data found")

def test_enhanced_psychology_with_odds(fixture_data, home_odds, away_odds, favorite, confidence):
    """Test the enhanced psychology system with extracted odds"""
    
    # Extract current score
    scores = fixture_data.get('scores', [])
    home_score = 0
    away_score = 0
    
    for score_entry in scores:
        if score_entry.get('description') == 'CURRENT':
            score_data = score_entry.get('score', {})
            goals = score_data.get('goals', 0)
            participant = score_data.get('participant', '')
            
            if participant == 'home':
                home_score = goals
            elif participant == 'away':
                away_score = goals
    
    scoreline = f"{home_score}-{away_score}"
    
    # Calculate psychology score
    psychology_score = 0
    urgency_level = "LOW"
    
    goal_diff = abs(home_score - away_score)
    
    if home_score == away_score:  # Draw
        if home_score == 0:
            psychology_score = 8
            urgency_level = "HIGH"
        else:
            psychology_score = 12
            urgency_level = "VERY HIGH"
    
    elif goal_diff == 1:  # One goal difference
        # Determine who is leading
        if home_score > away_score:
            leading_team = 'home'
            trailing_team = 'away'
        else:
            leading_team = 'away'
            trailing_team = 'home'
        
        # Check if favorite is trailing
        if trailing_team == favorite:
            # FAVORITE TRAILING - GOLDMINE!
            base_score = 15
            
            if confidence == 'HEAVY':
                psychology_score = base_score * 1.5  # 22.5
                urgency_level = "EXTREME"
            elif confidence == 'STRONG':
                psychology_score = base_score * 1.3  # 19.5
                urgency_level = "VERY HIGH"
            elif confidence == 'MODERATE':
                psychology_score = base_score * 1.1  # 16.5
                urgency_level = "HIGH"
            else:
                psychology_score = base_score  # 15
                urgency_level = "HIGH"
        else:
            # Underdog trailing
            psychology_score = 10
            urgency_level = "MEDIUM"
    
    elif goal_diff == 2:
        psychology_score = 5
        urgency_level = "MEDIUM"
    else:
        psychology_score = 0
        urgency_level = "LOW"
    
    print(f"         Scoreline: {scoreline}")
    print(f"         Psychology Score: {psychology_score:.1f}")
    print(f"         Urgency Level: {urgency_level}")
    
    if urgency_level == "EXTREME":
        print(f"         🔥 EXTREME URGENCY - CORNER GOLDMINE!")
    elif urgency_level == "VERY HIGH":
        print(f"         ⚡ VERY HIGH URGENCY - EXCELLENT CORNER POTENTIAL!")
    elif urgency_level == "HIGH":
        print(f"         🟡 HIGH URGENCY - GOOD CORNER POTENTIAL")
    else:
        print(f"         ⚠️ MEDIUM/LOW URGENCY - PROCEED WITH CAUTION")

if __name__ == "__main__":
    parse_flat_odds_structure() 