import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()

class PremiumCornerSystem:
    def __init__(self):
        self.api_key = os.getenv('SPORTMONKS_API_KEY')
        
        # Premium stat type mapping (discovered through investigation)
        self.stat_mapping = {
            # CORE STATS (available in most leagues)
            34: "Corners",
            41: "Shots Off Target", 
            42: "Shots Total",
            43: "Attacks",
            44: "Dangerous Attacks",
            45: "Ball Possession %",
            51: "Offsides",
            55: "Throw Ins",
            56: "Free Kicks", 
            84: "Big Chances Missed",
            86: "Saves",
            
            # PREMIUM STATS (major leagues only)
            49: "Shots Inside Box",      # ⭐ GAME CHANGER
            50: "Shots Outside Box",     # ⭐ CALCULATED
            60: "Crosses",               # ⭐ CONFIRMED
            53: "Yellow Cards",          # Premium indicator
            62: "Fouls",                 # Premium indicator
            65: "Interceptions",         # Premium indicator
            
            # ADVANCED STATS (top-tier leagues)
            27264: "Successful Long Passes",
            27265: "Successful Long Passes %",
            1605: "Pass Accuracy %",
        }
        
        # League quality tiers
        self.league_tiers = {
            'premium': [
                'Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1',
                'Champions League', 'Europa League', 'Primeira Liga', 'Eredivisie'
            ],
            'high': [
                'Championship', 'MLS', 'First Division', 'Superliga', 
                'Pro League', '2. Bundesliga', 'Serie B'
            ],
            'medium': [
                '2. Liga', '1. Liga', 'League One', 'League Two'
            ]
        }

    def get_live_matches(self):
        """Get all live matches with comprehensive data"""
        url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
        params = {
            'api_token': self.api_key,
            'include': 'scores;participants;state;events;periods;league'
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get('data', [])
        return []

    def assess_match_quality(self, match_id):
        """Assess the statistical quality of a match"""
        fixture_url = f"https://api.sportmonks.com/v3/football/fixtures/{match_id}"
        fixture_params = {
            'api_token': self.api_key,
            'include': 'statistics;participants;state;periods;league'
        }
        
        try:
            response = requests.get(fixture_url, params=fixture_params)
            if response.status_code == 200:
                fixture_data = response.json()
                
                if 'data' in fixture_data:
                    fixture = fixture_data['data']
                    statistics = fixture.get('statistics', [])
                    
                    # Count available stat types
                    available_types = set()
                    for stat in statistics:
                        available_types.add(stat.get('type_id'))
                    
                    # Check for premium stats
                    premium_stats = [49, 50, 60, 53, 62, 65, 27264, 27265, 1605]
                    premium_count = sum(1 for stat_id in premium_stats if stat_id in available_types)
                    
                    # Calculate quality score
                    quality_score = len(statistics) + (len(available_types) * 2) + (premium_count * 15)
                    
                    return {
                        'total_stats': len(statistics),
                        'unique_types': len(available_types),
                        'premium_count': premium_count,
                        'quality_score': quality_score,
                        'available_types': available_types,
                        'fixture_data': fixture
                    }
        except Exception as e:
            pass
        
        return None

    def calculate_corner_prediction(self, fixture_data, quality_data):
        """Calculate enhanced corner prediction score"""
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
        
        # Calculate prediction components
        corner_score = 0
        shot_score = 0
        pressure_score = 0
        
        # 1. Direct corner indicators
        corners_total = home_stats.get(34, 0) + away_stats.get(34, 0)
        corner_score += corners_total * 5  # Weight corners heavily
        
        # 2. Shot analysis (premium feature)
        if 49 in quality_data['available_types']:  # Shots Inside Box available
            inside_shots = home_stats.get(49, 0) + away_stats.get(49, 0)
            total_shots = home_stats.get(42, 0) + away_stats.get(42, 0)
            
            shot_score += inside_shots * 4  # Inside shots highly correlate with corners
            
            if total_shots > 0:
                inside_ratio = inside_shots / total_shots
                shot_score += inside_ratio * 20  # Bonus for high inside ratio
        else:
            # Fallback: use total shots
            total_shots = home_stats.get(42, 0) + away_stats.get(42, 0)
            shot_score += total_shots * 1.5
        
        # 3. Crosses analysis (premium feature) 
        if 60 in quality_data['available_types']:  # Crosses available
            crosses = home_stats.get(60, 0) + away_stats.get(60, 0)
            corner_score += crosses * 2  # Crosses directly lead to corners
        
        # 4. Attacking pressure
        dangerous_attacks = home_stats.get(44, 0) + away_stats.get(44, 0)
        offsides = home_stats.get(51, 0) + away_stats.get(51, 0)
        
        pressure_score += dangerous_attacks * 0.3
        pressure_score += offsides * 4  # High attacking intensity
        
        # 5. Set pieces (corner opportunities)
        free_kicks = home_stats.get(56, 0) + away_stats.get(56, 0)
        throw_ins = home_stats.get(55, 0) + away_stats.get(55, 0)
        
        pressure_score += free_kicks * 0.8
        pressure_score += throw_ins * 0.4
        
        # Combine scores
        base_score = corner_score + shot_score + pressure_score
        
        # Apply quality multiplier
        quality_multiplier = 1 + (quality_data['quality_score'] / 200)
        final_score = base_score * quality_multiplier
        
        return {
            'corner_score': corner_score,
            'shot_score': shot_score, 
            'pressure_score': pressure_score,
            'base_score': base_score,
            'quality_multiplier': quality_multiplier,
            'final_score': final_score,
            'stats_used': {
                'corners': corners_total,
                'shots_inside': home_stats.get(49, 0) + away_stats.get(49, 0),
                'shots_total': home_stats.get(42, 0) + away_stats.get(42, 0),
                'crosses': home_stats.get(60, 0) + away_stats.get(60, 0),
                'dangerous_attacks': dangerous_attacks,
                'offsides': offsides
            }
        }

    def get_match_timing(self, fixture_data):
        """Get current match timing information"""
        state = fixture_data.get('state', {})
        periods = fixture_data.get('periods', [])
        
        minute = 0
        is_second_half = False
        
        for period in periods:
            if period.get('ticking', False):
                minute = period.get('minutes', 0)
                period_desc = period.get('description', '').lower()
                if '2nd' in period_desc:
                    minute += 45
                    is_second_half = True
                break
        
        return {
            'minute': minute,
            'is_second_half': is_second_half,
            'state': state.get('developer_name', 'Unknown'),
            'is_late_game': minute >= 70
        }

    def generate_recommendation(self, prediction_data, timing_data, quality_data):
        """Generate intelligent betting recommendation"""
        score = prediction_data['final_score']
        minute = timing_data['minute']
        
        if not timing_data['is_late_game']:
            return {
                'action': 'WAIT',
                'confidence': 'N/A',
                'reason': f"Wait until 70+ minutes (currently {minute}')",
                'trajectory_score': score
            }
        
        # Determine recommendation based on score and quality
        if score >= 60 and quality_data['premium_count'] >= 3:
            return {
                'action': 'STRONG BUY',
                'confidence': 'HIGH',
                'reason': f"Premium data + exceptional activity (Score: {score:.1f})",
                'expected_corners': 'High likelihood of 2+ more corners'
            }
        elif score >= 40 and quality_data['premium_count'] >= 2:
            return {
                'action': 'BUY', 
                'confidence': 'MEDIUM',
                'reason': f"Good data quality + solid activity (Score: {score:.1f})",
                'expected_corners': 'Moderate likelihood of 1-2 more corners'
            }
        elif score >= 25:
            return {
                'action': 'WEAK BUY',
                'confidence': 'LOW',
                'reason': f"Fair opportunity but proceed with caution (Score: {score:.1f})",
                'expected_corners': 'Low-moderate likelihood of 1 more corner'
            }
        else:
            return {
                'action': 'AVOID',
                'confidence': 'N/A',
                'reason': f"Insufficient activity for corner betting (Score: {score:.1f})",
                'expected_corners': 'Very low corner probability'
            }

    def analyze_live_opportunities(self, max_matches=10):
        """Main function to analyze live corner betting opportunities"""
        print("🚀 PREMIUM CORNER BETTING SYSTEM v2.0")
        print("=" * 80)
        print(f"⏰ Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Get live matches
        matches = self.get_live_matches()
        print(f"📊 Found {len(matches)} live matches")
        
        opportunities = []
        
        print(f"\n🔍 ANALYZING TOP {max_matches} MATCHES FOR QUALITY:")
        print("   " + "-" * 70)
        
        for i, match in enumerate(matches[:max_matches]):
            match_id = match['id']
            league_info = match.get('league', {})
            league_name = league_info.get('name', 'Unknown')
            
            # Get team names
            participants = match.get('participants', [])
            teams = []
            for participant in participants:
                teams.append(participant.get('name', 'Unknown'))
            
            teams_str = ' vs '.join(teams)
            print(f"   {i+1:2d}. {teams_str[:40]:<40} | {league_name[:25]}")
            
            # Assess quality
            quality_data = self.assess_match_quality(match_id)
            
            if quality_data and quality_data['quality_score'] >= 30:  # Minimum quality threshold
                fixture_data = quality_data['fixture_data']
                
                # Calculate prediction
                prediction = self.calculate_corner_prediction(fixture_data, quality_data)
                timing = self.get_match_timing(fixture_data)
                recommendation = self.generate_recommendation(prediction, timing, quality_data)
                
                opportunities.append({
                    'match_id': match_id,
                    'teams': teams_str,
                    'league': league_name,
                    'quality_data': quality_data,
                    'prediction': prediction,
                    'timing': timing,
                    'recommendation': recommendation
                })
        
        # Sort by final score (best opportunities first)
        opportunities.sort(key=lambda x: x['prediction']['final_score'], reverse=True)
        
        # Display results
        print(f"\n🎯 CORNER BETTING OPPORTUNITIES:")
        print("=" * 80)
        
        if not opportunities:
            print("❌ No quality opportunities found at this time")
            return
        
        for i, opp in enumerate(opportunities[:5]):  # Show top 5
            print(f"\n🏆 OPPORTUNITY #{i+1}")
            print(f"   Match: {opp['teams']}")
            print(f"   League: {opp['league']}")
            print(f"   Minute: {opp['timing']['minute']}' | State: {opp['timing']['state']}")
            print(f"   Quality Score: {opp['quality_data']['quality_score']} | Premium Stats: {opp['quality_data']['premium_count']}")
            
            pred = opp['prediction']
            print(f"   📊 Statistics Used:")
            print(f"      Corners: {pred['stats_used']['corners']} | Shots Inside: {pred['stats_used']['shots_inside']}")
            print(f"      Total Shots: {pred['stats_used']['shots_total']} | Crosses: {pred['stats_used']['crosses']}")
            print(f"      Dangerous Attacks: {pred['stats_used']['dangerous_attacks']} | Offsides: {pred['stats_used']['offsides']}")
            
            print(f"   🎯 Prediction Score: {pred['final_score']:.1f}")
            
            rec = opp['recommendation'] 
            action_emoji = {
                'STRONG BUY': '🟢',
                'BUY': '🟡', 
                'WEAK BUY': '🟠',
                'AVOID': '🔴',
                'WAIT': '⏰'
            }
            
            print(f"   {action_emoji.get(rec['action'], '❓')} RECOMMENDATION: {rec['action']}")
            print(f"   💡 {rec['reason']}")
            if 'expected_corners' in rec:
                print(f"   📈 {rec['expected_corners']}")

if __name__ == "__main__":
    system = PremiumCornerSystem()
    system.analyze_live_opportunities(max_matches=15) 