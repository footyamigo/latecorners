import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_live_corner_opportunities():
    """Get corner betting opportunities from truly live matches only"""
    
    api_key = os.getenv('SPORTMONKS_API_KEY')
    
    print("🎯 LIVE CORNER BETTING OPPORTUNITIES (bet365 only)")
    print("=" * 80)
    
    # Get live matches
    url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
    params = {
        'api_token': api_key,
        'include': 'scores;participants;state;periods;league'
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"❌ Failed to get live matches: {response.status_code}")
        return
    
    matches = response.json().get('data', [])
    print(f"📊 Found {len(matches)} inplay matches")
    
    # Filter for truly live matches
    live_matches = filter_truly_live_matches(matches)
    print(f"⚽ Truly live and playing: {len(live_matches)}")
    print()
    
    opportunities = []
    
    for match in live_matches:
        try:
            result = analyze_live_match_for_corners(match, api_key)
            if result:
                opportunities.append(result)
        except Exception as e:
            print(f"⚠️ Error analyzing match {match.get('match_id', 'unknown')}: {e}")
    
    # Sort opportunities by psychology score
    opportunities.sort(key=lambda x: x['psychology_score'], reverse=True)
    
    print(f"📊 LIVE CORNER OPPORTUNITIES:")
    print("=" * 80)
    
    if opportunities:
        print(f"✅ Found {len(opportunities)} live matches with bet365 odds")
        
        for i, opp in enumerate(opportunities):
            print(f"\n🏆 #{i+1} LIVE OPPORTUNITY:")
            print(f"   ⚽ {opp['home_team']} vs {opp['away_team']}")
            print(f"   🏆 Score: {opp['scoreline']} | Minute: {opp['minute']}' | State: {opp['state']}")
            print(f"   🏟️ League: {opp['league']}")
            print(f"   🎯 Favorite: {opp['favorite']} ({opp['confidence']} favorite)")
            print(f"   🧠 Psychology Score: {opp['psychology_score']:.1f}")
            print(f"   ⚡ Urgency: {opp['urgency_level']}")
            print(f"   📊 bet365 Odds: {opp['home_team']} {opp['home_odds']:.2f} | {opp['away_team']} {opp['away_odds']:.2f}")
            
            if opp['urgency_level'] in ['EXTREME', 'VERY HIGH']:
                print(f"   🔥 RECOMMENDED: STRONG CORNER BET!")
                print(f"   💡 Reasoning: {get_psychology_reasoning(opp)}")
            elif opp['urgency_level'] == 'HIGH':
                print(f"   🟡 CONSIDER: Good corner potential")
            else:
                print(f"   ⚠️ CAUTION: Lower priority")
    else:
        print("❌ No live matches found with bet365 odds")
        print("💡 Try again in a few minutes - matches may not have bet365 odds yet")

def filter_truly_live_matches(matches):
    """Filter matches to only include those truly live and playing"""
    
    live_matches = []
    
    for match in matches:
        state = match.get('state', {})
        state_short = state.get('short_name', 'unknown')
        
        # Get actual minute from periods
        periods = match.get('periods', [])
        actual_minute = extract_match_minute(periods, state_short)
        
        # Include only matches that are actively playing
        is_live = False
        
        if state_short in ['1H', '1st'] and actual_minute > 0:
            is_live = True
        elif state_short in ['2H', '2nd'] and actual_minute > 45:
            is_live = True
        elif actual_minute > 0 and state_short not in ['NS', 'FT', 'HT']:
            is_live = True
        
        if is_live:
            # Add extracted minute to match data
            match['_live_minute'] = actual_minute
            match['_live_state'] = state_short
            live_matches.append(match)
    
    return live_matches

def extract_match_minute(periods, state_short):
    """Extract actual match minute from periods data"""
    
    if not periods:
        return 0
    
    # Find the current period
    current_period = None
    for period in periods:
        if period.get('is_current', False):
            current_period = period
            break
    
    if not current_period:
        # If no current period, try to find the latest one
        current_period = periods[-1] if periods else None
    
    if not current_period:
        return 0
    
    # Extract minute from current period
    minute = current_period.get('minute', 0)
    
    # For 2nd half, add 45 minutes
    if state_short in ['2H', '2nd']:
        minute += 45
    
    return minute

def analyze_live_match_for_corners(match, api_key):
    """Analyze a live match for corner betting opportunity"""
    
    match_id = match['id']
    live_minute = match.get('_live_minute', 0)
    live_state = match.get('_live_state', 'unknown')
    
    # Get team info
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
    
    # Get league info
    league_info = match.get('league', {})
    league_name = league_info.get('name', 'Unknown League')
    
    # Get current score
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
    
    # Calculate psychology score with live minute
    psychology_score = calculate_psychology_score(
        home_score, away_score, favorite, confidence, live_minute
    )
    
    urgency_level = get_urgency_level(psychology_score)
    
    return {
        'match_id': match_id,
        'home_team': home_team,
        'away_team': away_team,
        'league': league_name,
        'scoreline': scoreline,
        'minute': live_minute,
        'state': live_state,
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
    """Calculate psychology score based on scoreline, favorite status, and match time"""
    
    psychology_score = 0
    goal_diff = abs(home_score - away_score)
    
    # Late game multiplier increases urgency
    if minute >= 75:
        late_game_multiplier = 2.0  # Very late game - desperation time!
    elif minute >= 60:
        late_game_multiplier = 1.5  # Late game
    else:
        late_game_multiplier = 1.0  # Regular time
    
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
    
    if psychology_score >= 30:
        return 'EXTREME'
    elif psychology_score >= 20:
        return 'VERY HIGH'
    elif psychology_score >= 15:
        return 'HIGH'
    elif psychology_score >= 8:
        return 'MEDIUM'
    else:
        return 'LOW'

def get_psychology_reasoning(opp):
    """Get reasoning for psychology score"""
    
    reasoning_parts = []
    
    if opp['minute'] >= 75:
        reasoning_parts.append("Late game desperation (75+ min)")
    
    goal_diff = abs(int(opp['scoreline'].split('-')[0]) - int(opp['scoreline'].split('-')[1]))
    
    if goal_diff == 1:
        if 'trailing' in opp.get('scenario', ''):
            reasoning_parts.append(f"{opp['confidence']} favorite trailing by 1 goal")
    elif goal_diff == 0:
        reasoning_parts.append("Draw - both teams pushing for winner")
    
    return " + ".join(reasoning_parts) if reasoning_parts else "Standard corner opportunity"

if __name__ == "__main__":
    get_live_corner_opportunities() 