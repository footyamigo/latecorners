import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

def get_bet365_corner_opportunities():
    """Get corner betting opportunities using only bet365 odds"""
    
    api_key = os.getenv('SPORTMONKS_API_KEY')
    
    print("🎯 BET365 CORNER BETTING OPPORTUNITIES")
    print("=" * 80)
    
    # Get live matches
    url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
    params = {
        'api_token': api_key,
        'include': 'scores;participants;state;events;periods;league'
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"❌ Failed to get live matches: {response.status_code}")
        return
    
    matches = response.json().get('data', [])
    print(f"📊 Found {len(matches)} live matches")
    print("🔍 Analyzing bet365 odds for corner opportunities...")
    print()
    
    opportunities = []
    
    for match in matches:
        try:
            result = analyze_match_for_corners(match, api_key)
            if result:
                opportunities.append(result)
        except Exception as e:
            print(f"⚠️ Error analyzing match {match.get('id', 'unknown')}: {e}")
    
    # Sort opportunities by psychology score
    opportunities.sort(key=lambda x: x['psychology_score'], reverse=True)
    
    print(f"\n📊 CORNER OPPORTUNITIES SUMMARY:")
    print("=" * 80)
    
    if opportunities:
        print(f"✅ Found {len(opportunities)} matches with bet365 odds")
        
        for i, opp in enumerate(opportunities[:5]):  # Show top 5
            print(f"\n🏆 #{i+1} OPPORTUNITY:")
            print(f"   ⚽ {opp['home_team']} vs {opp['away_team']}")
            print(f"   🏆 Score: {opp['scoreline']} | Minute: {opp['minute']}'")
            print(f"   🎯 Favorite: {opp['favorite']} ({opp['confidence']} favorite)")
            print(f"   🧠 Psychology Score: {opp['psychology_score']:.1f}")
            print(f"   ⚡ Urgency: {opp['urgency_level']}")
            print(f"   📊 Odds: {opp['home_team']} {opp['home_odds']} | {opp['away_team']} {opp['away_odds']}")
            
            if opp['urgency_level'] in ['EXTREME', 'VERY HIGH']:
                print(f"   🔥 RECOMMENDED: STRONG CORNER BET!")
            elif opp['urgency_level'] == 'HIGH':
                print(f"   🟡 CONSIDER: Good corner potential")
            else:
                print(f"   ⚠️ CAUTION: Lower priority")
    else:
        print("❌ No matches found with bet365 odds")

def analyze_match_for_corners(match, api_key):
    """Analyze a single match for corner betting opportunity"""
    
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
    
    # Get current score and minute
    scores = match.get('scores', [])
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
    
    # Get match minute
    state = match.get('state', {})
    minute = state.get('minute', 0)
    
    scoreline = f"{home_score}-{away_score}"
    
    # Get fixture with odds
    fixture_url = f"https://api.sportmonks.com/v3/football/fixtures/{match_id}"
    fixture_params = {
        'api_token': api_key,
        'include': 'odds'
    }
    
    fixture_response = requests.get(fixture_url, params=fixture_params)
    if fixture_response.status_code != 200:
        return None
    
    fixture_data = fixture_response.json()['data']
    odds_data = fixture_data.get('odds', [])
    
    # Filter for bet365 only (bookmaker_id = 2)
    bet365_odds = [odds for odds in odds_data if odds.get('bookmaker_id') == 2]
    
    if not bet365_odds:
        return None  # No bet365 odds available
    
    # Get bet365 1x2 odds
    home_odds = None
    away_odds = None
    draw_odds = None
    
    for odds in bet365_odds:
        market_desc = odds.get('market_description', '').lower()
        
        if 'full time result' in market_desc or '1x2' in market_desc or 'match winner' in market_desc:
            label = odds.get('label', '').lower()
            value = float(odds.get('value', 0))
            
            if label == 'home':
                home_odds = value
            elif label == 'away':
                away_odds = value
            elif label == 'draw':
                draw_odds = value
    
    if not home_odds or not away_odds:
        return None  # Missing essential odds
    
    # Determine favorite and confidence
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
    
    # Calculate psychology score
    psychology_score = calculate_psychology_score(
        home_score, away_score, favorite, confidence, minute
    )
    
    urgency_level = get_urgency_level(psychology_score)
    
    return {
        'match_id': match_id,
        'home_team': home_team,
        'away_team': away_team,
        'scoreline': scoreline,
        'minute': minute,
        'home_odds': home_odds,
        'away_odds': away_odds,
        'draw_odds': draw_odds,
        'favorite': favorite_team,
        'confidence': confidence,
        'odds_ratio': odds_ratio,
        'psychology_score': psychology_score,
        'urgency_level': urgency_level
    }

def calculate_psychology_score(home_score, away_score, favorite, confidence, minute):
    """Calculate psychology score based on scoreline and favorite status"""
    
    psychology_score = 0
    goal_diff = abs(home_score - away_score)
    
    # Late game multiplier (after 60 minutes)
    late_game_multiplier = 1.5 if minute >= 60 else 1.0
    
    if home_score == away_score:  # Draw scenarios
        if home_score == 0:
            psychology_score = 8  # 0-0 - moderate urgency
        else:
            psychology_score = 12  # 1-1, 2-2 etc - high urgency
    
    elif goal_diff == 1:  # One goal difference - KEY SCENARIOS
        # Determine who is leading
        if home_score > away_score:
            leading_team = 'home'
            trailing_team = 'away'
        else:
            leading_team = 'away'
            trailing_team = 'home'
        
        # Check if favorite is trailing - GOLDMINE SCENARIO
        if trailing_team == favorite:
            base_score = 15
            
            # Multiply by confidence level
            if confidence == 'HEAVY':
                psychology_score = base_score * 1.5  # 22.5
            elif confidence == 'STRONG':
                psychology_score = base_score * 1.3  # 19.5
            elif confidence == 'MODERATE':
                psychology_score = base_score * 1.1  # 16.5
            else:
                psychology_score = base_score  # 15
        else:
            # Underdog trailing
            psychology_score = 10
    
    elif goal_diff == 2:
        psychology_score = 5  # Two goal difference - moderate pressure
    else:
        psychology_score = 0  # Large difference - low urgency
    
    # Apply late game multiplier
    psychology_score *= late_game_multiplier
    
    return psychology_score

def get_urgency_level(psychology_score):
    """Convert psychology score to urgency level"""
    
    if psychology_score >= 20:
        return 'EXTREME'
    elif psychology_score >= 15:
        return 'VERY HIGH'
    elif psychology_score >= 10:
        return 'HIGH'
    elif psychology_score >= 5:
        return 'MEDIUM'
    else:
        return 'LOW'

if __name__ == "__main__":
    get_bet365_corner_opportunities() 