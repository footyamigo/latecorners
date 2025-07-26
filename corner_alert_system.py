import os
import requests
from dotenv import load_dotenv
import json
import time
from datetime import datetime
from live_data_collector import LiveDataCollector

load_dotenv()

class CornerAlertSystem:
    """Monitors live matches and triggers alerts for corner betting opportunities"""
    
    def __init__(self):
        self.api_key = os.getenv('SPORTMONKS_API_KEY')
        self.collector = LiveDataCollector()
        self.monitored_matches = {}  # Track matches we're monitoring
        self.alert_history = []  # Track sent alerts
        
        # Alert thresholds
        self.PSYCHOLOGY_THRESHOLD = 25.0
        self.ALERT_MINUTE = 85
        self.MAX_ALERT_MINUTE = 90  # Stop monitoring after 90 minutes
        
        print("🚨 CORNER ALERT SYSTEM INITIALIZED")
        print(f"   Alert Trigger: {self.ALERT_MINUTE}th minute")
        print(f"   Psychology Threshold: {self.PSYCHOLOGY_THRESHOLD}")
    
    def start_monitoring(self, check_interval=30):
        """Start continuous monitoring for corner opportunities"""
        
        print(f"\n🔄 STARTING CONTINUOUS MONITORING (checking every {check_interval}s)")
        print("=" * 70)
        
        try:
            while True:
                self._check_for_opportunities()
                print(f"\n⏰ Next check in {check_interval} seconds...")
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        except Exception as e:
            print(f"\n❌ Monitoring error: {e}")
    
    def _check_for_opportunities(self):
        """Check current live matches for corner opportunities"""
        
        print(f"\n🔍 CHECKING OPPORTUNITIES - {datetime.now().strftime('%H:%M:%S')}")
        
        # Get live data
        live_data = self.collector.get_all_live_matches()
        
        if not live_data:
            print("   No live matches found")
            return
        
        opportunities = []
        
        for match in live_data:
            try:
                # Skip if no psychology data or bet365 odds
                if not match['psychology'] or not match['has_bet365_odds']:
                    continue
                
                # Calculate detailed psychology score
                psychology_score = self._calculate_detailed_psychology_score(match)
                match['detailed_psychology_score'] = psychology_score
                
                # Check if this match qualifies for monitoring
                if self._qualifies_for_monitoring(match):
                    opportunities.append(match)
                    
                    # Check for immediate alert conditions
                    if self._should_trigger_alert(match):
                        self._trigger_corner_alert(match)
                
            except Exception as e:
                print(f"   ⚠️ Error analyzing {match.get('home_team', 'Unknown')} vs {match.get('away_team', 'Unknown')}: {e}")
        
        # Update monitoring status
        self._update_monitoring_status(opportunities)
    
    def _qualifies_for_monitoring(self, match):
        """Check if match qualifies for monitoring"""
        
        psychology = match.get('psychology')
        minute = match['minute']
        
        # Must have psychology data
        if not psychology:
            return False
        
        # Must have favorable psychology scenario
        if psychology['scenario'] not in ['favorite_trailing', 'draw']:
            return False
        
        # Must be in monitoring window (70-90 minutes)
        if minute < 70 or minute > self.MAX_ALERT_MINUTE:
            return False
        
        # Must have decent psychology score potential
        if match['detailed_psychology_score'] < 15.0:
            return False
        
        return True
    
    def _should_trigger_alert(self, match):
        """Check if we should trigger an alert for this match"""
        
        match_id = match['match_id']
        minute = match['minute']
        psychology_score = match['detailed_psychology_score']
        
        # Must be exactly at alert minute or in desperation time
        if minute < self.ALERT_MINUTE:
            return False
        
        # Must meet psychology threshold
        if psychology_score < self.PSYCHOLOGY_THRESHOLD:
            return False
        
        # Don't alert for same match multiple times
        alert_key = f"{match_id}_{minute//5*5}"  # Group by 5-minute windows
        if alert_key in [alert['key'] for alert in self.alert_history]:
            return False
        
        return True
    
    def _trigger_corner_alert(self, match):
        """Trigger corner betting alert with Asian corner odds"""
        
        print(f"\n🚨 CORNER ALERT TRIGGERED!")
        print("=" * 50)
        
        match_id = match['match_id']
        
        # Get Asian corner odds
        asian_corner_odds = self._get_asian_corner_odds(match_id)
        
        # Create alert data
        alert_data = {
            'timestamp': datetime.now().isoformat(),
            'match_id': match_id,
            'key': f"{match_id}_{match['minute']//5*5}",
            'teams': f"{match['home_team']} vs {match['away_team']}",
            'scoreline': match['scoreline'],
            'minute': match['minute'],
            'league': match['league_name'],
            'psychology_score': match['detailed_psychology_score'],
            'scenario': match['psychology']['scenario'],
            'confidence': match['psychology']['confidence'],
            'bet365_1x2_odds': match['bet365_odds'],
            'asian_corner_odds': asian_corner_odds,
            'recommendation': self._generate_recommendation(match, asian_corner_odds)
        }
        
        # Display alert
        self._display_alert(alert_data)
        
        # Save alert
        self.alert_history.append(alert_data)
        self._save_alert(alert_data)
    
    def _get_asian_corner_odds(self, match_id):
        """Get Asian corner odds from bet365"""
        
        try:
            # Asian Total Corners (Market ID 61)
            asian_total_url = f"https://api.sportmonks.com/v3/football/odds/inplay/fixtures/{match_id}/markets/61"
            
            # Asian Handicap Corners (Market ID 62)  
            asian_handicap_url = f"https://api.sportmonks.com/v3/football/odds/inplay/fixtures/{match_id}/markets/62"
            
            params = {'api_token': self.api_key}
            
            corner_odds = {}
            
            # Get Asian Total Corners
            try:
                response = requests.get(asian_total_url, params=params, timeout=10)
                if response.status_code == 200:
                    total_odds = response.json().get('data', [])
                    bet365_total = [odds for odds in total_odds if odds.get('bookmaker_id') == 2]
                    
                    if bet365_total:
                        corner_odds['asian_total'] = self._parse_asian_total_odds(bet365_total)
            except:
                pass
            
            # Get Asian Handicap Corners
            try:
                response = requests.get(asian_handicap_url, params=params, timeout=10)
                if response.status_code == 200:
                    handicap_odds = response.json().get('data', [])
                    bet365_handicap = [odds for odds in handicap_odds if odds.get('bookmaker_id') == 2]
                    
                    if bet365_handicap:
                        corner_odds['asian_handicap'] = self._parse_asian_handicap_odds(bet365_handicap)
            except:
                pass
            
            return corner_odds if corner_odds else None
            
        except Exception as e:
            print(f"   ⚠️ Error getting Asian corner odds: {e}")
            return None
    
    def _parse_asian_total_odds(self, odds_data):
        """Parse Asian Total corner odds"""
        
        parsed = {}
        
        for odds in odds_data:
            label = odds.get('label', '').lower()
            value = odds.get('value', 0)
            total = odds.get('total', 0)
            
            if 'over' in label:
                parsed[f'over_{total}'] = float(value)
            elif 'under' in label:
                parsed[f'under_{total}'] = float(value)
        
        return parsed
    
    def _parse_asian_handicap_odds(self, odds_data):
        """Parse Asian Handicap corner odds"""
        
        parsed = {}
        
        for odds in odds_data:
            label = odds.get('label', '').lower()
            value = odds.get('value', 0)
            handicap = odds.get('handicap', 0)
            
            if 'home' in label:
                parsed[f'home_{handicap}'] = float(value)
            elif 'away' in label:
                parsed[f'away_{handicap}'] = float(value)
        
        return parsed
    
    def _calculate_detailed_psychology_score(self, match):
        """Calculate detailed psychology score"""
        
        psychology = match['psychology']
        minute = match['minute']
        home_score = match['home_score']
        away_score = match['away_score']
        
        if not psychology:
            return 0
        
        base_score = 0
        
        # Scenario scoring
        if psychology['scenario'] == 'favorite_trailing':
            if psychology['confidence'] == 'HEAVY':
                base_score = 22.5
            elif psychology['confidence'] == 'STRONG':
                base_score = 19.5
            elif psychology['confidence'] == 'MODERATE':
                base_score = 16.5
            else:
                base_score = 15.0
        elif psychology['scenario'] == 'draw':
            if home_score == 0:
                base_score = 8.0  # 0-0
            else:
                base_score = 12.0  # 1-1, 2-2, etc.
        elif psychology['scenario'] == 'underdog_trailing':
            base_score = 10.0
        
        # Time multiplier
        if minute >= 85:
            time_multiplier = 2.5
        elif minute >= 75:
            time_multiplier = 2.0
        elif minute >= 60:
            time_multiplier = 1.5
        else:
            time_multiplier = 1.0
        
        return base_score * time_multiplier
    
    def _generate_recommendation(self, match, asian_corner_odds):
        """Generate betting recommendation"""
        
        psychology_score = match['detailed_psychology_score']
        minute = match['minute']
        scenario = match['psychology']['scenario']
        
        if psychology_score >= 35:
            urgency = "EXTREME"
            action = "IMMEDIATE BET"
        elif psychology_score >= 25:
            urgency = "VERY HIGH"
            action = "STRONG BET"
        elif psychology_score >= 15:
            urgency = "HIGH"
            action = "CONSIDER BET"
        else:
            urgency = "MEDIUM"
            action = "MONITOR"
        
        corner_suggestion = "Over corners" if scenario == 'favorite_trailing' else "Monitor corners"
        
        return {
            'urgency': urgency,
            'action': action,
            'corner_suggestion': corner_suggestion,
            'timing': f"Minute {minute}+ ideal",
            'has_asian_odds': asian_corner_odds is not None
        }
    
    def _display_alert(self, alert_data):
        """Display alert information"""
        
        print(f"🔥 {alert_data['teams']}")
        print(f"⏰ {alert_data['minute']}' | Score: {alert_data['scoreline']}")
        print(f"🏟️ {alert_data['league']}")
        print(f"🧠 Psychology: {alert_data['psychology_score']:.1f} ({alert_data['scenario']})")
        print(f"🎯 Confidence: {alert_data['confidence']}")
        
        rec = alert_data['recommendation']
        print(f"⚡ {rec['urgency']} - {rec['action']}")
        print(f"🎯 {rec['corner_suggestion']}")
        
        if alert_data['asian_corner_odds']:
            print("📊 Asian Corner Odds Available:")
            odds = alert_data['asian_corner_odds']
            
            if 'asian_total' in odds:
                print("   Asian Total Corners:")
                for market, value in odds['asian_total'].items():
                    print(f"     {market}: {value}")
            
            if 'asian_handicap' in odds:
                print("   Asian Handicap Corners:")
                for market, value in odds['asian_handicap'].items():
                    print(f"     {market}: {value}")
        else:
            print("⚠️ No Asian corner odds available")
        
        print("\n" + "🔥" * 50)
    
    def _save_alert(self, alert_data):
        """Save alert to file"""
        
        try:
            filename = f"corner_alerts_{datetime.now().strftime('%Y%m%d')}.json"
            
            try:
                with open(filename, 'r') as f:
                    alerts = json.load(f)
            except FileNotFoundError:
                alerts = []
            
            alerts.append(alert_data)
            
            with open(filename, 'w') as f:
                json.dump(alerts, f, indent=2)
                
            print(f"💾 Alert saved to {filename}")
            
        except Exception as e:
            print(f"⚠️ Error saving alert: {e}")
    
    def _update_monitoring_status(self, opportunities):
        """Update monitoring status"""
        
        print(f"\n📊 MONITORING STATUS:")
        print(f"   Opportunities found: {len(opportunities)}")
        
        if opportunities:
            print("   🎯 Current opportunities:")
            for opp in opportunities:
                psychology_score = opp['detailed_psychology_score']
                minute = opp['minute']
                scenario = opp['psychology']['scenario']
                
                status = "🚨 ALERT READY" if minute >= self.ALERT_MINUTE and psychology_score >= self.PSYCHOLOGY_THRESHOLD else "👀 MONITORING"
                
                print(f"      {status} {opp['home_team']} vs {opp['away_team']} | {minute}' | Score: {psychology_score:.1f}")
        
        print(f"   📈 Total alerts sent today: {len(self.alert_history)}")

def main():
    """Main function to start the alert system"""
    
    try:
        alert_system = CornerAlertSystem()
        alert_system.start_monitoring(check_interval=30)  # Check every 30 seconds
        
    except Exception as e:
        print(f"❌ Error starting alert system: {e}")

if __name__ == "__main__":
    main() 