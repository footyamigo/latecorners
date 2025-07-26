import os
import requests
from dotenv import load_dotenv

load_dotenv()

class OddsAwareCornerSystem:
    def __init__(self):
        self.api_key = os.getenv('SPORTMONKS_API_KEY')
        
        # Core stats mapping
        self.core_stats = {
            34: "Corners",
            44: "Dangerous Attacks", 
            42: "Shots Total",
            49: "Shots Inside Box",
            60: "Crosses",
            51: "Offsides"
        }

    def get_prematch_odds(self, fixture_id):
        """Get pre-match odds to determine favorite vs underdog"""
        
        # Try to get pre-match odds for this fixture
        odds_url = f"https://api.sportmonks.com/v3/football/fixtures/{fixture_id}"
        odds_params = {
            'api_token': self.api_key,
            'include': 'odds.bookmaker;odds.markets'
        }
        
        try:
            response = requests.get(odds_url, params=odds_params)
            if response.status_code == 200:
                fixture_data = response.json()
                
                if 'data' in fixture_data:
                    fixture = fixture_data['data']
                    odds_data = fixture.get('odds', [])
                    
                    # Look for 1x2 (match winner) market
                    for odds_entry in odds_data:
                        markets = odds_entry.get('markets', [])
                        
                        for market in markets:
                            # Check if this is the match winner market
                            if market.get('name', '').lower() in ['1x2', 'match winner', 'full time result']:
                                selections = market.get('selections', [])
                                
                                home_odds = None
                                away_odds = None
                                
                                for selection in selections:
                                    label = selection.get('label', '').lower()
                                    odds = selection.get('odds', 0)
                                    
                                    if label in ['1', 'home', 'home win']:
                                        home_odds = float(odds)
                                    elif label in ['2', 'away', 'away win']:
                                        away_odds = float(odds)
                                
                                if home_odds and away_odds:
                                    return self.analyze_odds(home_odds, away_odds)
        
        except Exception as e:
            print(f"   ⚠️ Could not get odds data: {e}")
        
        return {
            'favorite': 'unknown',
            'underdog': 'unknown', 
            'home_odds': 0,
            'away_odds': 0,
            'odds_available': False,
            'favorite_confidence': 'unknown'
        }

    def analyze_odds(self, home_odds, away_odds):
        """Analyze odds to determine favorite and confidence level"""
        
        # Determine favorite based on lower odds
        if home_odds < away_odds:
            favorite = 'home'
            underdog = 'away'
            favorite_odds = home_odds
            underdog_odds = away_odds
        else:
            favorite = 'away'
            underdog = 'home' 
            favorite_odds = away_odds
            underdog_odds = home_odds
        
        # Calculate odds difference for confidence
        odds_ratio = underdog_odds / favorite_odds
        
        if odds_ratio >= 3.0:
            confidence = 'HEAVY'  # Heavy favorite
        elif odds_ratio >= 2.0:
            confidence = 'STRONG'  # Strong favorite
        elif odds_ratio >= 1.5:
            confidence = 'MODERATE'  # Moderate favorite
        else:
            confidence = 'SLIGHT'  # Pick'em game
        
        return {
            'favorite': favorite,
            'underdog': underdog,
            'home_odds': home_odds,
            'away_odds': away_odds,
            'odds_available': True,
            'favorite_confidence': confidence,
            'odds_ratio': odds_ratio
        }

    def enhanced_scoreline_psychology(self, score_data, odds_data, minute):
        """Enhanced psychology considering favorite/underdog status"""
        
        home_score = score_data['home_score']
        away_score = score_data['away_score']
        scoreline = score_data['scoreline']
        
        psychology_score = 0
        urgency_level = "LOW"
        explanation = ""
        
        # Base scoreline analysis
        goal_diff = abs(home_score - away_score)
        
        if home_score == away_score:  # DRAW
            if home_score == 0:  # 0-0
                psychology_score += 8
                urgency_level = "HIGH"
                explanation = "0-0 draw - both teams need breakthrough"
            else:  # 1-1, 2-2, etc.
                psychology_score += 12
                urgency_level = "VERY HIGH"
                explanation = f"{scoreline} draw - both teams desperate for winner"
        
        elif goal_diff == 1 and odds_data['odds_available']:  # ONE GOAL DIFFERENCE + ODDS AVAILABLE
            
            # Determine who is leading
            if home_score > away_score:  # Home leading
                leading_team = 'home'
                trailing_team = 'away'
            else:  # Away leading
                leading_team = 'away'
                trailing_team = 'home'
            
            # CRITICAL ANALYSIS: Favorite vs Underdog status
            if trailing_team == odds_data['favorite']:
                # FAVORITE TRAILING - CORNER GOLDMINE! ⭐⭐⭐
                base_score = 15  # High base score
                
                if odds_data['favorite_confidence'] == 'HEAVY':
                    psychology_score += base_score * 1.5  # 22.5 points
                    urgency_level = "EXTREME"
                    explanation = f"HEAVY FAVORITE trailing {scoreline} - desperate high-quality attack expected!"
                elif odds_data['favorite_confidence'] == 'STRONG':
                    psychology_score += base_score * 1.3  # 19.5 points
                    urgency_level = "VERY HIGH"
                    explanation = f"STRONG FAVORITE trailing {scoreline} - quality attacking pressure"
                elif odds_data['favorite_confidence'] == 'MODERATE':
                    psychology_score += base_score * 1.1  # 16.5 points
                    urgency_level = "HIGH"
                    explanation = f"MODERATE FAVORITE trailing {scoreline} - good attacking potential"
                else:  # SLIGHT
                    psychology_score += base_score  # 15 points
                    urgency_level = "HIGH"
                    explanation = f"SLIGHT FAVORITE trailing {scoreline} - even match pressure"
            
            elif leading_team == odds_data['underdog']:
                # UNDERDOG LEADING - Favorite will attack but consider underdog's defensive capability
                base_score = 12  # Good base score
                
                if odds_data['favorite_confidence'] == 'HEAVY':
                    psychology_score += base_score * 1.4  # 16.8 points
                    urgency_level = "VERY HIGH"
                    explanation = f"UNDERDOG leading {scoreline} vs HEAVY FAVORITE - quality counter-attack expected"
                elif odds_data['favorite_confidence'] == 'STRONG':
                    psychology_score += base_score * 1.2  # 14.4 points
                    urgency_level = "HIGH"
                    explanation = f"UNDERDOG leading {scoreline} vs STRONG FAVORITE - sustained pressure expected"
                else:
                    psychology_score += base_score  # 12 points
                    urgency_level = "HIGH"
                    explanation = f"UNDERDOG leading {scoreline} - favorite will push"
            
            else:
                # Leading team is favorite - less urgent
                psychology_score += 8
                urgency_level = "MEDIUM"
                explanation = f"FAVORITE leading {scoreline} - underdog may push but limited quality"
        
        elif goal_diff == 1:  # ONE GOAL DIFFERENCE but no odds data
            psychology_score += 10
            urgency_level = "HIGH"
            explanation = f"One goal game {scoreline} - high pressure (odds unavailable)"
        
        elif goal_diff == 2:  # TWO GOAL DIFFERENCE
            psychology_score += 5
            urgency_level = "MEDIUM"
            explanation = f"{scoreline} - losing team may push but not desperately"
        
        else:  # 3+ GOAL DIFFERENCE
            psychology_score += 0
            urgency_level = "LOW"
            explanation = f"{scoreline} - game likely decided"
        
        # LATE GAME MULTIPLIERS (70+ minutes)
        if minute >= 70:
            if urgency_level == "EXTREME":
                psychology_score *= 1.8  # Extreme urgency gets massive boost
            elif urgency_level == "VERY HIGH":
                psychology_score *= 1.5
            elif urgency_level == "HIGH":
                psychology_score *= 1.3
            
            explanation += f" + late game desperation (min {minute})"
        
        return {
            'psychology_score': psychology_score,
            'urgency_level': urgency_level,
            'explanation': explanation,
            'scoreline': scoreline
        }

    def test_odds_system(self, fixture_id):
        """Test the odds-aware corner system"""
        
        print(f"🎯 ODDS-AWARE CORNER SYSTEM TEST")
        print(f"📊 Fixture ID: {fixture_id}")
        print("=" * 80)
        
        # Get fixture data
        fixture_url = f"https://api.sportmonks.com/v3/football/fixtures/{fixture_id}"
        fixture_params = {
            'api_token': self.api_key,
            'include': 'statistics;participants;state;periods;scores'
        }
        
        response = requests.get(fixture_url, params=fixture_params)
        if response.status_code == 200:
            fixture_data = response.json()['data']
            
            # Get team names and score
            participants = fixture_data.get('participants', [])
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
            
            # Extract score
            scores = fixture_data.get('scores', [])
            home_score = 0
            away_score = 0
            
            for score_entry in scores:
                if score_entry.get('description') == 'CURRENT':
                    score_data_entry = score_entry.get('score', {})
                    goals = score_data_entry.get('goals', 0)
                    participant = score_data_entry.get('participant', '')
                    
                    if participant == 'home':
                        home_score = goals
                    elif participant == 'away':
                        away_score = goals
            
            score_data = {
                'home_team': home_team,
                'away_team': away_team,
                'home_score': home_score,
                'away_score': away_score,
                'scoreline': f"{home_score}-{away_score}"
            }
            
            # Get match timing
            periods = fixture_data.get('periods', [])
            minute = 0
            for period in periods:
                if period.get('ticking', False):
                    minute = period.get('minutes', 0)
                    if '2nd' in period.get('description', '').lower():
                        minute += 45
                    break
            
            # Get odds data
            odds_data = self.get_prematch_odds(fixture_id)
            
            # Analyze psychology with odds
            psychology = self.enhanced_scoreline_psychology(score_data, odds_data, minute)
            
            # Display results
            print(f"⚽ MATCH: {home_team} vs {away_team}")
            print(f"🏆 SCORE: {score_data['scoreline']} | Minute: {minute}'")
            print()
            
            if odds_data['odds_available']:
                print(f"💰 PRE-MATCH ODDS:")
                print(f"   Home: {odds_data['home_odds']:.2f} | Away: {odds_data['away_odds']:.2f}")
                print(f"   Favorite: {odds_data['favorite'].upper()} ({odds_data['favorite_confidence']} favorite)")
                print(f"   Odds Ratio: {odds_data['odds_ratio']:.2f}x")
            else:
                print(f"💰 PRE-MATCH ODDS: Not available")
            print()
            
            print(f"🧠 ENHANCED SCORELINE PSYCHOLOGY:")
            print(f"   {psychology['explanation']}")
            print(f"   Urgency Level: {psychology['urgency_level']}")
            print(f"   Psychology Score: {psychology['psychology_score']:.1f}")
            print()
            
            # Show recommendation impact
            if psychology['urgency_level'] == "EXTREME":
                print(f"   🔥 EXTREME URGENCY = CORNER GOLDMINE OPPORTUNITY!")
            elif psychology['urgency_level'] == "VERY HIGH":
                print(f"   ⚡ VERY HIGH URGENCY = EXCELLENT CORNER POTENTIAL!")
            elif psychology['urgency_level'] == "HIGH":
                print(f"   🟡 HIGH URGENCY = GOOD CORNER POTENTIAL")
            else:
                print(f"   ⚠️ MEDIUM/LOW URGENCY = PROCEED WITH CAUTION")

if __name__ == "__main__":
    system = OddsAwareCornerSystem()
    
    # Test with a live match
    test_fixture_id = 19380117  # Replace with current live match
    system.test_odds_system(test_fixture_id) 