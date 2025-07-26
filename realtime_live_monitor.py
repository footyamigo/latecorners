import os
import requests
from dotenv import load_dotenv
import json
import time
from datetime import datetime
import threading
from collections import defaultdict

load_dotenv()

class RealtimeLiveMonitor:
    """Real-time monitoring system for live football matches"""
    
    def __init__(self, check_interval=60):
        self.api_key = os.getenv('SPORTMONKS_API_KEY')
        if not self.api_key:
            raise ValueError("SPORTMONKS_API_KEY not found in environment variables")
        
        self.check_interval = check_interval  # seconds
        self.running = False
        
        # Track match states
        self.current_live_matches = {}  # match_id -> match_data
        self.match_history = []  # Historical tracking
        self.session_stats = {
            'start_time': datetime.now(),
            'total_checks': 0,
            'new_matches_detected': 0,
            'matches_ended': 0,
            'max_concurrent_live': 0,
            'api_errors': 0
        }
        
        print("🚀 REALTIME LIVE MATCH MONITOR INITIALIZED")
        print(f"   Check interval: {check_interval} seconds")
        print(f"   Started at: {datetime.now().strftime('%H:%M:%S')}")
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        
        print(f"\n🔄 STARTING CONTINUOUS LIVE MONITORING")
        print("=" * 80)
        print("   Press Ctrl+C to stop monitoring")
        print("=" * 80)
        
        self.running = True
        
        try:
            while self.running:
                self._check_live_matches()
                
                if self.running:  # Check if still running after the check
                    print(f"\n⏰ Next check in {self.check_interval} seconds...")
                    time.sleep(self.check_interval)
                    
        except KeyboardInterrupt:
            print(f"\n🛑 MONITORING STOPPED BY USER")
            self._show_session_summary()
        except Exception as e:
            print(f"\n❌ MONITORING ERROR: {e}")
            self._show_session_summary()
    
    def _check_live_matches(self):
        """Check current live matches and detect changes"""
        
        check_time = datetime.now()
        self.session_stats['total_checks'] += 1
        
        print(f"\n🔍 CHECKING LIVE MATCHES - {check_time.strftime('%H:%M:%S')}")
        
        try:
            # Get current live matches
            live_matches = self._get_live_matches()
            
            if live_matches is None:
                self.session_stats['api_errors'] += 1
                print("   ❌ API Error - skipping this check")
                return
            
            # Convert to dict for comparison
            current_match_ids = {match['match_id'] for match in live_matches}
            previous_match_ids = set(self.current_live_matches.keys())
            
            # Detect changes
            new_matches = current_match_ids - previous_match_ids
            ended_matches = previous_match_ids - current_match_ids
            continuing_matches = current_match_ids & previous_match_ids
            
            # Update statistics
            if len(current_match_ids) > self.session_stats['max_concurrent_live']:
                self.session_stats['max_concurrent_live'] = len(current_match_ids)
            
            self.session_stats['new_matches_detected'] += len(new_matches)
            self.session_stats['matches_ended'] += len(ended_matches)
            
            # Update current matches
            self.current_live_matches = {match['match_id']: match for match in live_matches}
            
            # Display current status
            self._display_live_status(live_matches, new_matches, ended_matches, continuing_matches)
            
            # Log this check
            self.match_history.append({
                'timestamp': check_time.isoformat(),
                'total_live': len(current_match_ids),
                'new_matches': len(new_matches),
                'ended_matches': len(ended_matches),
                'new_match_ids': list(new_matches),
                'ended_match_ids': list(ended_matches)
            })
            
            # Save current state
            self._save_current_state(live_matches)
            
        except Exception as e:
            print(f"   ❌ Error in check: {e}")
            self.session_stats['api_errors'] += 1
    
    def _get_live_matches(self):
        """Get current live matches from API"""
        
        url = f"https://api.sportmonks.com/v3/football/livescores/inplay"
        params = {
            'api_token': self.api_key,
            'include': 'scores;participants;state;periods;league;statistics'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            matches = response.json().get('data', [])
            
            # Filter for truly live matches (using our improved logic)
            live_matches = []
            
            for match in matches:
                periods = match.get('periods', [])
                has_ticking = any(period.get('ticking', False) for period in periods)
                
                # Include ANY match with ticking period
                if has_ticking:
                    match_data = self._extract_match_data(match)
                    if match_data:
                        live_matches.append(match_data)
            
            return live_matches
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ API Error: {e}")
            return None
        except Exception as e:
            print(f"   ❌ Processing Error: {e}")
            return None
    
    def _extract_match_data(self, match):
        """Extract essential match data"""
        
        try:
            match_id = match['id']
            
            # Get state and minute
            state = match.get('state', {})
            state_short = state.get('short_name', 'unknown')
            actual_minute = self._extract_match_minute(match)
            
            # Get teams
            participants = match.get('participants', [])
            home_team = away_team = "Unknown"
            
            for participant in participants:
                meta = participant.get('meta', {})
                location = meta.get('location', 'unknown')
                name = participant.get('name', 'Unknown')
                
                if location == 'home':
                    home_team = name
                elif location == 'away':
                    away_team = name
            
            # Get score
            scores = match.get('scores', [])
            home_score = away_score = 0
            
            for score_entry in scores:
                if score_entry.get('description') == 'CURRENT':
                    score_data = score_entry.get('score', {})
                    goals = score_data.get('goals', 0)
                    participant = score_data.get('participant', '')
                    
                    if participant == 'home':
                        home_score = goals
                    elif participant == 'away':
                        away_score = goals
            
            # Get league
            league_info = match.get('league', {})
            league_name = league_info.get('name', 'Unknown League')
            
            return {
                'match_id': match_id,
                'home_team': home_team,
                'away_team': away_team,
                'scoreline': f"{home_score}-{away_score}",
                'home_score': home_score,
                'away_score': away_score,
                'minute': actual_minute,
                'state': state_short,
                'league': league_name,
                'teams_display': f"{home_team} vs {away_team}",
                'last_seen': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"   ⚠️ Error extracting match {match.get('id', 'unknown')}: {e}")
            return None
    
    def _extract_match_minute(self, match):
        """Extract match minute from periods"""
        periods = match.get('periods', [])
        for period in periods:
            if period.get('ticking', False):
                return period.get('minutes', 0)
        return 0
    
    def _display_live_status(self, live_matches, new_matches, ended_matches, continuing_matches):
        """Display current live match status"""
        
        total_live = len(live_matches)
        
        print(f"📊 LIVE MATCH STATUS:")
        print(f"   🔴 Currently Live: {total_live} matches")
        print(f"   🟢 New This Check: {len(new_matches)} matches")
        print(f"   🔴 Ended This Check: {len(ended_matches)} matches")
        print(f"   ⚪ Continuing: {len(continuing_matches)} matches")
        
        # Show new matches
        if new_matches:
            print(f"\n🚨 NEW LIVE MATCHES:")
            for match in live_matches:
                if match['match_id'] in new_matches:
                    print(f"   🟢 {match['teams_display']} | {match['state']} | {match['minute']}' | {match['scoreline']}")
        
        # Show ended matches
        if ended_matches:
            print(f"\n📄 MATCHES ENDED:")
            for match_id in ended_matches:
                if match_id in self.current_live_matches:
                    match = self.current_live_matches[match_id]
                    print(f"   🔴 {match['teams_display']} | Final: {match['scoreline']}")
        
        # Show sample of continuing matches
        if continuing_matches:
            print(f"\n⚽ LIVE MATCHES (showing first 10):")
            continuing_list = [match for match in live_matches if match['match_id'] in continuing_matches]
            
            for i, match in enumerate(continuing_list[:10]):
                # Highlight late-stage matches
                if match['minute'] >= 80:
                    icon = "🔥"
                elif match['minute'] >= 70:
                    icon = "⚡"
                elif match['minute'] >= 45:
                    icon = "⚽"
                else:
                    icon = "🟢"
                
                print(f"   {icon} {match['teams_display']} | {match['state']} | {match['minute']}' | {match['scoreline']}")
            
            if len(continuing_list) > 10:
                print(f"   ... and {len(continuing_list) - 10} more continuing matches")
        
        # Show session stats
        print(f"\n📈 SESSION STATS:")
        runtime = datetime.now() - self.session_stats['start_time']
        runtime_str = str(runtime).split('.')[0]  # Remove microseconds
        
        print(f"   ⏱️ Runtime: {runtime_str}")
        print(f"   🔍 Total Checks: {self.session_stats['total_checks']}")
        print(f"   🆕 New Matches: {self.session_stats['new_matches_detected']}")
        print(f"   📄 Ended Matches: {self.session_stats['matches_ended']}")
        print(f"   📊 Max Concurrent: {self.session_stats['max_concurrent_live']}")
        print(f"   ❌ API Errors: {self.session_stats['api_errors']}")
    
    def _save_current_state(self, live_matches):
        """Save current state to files"""
        
        try:
            # Save current live matches
            with open('current_live_matches.json', 'w') as f:
                json.dump(live_matches, f, indent=2)
            
            # Save session history
            with open('live_match_history.json', 'w') as f:
                json.dump({
                    'session_stats': {
                        **self.session_stats,
                        'start_time': self.session_stats['start_time'].isoformat(),
                        'last_update': datetime.now().isoformat()
                    },
                    'history': self.match_history
                }, f, indent=2)
                
        except Exception as e:
            print(f"   ⚠️ Error saving state: {e}")
    
    def _show_session_summary(self):
        """Show final session summary"""
        
        runtime = datetime.now() - self.session_stats['start_time']
        
        print(f"\n📊 FINAL SESSION SUMMARY")
        print("=" * 50)
        print(f"   ⏱️ Total Runtime: {str(runtime).split('.')[0]}")
        print(f"   🔍 Total Checks: {self.session_stats['total_checks']}")
        print(f"   🆕 New Matches Detected: {self.session_stats['new_matches_detected']}")
        print(f"   📄 Matches Ended: {self.session_stats['matches_ended']}")
        print(f"   📊 Max Concurrent Live: {self.session_stats['max_concurrent_live']}")
        print(f"   ❌ API Errors: {self.session_stats['api_errors']}")
        
        if self.session_stats['total_checks'] > 0:
            avg_live = sum(entry['total_live'] for entry in self.match_history) / len(self.match_history) if self.match_history else 0
            print(f"   📈 Average Live Matches: {avg_live:.1f}")
        
        print(f"\n💾 Data saved to:")
        print(f"   📄 current_live_matches.json")
        print(f"   📊 live_match_history.json")

def main():
    """Main function to start monitoring"""
    
    import argparse
    parser = argparse.ArgumentParser(description='Real-time Live Match Monitor')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds (default: 60)')
    args = parser.parse_args()
    
    try:
        monitor = RealtimeLiveMonitor(check_interval=args.interval)
        monitor.start_monitoring()
        
    except Exception as e:
        print(f"❌ Error starting monitor: {e}")

if __name__ == "__main__":
    main() 