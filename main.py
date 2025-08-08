#!/usr/bin/env python3

import asyncio
import copy
import logging
import time
from datetime import datetime
from typing import Dict, Set, Optional
import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_config
from new_telegram_system import send_corner_alert_new, send_system_message_new
from alert_tracker import track_elite_alert
from result_checker import check_pending_results
from startup_flag import is_first_startup, mark_startup
from reliable_corner_system import ReliableCornerSystem  # New scoring system

class LateCornerMonitor:
    """Monitor live matches for late corner betting opportunities using shared dashboard data"""
    
    def __init__(self):
        self.config = get_config()
        
        # Track which matches we've already alerted on
        self.alerted_matches: Set[int] = set()
        self.monitored_matches: Set[int] = set()
        
        # Track previous stats for momentum calculation
        self.previous_stats = {}
        
        # Track discovery cycles
        self.match_discovery_counter = 0
        self.result_check_counter = 0  # For hourly result checking
        
        self.logger = self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        
        # Create logger
        logger = logging.getLogger()
        logger.setLevel(getattr(logging, self.config.LOG_LEVEL))
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, self.config.LOG_LEVEL))
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        if not logger.handlers:
            logger.addHandler(console_handler)
        
        return logger
    
    def _get_shared_live_matches(self):
        """Get live matches from the shared dashboard data source"""
        try:
            # Import dashboard's live data
            from web_dashboard import live_matches_data
            
            # Convert dashboard format to our expected format
            matches = []
            for dashboard_match in live_matches_data:
                # Convert dashboard match format to SportMonks format for compatibility
                converted_match = self._convert_dashboard_to_sportmonks_format(dashboard_match)
                if converted_match:
                    matches.append(converted_match)
            
            self.logger.info(f"📊 SHARED DATA: Got {len(matches)} live matches from dashboard")
            return matches
            
        except ImportError:
            self.logger.error("❌ Cannot import dashboard data - dashboard not running?")
            return []
        except Exception as e:
            self.logger.error(f"❌ Error reading shared dashboard data: {e}")
            return []
    
    def _convert_dashboard_to_sportmonks_format(self, dashboard_match):
        """Convert dashboard match format to SportMonks format for compatibility"""
        try:
            # Create a SportMonks-compatible format from dashboard data
            sportmonks_format = {
                'id': dashboard_match.get('match_id'),
                'participants': [
                    {
                        'name': dashboard_match.get('home_team', 'Unknown'),
                        'meta': {'location': 'home'}
                    },
                    {
                        'name': dashboard_match.get('away_team', 'Unknown'), 
                        'meta': {'location': 'away'}
                    }
                ],
                'scores': [
                    {
                        'description': 'CURRENT',
                        'score': {
                            'goals': dashboard_match.get('home_score', 0),
                            'participant': 'home'
                        }
                    },
                    {
                        'description': 'CURRENT',
                        'score': {
                            'goals': dashboard_match.get('away_score', 0),
                            'participant': 'away'
                        }
                    }
                ],
                'periods': [
                    {
                        'ticking': True,
                        'minutes': dashboard_match.get('minute', 0)
                    }
                ],
                'state': {
                    'short_name': dashboard_match.get('state', 'unknown'),
                    'developer_name': 'INPLAY_2ND_HALF' if dashboard_match.get('minute', 0) > 45 else 'INPLAY_1ST_HALF'
                },
                'league': {
                    'name': dashboard_match.get('league', 'Unknown League')
                },
                'statistics': self._convert_dashboard_stats_to_sportmonks(dashboard_match.get('statistics', {}))
            }
            
            return sportmonks_format
            
        except Exception as e:
            self.logger.error(f"❌ Error converting dashboard match {dashboard_match.get('match_id', 'unknown')}: {e}")
            return None
    
    def _convert_dashboard_stats_to_sportmonks(self, dashboard_stats):
        """Convert dashboard statistics format to SportMonks format"""
        try:
            home_stats = dashboard_stats.get('home', {})
            away_stats = dashboard_stats.get('away', {})
            
            # Convert dashboard stats to SportMonks statistics format
            statistics = []
            
            # Add home team statistics
            for stat_name, value in home_stats.items():
                stat_id = self._get_stat_type_id(stat_name)
                if stat_id:
                    statistics.append({
                        'type_id': stat_id,
                        'data': {'value': value},
                        'location': 'home'
                    })
            
            # Add away team statistics  
            for stat_name, value in away_stats.items():
                stat_id = self._get_stat_type_id(stat_name)
                if stat_id:
                    statistics.append({
                        'type_id': stat_id,
                        'data': {'value': value},
                        'location': 'away'
                    })
            
            return statistics
            
        except Exception as e:
            self.logger.error(f"❌ Error converting dashboard stats: {e}")
            return []
    
    def _get_stat_type_id(self, stat_name: str) -> Optional[int]:
        """Map dashboard stat names to SportMonks type IDs"""
        stat_mapping = {
            'corners': 34,                # CORNERS
            'ball_possession': 45,        # BALL POSSESSION
            'shots_off_target': 41,       # SHOTS_OFF_TARGET
            'shots_total': 42,            # SHOTS_TOTAL
            'dangerous_attacks': 44,      # DANGEROUS_ATTACKS
            'offsides': 51,               # OFFSIDES
            'goal_attempts': 54,          # GOAL_ATTEMPTS
            'throwins': 60,               # THROWINS
            'shots_on_target': 86,        # SHOTS_ON_TARGET
            'crosses_total': 98,          # TOTAL_CROSSES
        }
        return stat_mapping.get(stat_name)
    
    async def _discover_new_matches(self):
        """Discover new live matches using shared dashboard data"""
        try:
            self.logger.info("🔍 DISCOVERING new live matches from shared data...")
            
            # Use shared data instead of direct API call
            live_matches = self._get_shared_live_matches()
            
            if not live_matches:
                self.logger.warning("⚠️ No live matches from shared data source")
                return
            
            self.logger.info(f"📊 Found {len(live_matches)} live matches from shared data")
            
            # Filter matches that are actually in play and worth monitoring
            eligible_matches = []
            for match in live_matches:
                try:
                    # Extract basic match info
                    match_id = match.get('id')
                    if not match_id:
                        continue
                    
                    # Get minute from periods
                    minute = 0
                    periods = match.get('periods', [])
                    for period in periods:
                        if period.get('ticking', False):
                            minute = period.get('minutes', 0)
                            break
                    
                    # Get state from state object
                    state_obj = match.get('state', {})
                    state = state_obj.get('developer_name', 'unknown')
                    
                    self.logger.debug(f"🧪 DEBUG: Match {match_id} - minute: {minute}, state: {state}")
                    
                    # Only monitor matches in active play states
                    if state in ['INPLAY_1ST_HALF', 'INPLAY_2ND_HALF', 'HT']:
                        # Only start monitoring from configured minute
                        if minute >= self.config.MIN_MINUTE_TO_START_MONITORING:
                            eligible_matches.append(match)
                            self.logger.debug(f"✅ Eligible: Match {match_id} at {minute}' ({state})")
                    
                except Exception as e:
                    self.logger.error(f"❌ Error processing match during discovery: {e}")
                    continue
            
            # Add new matches to monitoring
            for match in eligible_matches:
                match_id = match['id']
                if match_id not in self.monitored_matches:
                    self.monitored_matches.add(match_id)
                    self.logger.info(f"➕ ADDED match {match_id} to monitoring")
            
            self.logger.info(f"📊 MONITORING {len(self.monitored_matches)} matches total")
            
        except Exception as e:
            self.logger.error(f"❌ Error in match discovery: {e}")

    async def _monitor_single_match(self, match_data: Dict) -> Optional[Dict]:
        """Monitor a single match for alert conditions using shared data"""
        try:
            fixture_id = match_data.get('id')
            if not fixture_id:
                return None
            
            # Use shared SportMonks client format that we converted
            match_stats = self._parse_match_data_from_shared(match_data)
            if not match_stats:
                return None
            
            # Log detailed match information
            self.logger.info(f"🧪 DEBUG: Stats for match {fixture_id}: {match_stats}")
            
            # Store current stats for momentum tracking
            current_stats = {
                'minute': match_stats.minute,
                'attacks': (match_stats.attacks or {}).copy(),
                'dangerous_attacks': (match_stats.dangerous_attacks or {}).copy(),
                'shots_total': (match_stats.shots_total or {}).copy(),
                'shots_on_target': (match_stats.shots_on_target or {}).copy(),
                'total_corners': match_stats.total_corners,
                'score_diff': match_stats.home_score - match_stats.away_score,
                'is_home': True,  # We'll enhance this later
                'has_live_asian_corners': False,  # Set after odds check
                'home_team': match_stats.home_team,
                'away_team': match_stats.away_team,
                'home_score': match_stats.home_score,
                'away_score': match_stats.away_score,
                'corners_last_15': 0  # We'll calculate this properly later
            }
            
            # Remove finished matches from monitoring
            if match_stats.state == 'FT' or match_stats.minute >= 100:
                if fixture_id in self.monitored_matches:
                    self.monitored_matches.remove(fixture_id)
                    if fixture_id in self.previous_stats:
                        del self.previous_stats[fixture_id]
                    self.logger.info(f"🏁 REMOVED finished match {fixture_id} from monitoring")
                return None
            
            # PRE-CHECKS: Log basic match info
            self.logger.info(f"🔍 PRE-CHECKS: Match {fixture_id} ({match_stats.home_team} vs {match_stats.away_team})")
            self.logger.info(f"   📊 Minute: {match_stats.minute} (need 85-89)")
            self.logger.info(f"   ⚽ Corners: {match_stats.total_corners}")
            self.logger.info(f"   🎮 Match State: {match_stats.state}")
            
            # First, check if we're in the alert window (85-89th minute)
            if not (85 <= match_stats.minute <= 89):
                self.logger.info(f"⏰ Match {fixture_id} outside alert window (need 85-89', currently {match_stats.minute}')")
                # Update previous stats for momentum tracking on next cycle
                self.previous_stats[fixture_id] = copy.deepcopy(current_stats)
                return None

            # Check if we've already alerted on this match
            if fixture_id in self.alerted_matches:
                self.logger.info(f"⏭️ Match {fixture_id} already alerted")
                # Update previous stats for momentum tracking on next cycle
                self.previous_stats[fixture_id] = copy.deepcopy(current_stats)
                return None

            # Get corner odds first - no point calculating if we can't bet
            corner_odds = await self._get_corner_odds(fixture_id)
            if not corner_odds:
                self.logger.warning(f"🚫 Match {fixture_id} - No corner odds available")
                # Update previous stats for momentum tracking on next cycle
                self.previous_stats[fixture_id] = copy.deepcopy(current_stats)
                return None
            # Mark that live asian corners are available
            current_stats['has_live_asian_corners'] = True

            # Get previous stats or empty dict if first time
            previous_stats = self.previous_stats.get(fixture_id, {})

            # Use the reliable corner system to make alert decision
            corner_system = ReliableCornerSystem()
            result = corner_system.should_alert(current_stats, previous_stats, 5)

            # Log the analysis
            self.logger.info(f"\n📊 ANALYZING MATCH {fixture_id}:")
            self.logger.info(f"   {match_stats.home_team} vs {match_stats.away_team}")
            self.logger.info(f"   Score: {match_stats.home_score}-{match_stats.away_score}")
            self.logger.info(f"   Minute: {match_stats.minute}")
            self.logger.info(f"   Corners: {match_stats.total_corners}")

            # Use COMBINED match-level decision and best team context
            combined = result.get('combined', {})
            if not combined or not combined.get('alert'):
                self.logger.info("\n❌ NO ALERT - Combined decision:")
                for reason in combined.get('reasons', []):
                    self.logger.info(f"   • {reason}")
                # Update previous stats for momentum tracking on next cycle
                self.previous_stats[fixture_id] = copy.deepcopy(current_stats)
                return None

            best_team = combined.get('best_team', 'home')
            team_result = result[best_team]

            # If we get here, the alert is triggered
            self.logger.info("\n✅ ALERT TRIGGERED!")
            
            # Get the full probability calculation
            probabilities = corner_system.calculate_corner_probability(current_stats, previous_stats, 5)
            
            # Extract metrics and patterns
            metrics = team_result['metrics']
            momentum_indicators = {
                'attack_intensity': metrics.get('attack_intensity', 0),
                'shot_efficiency': metrics.get('shot_efficiency', 0),
                'attack_volume': metrics.get('attack_volume', 0),
                'corner_momentum': metrics.get('corner_momentum', 0),
                'score_context': metrics.get('score_context', 0)
            }
            
            # Log the metrics
            self.logger.info("\n📈 ALERT METRICS:")
            self.logger.info(f"   • Combined Probability: {combined.get('probability', 0.0):.1f}%")
            self.logger.info(f"   • Team Probability ({best_team}): {metrics['total_probability']:.1f}%")
            self.logger.info(f"   • Attack Intensity: {metrics['attack_intensity']:.1f}%")
            self.logger.info(f"   • Corner Momentum: {metrics['corner_momentum']:.1f}%")
            
            # Get patterns
            detected_patterns = probabilities[best_team].get('detected_patterns', [])
            if detected_patterns:
                self.logger.info("\n🎯 DETECTED PATTERNS:")
                for pattern in detected_patterns:
                    self.logger.info(f"   • {pattern['name']} (Weight: {pattern['weight']})")

            # Prepare alert info
            alert_info = {
                'fixture_id': fixture_id,
                'home_team': match_stats.home_team,
                'away_team': match_stats.away_team,
                'home_score': match_stats.home_score,
                'away_score': match_stats.away_score,
                'minute': match_stats.minute,
                'total_corners': match_stats.total_corners,
                'tier': "TIER_1",
                # Store combined probability as the alert score
                'total_probability': combined.get('probability', metrics['total_probability']),
                'best_team': best_team,
                'team_probability': metrics['total_probability'],
                'momentum_indicators': momentum_indicators,
                'detected_patterns': detected_patterns,
                'odds_count': corner_odds.get('count', 0),
                'active_odds_count': corner_odds.get('active_count', 0),
                'odds_details': corner_odds.get('odds_details', []),
                'active_odds': corner_odds.get('active_odds', [])
            }

            # SAVE ALERT TO DATABASE FIRST
            self.logger.info(f"💾 SAVING ALERT TO DATABASE for TIER_1 match {fixture_id}...")
            
            try:
                # Save alert with new system metrics
                track_success = track_elite_alert(
                    alert_info=alert_info,
                    tier="TIER_1",
                    score=alert_info['total_probability'],
                    conditions=[p['name'] for p in detected_patterns],
                    momentum_indicators=momentum_indicators,
                    detected_patterns=detected_patterns
                )
                
                if track_success:
                    self.logger.info(f"✅ ALERT SAVED TO DATABASE")
                    self.logger.info("   Metrics saved:")
                    self.logger.info(f"   • Combined Probability: {alert_info['total_probability']:.1f}%")
                    self.logger.info(f"   • Attack Quality: {momentum_indicators['attack_intensity']:.1f}%")
                    self.logger.info(f"   • Corner Momentum: {momentum_indicators['corner_momentum']:.1f}%")
                    self.logger.info(f"   • Score Context: {momentum_indicators['score_context']:.1f}%")
                    self.logger.info(f"   • Patterns: {len(detected_patterns)}")
                    for pattern in detected_patterns:
                        self.logger.info(f"     - {pattern['name']} (Weight: {pattern['weight']})")
                else:
                    self.logger.error(f"❌ DATABASE SAVE FAILED: Alert not saved to database")
            except Exception as e:
                self.logger.error(f"❌ DATABASE SAVE ERROR: {e}")
                import traceback
                self.logger.error(traceback.format_exc())

            # THEN ATTEMPT TO SEND TELEGRAM ALERT
            self.logger.info(f"📱 SENDING TELEGRAM ALERT for TIER_1 match {fixture_id}...")
            
            try:
                telegram_success = send_corner_alert_new(
                    match_data=alert_info,
                    tier="TIER_1",
                    score=alert_info['total_probability'],
                    conditions=[p['name'] for p in detected_patterns]
                )
                
                if telegram_success:
                    self.alerted_matches.add(fixture_id)
                    self.logger.info(f"🎉 TELEGRAM ALERT SENT SUCCESSFULLY")
                    self.logger.info(f"   ✅ Match added to alerted list")
                else:
                    self.logger.error(f"❌ TELEGRAM ALERT FAILED")
                    self.logger.error(f"   ❌ Check Telegram configuration and network")
                    self.logger.error(f"   ❌ Alert will be retried next cycle")
            except Exception as e:
                self.logger.error(f"❌ TELEGRAM SEND ERROR: {e}")
                import traceback
                self.logger.error(traceback.format_exc())

            # Update previous stats at END of processing
            self.previous_stats[fixture_id] = copy.deepcopy(current_stats)

            return alert_info
            
        except Exception as e:
            self.logger.error(f"❌ Error monitoring match {fixture_id}: {e}")
            # Attempt to update previous stats on error as well
            try:
                self.previous_stats[fixture_id] = current_stats
            except Exception:
                pass
            return None

    def _parse_match_data_from_shared(self, match_data):
        """Parse match data from shared dashboard format into MatchStats"""
        try:
            # Use the SportMonks client to parse the live match data
            from sportmonks_client import SportmonksClient
            client = SportmonksClient()
            match_stats = client._parse_live_match_data(match_data)
            
            # Fix total_corners calculation from raw statistics data
            if match_stats and hasattr(match_stats, 'statistics'):
                home_corners = 0
                away_corners = 0
                
                # Look for type_id 34 (corners) in statistics
                for stat in match_stats.statistics:
                    if stat.get('type_id') == 34:  # Corners
                        value = stat.get('data', {}).get('value', 0)
                        location = stat.get('location', '')
                        
                        if location == 'home':
                            home_corners = value
                        elif location == 'away':
                            away_corners = value
                
                # Update total_corners with correct calculation
                match_stats.total_corners = home_corners + away_corners
                
                self.logger.debug(f"🧪 CORNER FIX: Match {match_stats.fixture_id} - Home: {home_corners}, Away: {away_corners}, Total: {match_stats.total_corners}")
            
            return match_stats
        except Exception as e:
            self.logger.error(f"❌ Error parsing shared match data: {e}")
            return None

    async def _get_corner_odds(self, fixture_id: int) -> Optional[Dict]:
        """Get corner odds directly from SportMonks"""
        try:
            self.logger.info(f"🔍 Fetching corner odds for match {fixture_id}")
            
            # Import the odds checking function
            from web_dashboard import check_corner_odds_available
            
            # Get fresh odds
            odds_data = check_corner_odds_available(fixture_id)
            
            if odds_data and odds_data.get('available', False):
                total_count = odds_data.get('count', 0)
                active_count = odds_data.get('active_count', 0)
                suspended_count = total_count - active_count
                
                self.logger.info(f"✅ LIVE ODDS: {total_count} bet365 Asian corner markets found!")
                self.logger.info(f"   🟢 ACTIVE (bettable): {active_count} markets")
                self.logger.info(f"   🔶 SUSPENDED: {suspended_count} markets")
                
                # Show active odds
                if 'active_odds' in odds_data and odds_data['active_odds']:
                    self.logger.info(f"   💎 ACTIVE ODDS (bettable now):")
                    for odds_str in odds_data['active_odds']:
                        self.logger.info(f"      • {odds_str}")
                
                return odds_data
            else:
                self.logger.warning(f"❌ NO ODDS: No corner odds available for match {fixture_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error getting corner odds for match {fixture_id}: {e}")
            return None

    async def start_monitoring(self):
        """Start the main monitoring loop using shared dashboard data"""
        self.logger.info("🚀 STARTING Late Corner Monitor with SHARED DATA architecture...")
        
        # Wait a moment for dashboard to initialize
        await asyncio.sleep(5)
        
        try:
            # Send startup message if it's the first deployment
            if is_first_startup():
                startup_message = (
                    "🚀 <b>Late Corner Monitor Started!</b>\n\n"
                    "📊 <b>System Status:</b>\n"
                    "✅ Shared data architecture active\n"
                    "✅ SportMonks API connected via dashboard\n"
                    "✅ Telegram bot ready\n"
                    "✅ New corner prediction system loaded\n\n"
                    "🎯 <b>Alert Criteria:</b>\n"
                    "• High total probability (>80%)\n"
                    "• Strong attack intensity (>65%)\n"
                    "• Multiple strong patterns\n"
                    "• Good corner momentum\n"
                    "• Exact 85-89 minute timing\n"
                    "• Live corner odds available\n\n"
                    "💰 Ready to catch profitable corner opportunities!"
                )
                
                try:
                    send_system_message_new(startup_message)
                    mark_startup()
                    self.logger.info("📱 SUCCESS: Startup message sent")
                except Exception as e:
                    self.logger.error(f"❌ Failed to send startup message: {e}")
            
            self.logger.info("🎯 SUCCESS: All systems ready. Starting match monitoring...")
            
            # Main monitoring loop
            while True:
                try:
                    # Discover new matches periodically
                    if self.match_discovery_counter % (self.config.MATCH_DISCOVERY_INTERVAL // self.config.LIVE_POLL_INTERVAL) == 0:
                        await self._discover_new_matches()
                    
                    # Monitor all current matches using shared data
                    shared_live_matches = self._get_shared_live_matches()
                    
                    if shared_live_matches:
                        self.logger.info(f"🔍 MONITORING: Processing {len(shared_live_matches)} live matches")
                        
                        for match in shared_live_matches:
                            try:
                                match_id = match.get('id')
                                if match_id and match_id in self.monitored_matches:
                                    # Monitor this match for alert conditions
                                    await self._monitor_single_match(match)
                            except Exception as e:
                                self.logger.error(f"❌ Error processing match {match.get('id', 'unknown')}: {e}")
                                continue
                    else:
                        self.logger.info("📊 No live matches available from shared data source")
                    
                    self.match_discovery_counter += 1
                    self.result_check_counter += 1
                    
                    # HOURLY RESULT CHECKING
                    if self.result_check_counter >= 120:  
                        self.logger.info("🔍 HOURLY CHECK: Checking pending alert results...")
                        try:
                            await check_pending_results()
                            self.logger.info("✅ HOURLY CHECK: Result checking completed")
                        except Exception as e:
                            self.logger.error(f"❌ HOURLY CHECK: Error checking results: {e}")
                        finally:
                            self.result_check_counter = 0  # Reset counter
                    
                    # Wait before next cycle
                    await asyncio.sleep(self.config.LIVE_POLL_INTERVAL)
                    
                except Exception as e:
                    self.logger.error(f"❌ Error in monitoring loop: {e}")
                    await asyncio.sleep(30)  # Wait longer on error
                    
        except Exception as e:
            self.logger.error(f"❌ Fatal error in monitoring: {e}")
            raise

async def main():
    """Main entry point"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🚀 STARTING Late Corner Monitor with SHARED DATA...")
        
        # Initialize and start the monitor
        monitor = LateCornerMonitor()
        await monitor.start_monitoring()
        
    except KeyboardInterrupt:
        logger.info("👋 Shutting down gracefully...")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())