import os
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class ScorelineAwareCornerSystem:
    def __init__(self):
        self.api_key = os.getenv('SPORTMONKS_API_KEY')
        
        # CORE STATS ONLY (removed peripheral stats)
        self.core_stats = {
            # TIER 1: MUST HAVE
            34: "Corners",                  # Weight: ×5
            44: "Dangerous Attacks",        # Weight: ×0.3 (YOU'RE RIGHT - THIS IS CRUCIAL!)
            42: "Shots Total",              # Weight: ×1.5
            
            # TIER 2: PREMIUM (when available)
            49: "Shots Inside Box",         # Weight: ×4 (GAME CHANGER)
            60: "Crosses",                  # Weight: ×2 (GAME CHANGER)
            
            # TIER 3: SUPPORTING
            51: "Offsides",                 # Weight: ×4 (attacking intensity)
            43: "Attacks",                  # Weight: ×0.1
            56: "Free Kicks",               # Weight: ×0.8
            45: "Ball Possession %",        # Weight: ×0.2
        }

    def extract_current_score(self, fixture_data):
        """Extract current match score and analyze scoreline psychology"""
        scores = fixture_data.get('scores', [])
        participants = fixture_data.get('participants', [])
        
        home_score = 0
        away_score = 0
        home_team = "Unknown"
        away_team = "Unknown"
        
        # Get team names
        for participant in participants:
            meta = participant.get('meta', {})
            location = meta.get('location', 'unknown')
            name = participant.get('name', 'Unknown')
            
            if location == 'home':
                home_team = name
            elif location == 'away':
                away_team = name
        
        # Get current score
        for score_entry in scores:
            if score_entry.get('description') == 'CURRENT':
                score_data = score_entry.get('score', {})
                goals = score_data.get('goals', 0)
                participant = score_data.get('participant', '')
                
                if participant == 'home':
                    home_score = goals
                elif participant == 'away':
                    away_score = goals
        
        return {
            'home_team': home_team,
            'away_team': away_team,
            'home_score': home_score,
            'away_score': away_score,
            'scoreline': f"{home_score}-{away_score}"
        }

    def analyze_scoreline_psychology(self, score_data, minute):
        """Analyze how current scoreline affects corner probability"""
        home_score = score_data['home_score']
        away_score = score_data['away_score']
        scoreline = score_data['scoreline']
        
        psychology_score = 0
        urgency_level = "LOW"
        explanation = ""
        
        # SCORELINE PSYCHOLOGY ANALYSIS
        if home_score == away_score:  # DRAW
            if home_score == 0:  # 0-0
                psychology_score += 8
                urgency_level = "HIGH"
                explanation = "0-0 draw - both teams desperate for breakthrough"
            else:  # 1-1, 2-2, etc.
                psychology_score += 12
                urgency_level = "VERY HIGH"
                explanation = f"{scoreline} draw - both teams pushing for winner"
        
        elif abs(home_score - away_score) == 1:  # ONE GOAL DIFFERENCE
            psychology_score += 10
            urgency_level = "HIGH"
            if home_score > away_score:
                explanation = f"Home leading {scoreline} - away team pressing"
            else:
                explanation = f"Away leading {scoreline} - home team pressing"
        
        elif abs(home_score - away_score) == 2:  # TWO GOAL DIFFERENCE
            psychology_score += 5
            urgency_level = "MEDIUM"
            explanation = f"{scoreline} - losing team may push but not desperately"
        
        else:  # 3+ GOAL DIFFERENCE
            psychology_score += 0
            urgency_level = "LOW"
            explanation = f"{scoreline} - game likely decided, low urgency"
        
        # LATE GAME MULTIPLIER (70+ minutes)
        if minute >= 70:
            if urgency_level == "VERY HIGH":
                psychology_score *= 1.5  # Multiply by 1.5 for very high urgency
            elif urgency_level == "HIGH":
                psychology_score *= 1.3  # Multiply by 1.3 for high urgency
            
            explanation += f" + late game pressure (min {minute})"
        
        return {
            'psychology_score': psychology_score,
            'urgency_level': urgency_level,
            'explanation': explanation,
            'scoreline': scoreline
        }

    def calculate_enhanced_prediction(self, fixture_data, quality_data, minute):
        """Enhanced prediction including scoreline psychology"""
        statistics = fixture_data.get('statistics', [])
        
        # Group stats by team
        home_stats = {}
        away_stats = {}
        
        for stat in statistics:
            location = stat.get('location', 'unknown')
            type_id = stat.get('type_id')
            value = stat.get('data', {}).get('value', 0)
            
            if location == 'home':
                home_stats[type_id] = value
            elif location == 'away':
                away_stats[type_id] = value
        
        # CORE STATISTICAL ANALYSIS (focused on essentials)
        stats_score = 0
        
        # 1. CORNERS (highest weight)
        corners_total = home_stats.get(34, 0) + away_stats.get(34, 0)
        stats_score += corners_total * 5
        
        # 2. DANGEROUS ATTACKS (crucial for corners!)
        dangerous_attacks = home_stats.get(44, 0) + away_stats.get(44, 0)
        stats_score += dangerous_attacks * 0.4  # Increased weight
        
        # 3. SHOTS ANALYSIS
        if 49 in quality_data['available_types']:  # Premium: Shots Inside Box
            inside_shots = home_stats.get(49, 0) + away_stats.get(49, 0)
            total_shots = home_stats.get(42, 0) + away_stats.get(42, 0)
            stats_score += inside_shots * 4
            
            if total_shots > 0:
                inside_ratio = inside_shots / total_shots
                stats_score += inside_ratio * 20  # Bonus for inside ratio
        else:  # Fallback: Total shots
            total_shots = home_stats.get(42, 0) + away_stats.get(42, 0)
            stats_score += total_shots * 1.5
        
        # 4. CROSSES (premium feature)
        if 60 in quality_data['available_types']:
            crosses = home_stats.get(60, 0) + away_stats.get(60, 0)
            stats_score += crosses * 2
        
        # 5. ATTACKING INTENSITY
        offsides = home_stats.get(51, 0) + away_stats.get(51, 0)
        stats_score += offsides * 4
        
        # SCORELINE PSYCHOLOGY ANALYSIS
        score_data = self.extract_current_score(fixture_data)
        psychology = self.analyze_scoreline_psychology(score_data, minute)
        
        # COMBINE SCORES
        base_score = stats_score + psychology['psychology_score']
        
        # Quality multiplier
        quality_multiplier = 1 + (quality_data['quality_score'] / 200)
        final_score = base_score * quality_multiplier
        
        return {
            'stats_score': stats_score,
            'psychology_score': psychology['psychology_score'],
            'base_score': base_score,
            'quality_multiplier': quality_multiplier,
            'final_score': final_score,
            'score_data': score_data,
            'psychology': psychology,
            'key_stats': {
                'corners': corners_total,
                'dangerous_attacks': dangerous_attacks,
                'shots_inside': home_stats.get(49, 0) + away_stats.get(49, 0),
                'shots_total': home_stats.get(42, 0) + away_stats.get(42, 0),
                'crosses': home_stats.get(60, 0) + away_stats.get(60, 0),
                'offsides': offsides
            }
        }

    def generate_enhanced_recommendation(self, prediction_data, minute):
        """Generate recommendation considering both stats and scoreline"""
        score = prediction_data['final_score']
        psychology = prediction_data['psychology']
        scoreline = prediction_data['score_data']['scoreline']
        
        if minute < 70:
            return {
                'action': 'WAIT',
                'confidence': 'N/A',
                'reason': f"Wait until 70+ minutes (currently {minute}') | Score: {scoreline}",
                'trajectory_score': score
            }
        
        # Enhanced recommendations considering scoreline
        if score >= 60 and psychology['urgency_level'] in ['HIGH', 'VERY HIGH']:
            return {
                'action': 'STRONG BUY',
                'confidence': 'VERY HIGH',
                'reason': f"Excellent stats + {psychology['explanation']} (Score: {score:.1f})",
                'expected_outcome': 'High likelihood of 2+ more corners'
            }
        elif score >= 40 and psychology['urgency_level'] != 'LOW':
            return {
                'action': 'BUY',
                'confidence': 'HIGH',
                'reason': f"Good stats + scoreline pressure (Score: {score:.1f})",
                'expected_outcome': 'Moderate likelihood of 1-2 more corners'
            }
        elif score >= 25:
            return {
                'action': 'WEAK BUY',
                'confidence': 'MEDIUM',
                'reason': f"Fair opportunity (Score: {score:.1f}) | {scoreline}",
                'expected_outcome': 'Low-moderate likelihood of 1 more corner'
            }
        else:
            return {
                'action': 'AVOID',
                'confidence': 'N/A',
                'reason': f"Insufficient activity (Score: {score:.1f}) | {scoreline}",
                'expected_outcome': 'Very low corner probability'
            }

    def test_enhanced_system(self, match_id):
        """Test the enhanced system on a specific match"""
        print(f"🎯 ENHANCED CORNER SYSTEM TEST (with Scoreline Analysis)")
        print(f"📊 Match ID: {match_id}")
        print("=" * 80)
        
        # Get fixture data
        fixture_url = f"https://api.sportmonks.com/v3/football/fixtures/{match_id}"
        fixture_params = {
            'api_token': self.api_key,
            'include': 'statistics;participants;state;periods;scores'
        }
        
        response = requests.get(fixture_url, params=fixture_params)
        if response.status_code == 200:
            fixture_data = response.json()['data']
            
            # Get match timing
            periods = fixture_data.get('periods', [])
            minute = 0
            for period in periods:
                if period.get('ticking', False):
                    minute = period.get('minutes', 0)
                    if '2nd' in period.get('description', '').lower():
                        minute += 45
                    break
            
            # Assess quality
            statistics = fixture_data.get('statistics', [])
            available_types = set(stat.get('type_id') for stat in statistics)
            premium_count = sum(1 for t in [49, 60, 53, 62] if t in available_types)
            quality_score = len(statistics) + len(available_types) * 2 + premium_count * 15
            
            quality_data = {
                'quality_score': quality_score,
                'available_types': available_types,
                'premium_count': premium_count
            }
            
            # Run enhanced prediction
            prediction = self.calculate_enhanced_prediction(fixture_data, quality_data, minute)
            recommendation = self.generate_enhanced_recommendation(prediction, minute)
            
            # Display results
            print(f"⚽ MATCH: {prediction['score_data']['home_team']} vs {prediction['score_data']['away_team']}")
            print(f"🏆 CURRENT SCORE: {prediction['score_data']['scoreline']} | Minute: {minute}'")
            print()
            
            print(f"📊 CORE STATISTICS:")
            stats = prediction['key_stats']
            print(f"   Corners: {stats['corners']} | Dangerous Attacks: {stats['dangerous_attacks']}")
            print(f"   Shots Inside: {stats['shots_inside']} | Total Shots: {stats['shots_total']}")
            print(f"   Crosses: {stats['crosses']} | Offsides: {stats['offsides']}")
            print()
            
            print(f"🧠 SCORELINE PSYCHOLOGY:")
            psych = prediction['psychology']
            print(f"   {psych['explanation']}")
            print(f"   Urgency Level: {psych['urgency_level']}")
            print(f"   Psychology Score: {psych['psychology_score']:.1f}")
            print()
            
            print(f"🎯 FINAL ANALYSIS:")
            print(f"   Stats Score: {prediction['stats_score']:.1f}")
            print(f"   Psychology Score: {prediction['psychology_score']:.1f}")
            print(f"   Quality Multiplier: {prediction['quality_multiplier']:.2f}x")
            print(f"   🎯 FINAL SCORE: {prediction['final_score']:.1f}")
            print()
            
            rec = recommendation
            action_emoji = {'STRONG BUY': '🟢', 'BUY': '🟡', 'WEAK BUY': '🟠', 'AVOID': '🔴', 'WAIT': '⏰'}
            print(f"   {action_emoji.get(rec['action'], '❓')} RECOMMENDATION: {rec['action']}")
            print(f"   💡 {rec['reason']}")
            if 'expected_outcome' in rec:
                print(f"   📈 {rec['expected_outcome']}")

if __name__ == "__main__":
    system = ScorelineAwareCornerSystem()
    
    # Test with a live match that has good stats
    test_match_id = 19380117  # Or get from live matches
    system.test_enhanced_system(test_match_id) 