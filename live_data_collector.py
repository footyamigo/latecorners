import os
import requests
from dotenv import load_dotenv
import json
import time
from datetime import datetime

load_dotenv()

class LiveDataCollector:
    """Collects comprehensive live match data for corner betting analysis"""
    
    def __init__(self):
        self.api_key = os.getenv('SPORTMONKS_API_KEY')
        if not self.api_key:
            raise ValueError("SPORTMONKS_API_KEY not found in environment variables")
    
    def get_all_live_matches(self):
        """Get all truly live matches with comprehensive data"""
        
        print(f"🔄 COLLECTING LIVE MATCH DATA - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 70)
        
        # Get live matches with all necessary includes
        url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
        params = {
            'api_token': self.api_key,
            'include': 'scores;participants;state;periods;league;statistics'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            matches = response.json().get('data', [])
            print(f"📊 Retrieved {len(matches)} inplay matches from API")
            
            # Filter for truly live matches
            live_matches = self._filter_truly_live_matches(matches)
            print(f"⚽ Found {len(live_matches)} truly live matches")
            
            # Collect comprehensive data for each live match
            live_data = []
            
            for i, match in enumerate(live_matches):
                try:
                    match_data = self._collect_match_data(match)
                    if match_data:
                        live_data.append(match_data)
                        print(f"✅ {i+1:2d}. {match_data['home_team']} vs {match_data['away_team']} | {match_data['minute']}' | {match_data['scoreline']}")
                    
                except Exception as e:
                    print(f"⚠️ Error processing match {match.get('id', 'unknown')}: {e}")
            
            print(f"\n📦 COLLECTED DATA FOR {len(live_data)} MATCHES")
            return live_data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API Error: {e}")
            return []
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return []
    
    def _filter_truly_live_matches(self, matches):
        """Filter matches to only include those truly live and playing"""
        
        live_matches = []
        
        for match in matches:
            periods = match.get('periods', [])
            has_ticking = any(period.get('ticking', False) for period in periods)
            
            # Include ANY match with ticking period (SportMonks definitive live indicator)
            if has_ticking:
                state = match.get('state', {})
                state_short = state.get('short_name', 'unknown')
                actual_minute = self._extract_match_minute(match)
                
                match['_live_minute'] = actual_minute
                match['_live_state'] = state_short
                live_matches.append(match)
        
        return live_matches
    
    def _extract_match_minute(self, match):
        """Extract actual match minute from periods data"""
        
        periods = match.get('periods', [])
        for period in periods:
            if period.get('ticking', False):
                return period.get('minutes', 0)
        return 0
    
    def _collect_match_data(self, match):
        """Collect comprehensive data for a single match"""
        
        match_id = match['id']
        live_minute = match.get('_live_minute', 0)
        live_state = match.get('_live_state', 'unknown')
        
        # Extract team info
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
        
        # Extract league info
        league_info = match.get('league', {})
        league_name = league_info.get('name', 'Unknown League')
        league_id = league_info.get('id')
        
        # Extract current score
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
        
        # Extract statistics
        statistics = self._extract_statistics(match)
        
        # Get bet365 1x2 odds for psychology
        bet365_odds = self._get_bet365_1x2_odds(match_id)
        
        # Calculate basic psychology indicators
        psychology_data = self._calculate_psychology_indicators(
            home_score, away_score, bet365_odds, live_minute
        )
        
        return {
            'match_id': match_id,
            'home_team': home_team,
            'away_team': away_team,
            'home_id': home_id,
            'away_id': away_id,
            'league_name': league_name,
            'league_id': league_id,
            'scoreline': f"{home_score}-{away_score}",
            'home_score': home_score,
            'away_score': away_score,
            'minute': live_minute,
            'state': live_state,
            'statistics': statistics,
            'bet365_odds': bet365_odds,
            'psychology': psychology_data,
            'timestamp': datetime.now().isoformat(),
            'has_bet365_odds': bet365_odds is not None
        }
    
    def _extract_statistics(self, match):
        """Extract relevant statistics from match data"""
        
        statistics = match.get('statistics', [])
        
        # Key stat type IDs we need
        stat_mapping = {
            34: 'corners',          # Corners ✅ (Type 34 - original working + official docs)
            42: 'shots_total',      # Shots Total
            86: 'shots_on_target',  # Shots on Target ✅ (Type 86 - confirmed)
            41: 'shots_off_target', # Shots off Target ✅ (Type 41 - confirmed)  
            44: 'dangerous_attacks', # Dangerous Attacks
            45: 'ball_possession',  # Ball Possession % ✅ (Type 45 - original working system)
            49: 'shots_inside_box', # Shots Inside Box (premium)
            60: 'crosses',          # Crosses (premium)
        }
        
        home_stats = {}
        away_stats = {}
        
        for stat in statistics:
            type_id = stat.get('type_id')
            if type_id in stat_mapping:
                stat_name = stat_mapping[type_id]
                value = stat.get('data', {}).get('value', 0)
                location = stat.get('location', 'unknown')
                
                if location == 'home':
                    home_stats[stat_name] = value
                elif location == 'away':
                    away_stats[stat_name] = value
        
        return {
            'home': home_stats,
            'away': away_stats,
            'quality_score': len(home_stats) + len(away_stats)  # Simple quality indicator
        }
    
    def _get_bet365_1x2_odds(self, match_id):
        """Get bet365 1x2 odds for psychology calculation"""
        
        try:
            fixture_url = f"https://api.sportmonks.com/v3/football/fixtures/{match_id}"
            fixture_params = {
                'api_token': self.api_key,
                'include': 'odds;participants;scores'
            }
            
            response = requests.get(fixture_url, params=fixture_params, timeout=15)
            if response.status_code != 200:
                return None
                
            fixture_data = response.json()['data']
            odds_data = fixture_data.get('odds', [])
            
            # Filter for bet365 1x2 odds
            bet365_odds = [odds for odds in odds_data if odds.get('bookmaker_id') == 2]
            
            home_odds = None
            away_odds = None
            draw_odds = None
            
            for odds in bet365_odds:
                market_desc = odds.get('market_description', '').lower()
                
                # Look for match winner markets with broader search
                if any(term in market_desc for term in ['1x2', 'match winner', 'full time result', 'match result']):
                    label = odds.get('label', '').lower()
                    value = float(odds.get('value', 0))
                    
                    # More flexible label matching
                    if label in ['home', '1', 'home win']:
                        home_odds = value
                    elif label in ['away', '2', 'away win']:
                        away_odds = value
                    elif label in ['draw', 'x', 'tie']:
                        draw_odds = value
            
            if home_odds and away_odds:
                return {
                    'home': home_odds,
                    'away': away_odds,
                    'draw': draw_odds
                }
            
            return None
            
        except Exception as e:
            return None
    
    def _calculate_psychology_indicators(self, home_score, away_score, odds, minute):
        """Calculate basic psychology indicators"""
        
        if not odds:
            return None
        
        # Determine favorite
        favorite = 'home' if odds['home'] < odds['away'] else 'away'
        favorite_odds = min(odds['home'], odds['away'])
        underdog_odds = max(odds['home'], odds['away'])
        odds_ratio = underdog_odds / favorite_odds
        
        # Confidence level
        if odds_ratio >= 3.0:
            confidence = 'HEAVY'
        elif odds_ratio >= 2.0:
            confidence = 'STRONG'
        elif odds_ratio >= 1.5:
            confidence = 'MODERATE'
        else:
            confidence = 'SLIGHT'
        
        # Basic scenario detection
        goal_diff = abs(home_score - away_score)
        scenario = 'unknown'
        
        if home_score == away_score:
            scenario = 'draw'
        elif goal_diff == 1:
            if (home_score > away_score and favorite == 'away') or (away_score > home_score and favorite == 'home'):
                scenario = 'favorite_trailing'
            else:
                scenario = 'underdog_trailing'
        elif goal_diff >= 2:
            scenario = 'large_difference'
        
        return {
            'favorite': favorite,
            'confidence': confidence,
            'odds_ratio': odds_ratio,
            'scenario': scenario,
            'goal_difference': goal_diff,
            'is_late_game': minute >= 75,
            'is_desperation_time': minute >= 85
        }

def save_live_data(data, filename='live_matches.json'):
    """Save live data to JSON file"""
    
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"💾 Saved data to {filename}")
    except Exception as e:
        print(f"❌ Error saving data: {e}")

def main():
    """Main function to collect and save live data"""
    
    try:
        collector = LiveDataCollector()
        live_data = collector.get_all_live_matches()
        
        if live_data:
            save_live_data(live_data)
            
            # Show summary
            print(f"\n📊 SUMMARY:")
            print(f"   Total live matches: {len(live_data)}")
            print(f"   With bet365 odds: {sum(1 for m in live_data if m['has_bet365_odds'])}")
            print(f"   Late game (75+ min): {sum(1 for m in live_data if m['minute'] >= 75)}")
            print(f"   Desperation time (85+ min): {sum(1 for m in live_data if m['minute'] >= 85)}")
            
            # Show top psychology opportunities
            high_potential = [m for m in live_data if m['psychology'] and m['psychology']['scenario'] == 'favorite_trailing']
            if high_potential:
                print(f"\n🔥 FAVORITE TRAILING OPPORTUNITIES:")
                for match in high_potential[:3]:
                    print(f"   ⚽ {match['home_team']} vs {match['away_team']} | {match['minute']}' | {match['scoreline']}")
        
        else:
            print("❌ No live data collected")
            
    except Exception as e:
        print(f"❌ Error in main: {e}")

if __name__ == "__main__":
    main() 