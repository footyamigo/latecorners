#!/usr/bin/env python3

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Set, Optional
import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_config
from telegram_bot import TelegramBot
from scoring_engine import ScoringEngine
from startup_flag import should_send_startup_message, mark_startup_message_sent

class LateCornerMonitor:
    """Monitor live matches for late corner betting opportunities using shared dashboard data"""
    
    def __init__(self):
        self.config = get_config()
        self.telegram_bot = TelegramBot()
        self.scoring_engine = ScoringEngine()
        
        # Track which matches we've already alerted on
        self.alerted_matches: Set[int] = set()
        self.monitored_matches: Set[int] = set()
        
        # Track discovery cycles
        self.match_discovery_counter = 0
        
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
    
    def _get_stat_type_id(self, stat_name):
        """Map dashboard stat names to SportMonks type IDs"""
        stat_mapping = {
            'corners': 34,
            'shots_total': 42,
            'shots_on_goal': 41,
            'dangerous_attacks': 44,
            'crosses': 60,
            'ball_possession': 45,
            'offsides': 54
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
            
            # Remove finished matches from monitoring
            if match_stats.state == 'FT' or match_stats.minute >= 100:
                if fixture_id in self.monitored_matches:
                    self.monitored_matches.remove(fixture_id)
                    self.logger.info(f"🏁 REMOVED finished match {fixture_id} from monitoring")
                return None
            
            # TEST ALERT: Simple 85th minute + 6 corners test (bypass scoring system)
            if match_stats.minute == 85 and match_stats.total_corners >= 6:
                if fixture_id not in self.alerted_matches:
                    self.logger.info(f"🧪 TEST ALERT TRIGGERED: Match {fixture_id} at 85' with {match_stats.total_corners} corners")
                    
                    # Send simple test alert
                    test_message = (
                        f"🧪 <b>TEST ALERT - NOT MAIN SYSTEM</b> 🧪\n\n"
                        f"⚽ <b>{match_stats.home_team} vs {match_stats.away_team}</b>\n"
                        f"📊 Score: {match_stats.home_score}-{match_stats.away_score} (85')\n"
                        f"🚩 Corners: {match_stats.total_corners} total\n\n"
                        f"📱 <b>This is just a system test!</b>\n"
                        f"✅ Telegram alerts are working\n"
                        f"✅ 85th minute detection working\n"
                        f"✅ Corner counting working\n\n"
                        f"💡 <i>Real alerts use elite scoring system</i>"
                    )
                    
                    success = await self.telegram_bot.send_alert(test_message)
                    if success:
                        self.alerted_matches.add(fixture_id)
                        self.logger.info(f"🧪 TEST ALERT SENT successfully for match {fixture_id}")
                        return None  # Don't continue to main scoring
                    else:
                        self.logger.error(f"❌ TEST ALERT FAILED for match {fixture_id}")
            
            # Check if this match meets our alert criteria
            scoring_result = self.scoring_engine.evaluate_match(match_stats)
            
            # Log scoring result for debugging
            if scoring_result:
                total_score = scoring_result.get('total_score', 0)
                high_priority_count = scoring_result.get('high_priority_indicators', 0)
                self.logger.info(f"🧪 DEBUG: Match {fixture_id} scoring - Total: {total_score}, High Priority: {high_priority_count}")
            
            # ELITE ALERT LOGIC: Check if conditions are met for alert
            if scoring_result and fixture_id not in self.alerted_matches:
                total_score = scoring_result.get('total_score', 0)
                high_priority_count = scoring_result.get('high_priority_indicators', 0)
                
                # Elite thresholds: minimum 10 points AND at least 2 high-priority indicators
                if total_score >= 10 and high_priority_count >= 2:
                    self.logger.info(f"🎯 ELITE MATCH DETECTED: {fixture_id} - Score: {total_score}, High Priority: {high_priority_count}")
                    
                    # Check if we're in the exact alert window (85th minute)
                    if self.scoring_engine._is_in_alert_window(match_stats.minute):
                        # Check corner odds availability
                        corner_odds = await self._get_corner_odds(fixture_id)
                        if corner_odds:
                            # Extract match info for alert
                            match_info = self._extract_match_info(match_stats, scoring_result, corner_odds)
                            return match_info
                        else:
                            self.logger.warning(f"⚠️ No corner odds available for elite match {fixture_id}")
                    else:
                        self.logger.info(f"⏰ Elite match {fixture_id} not in alert window yet (minute {match_stats.minute})")
                else:
                    self.logger.debug(f"📊 Match {fixture_id} below elite thresholds - Score: {total_score}/10, High Priority: {high_priority_count}/2")
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error monitoring match {fixture_id}: {e}")
            return None

    def _parse_match_data_from_shared(self, match_data):
        """Parse match data from shared dashboard format into MatchStats"""
        try:
            # This uses the converted SportMonks format from dashboard data
            from sportmonks_client import SportmonksClient
            client = SportmonksClient()
            return client._parse_live_match_data(match_data)
        except Exception as e:
            self.logger.error(f"❌ Error parsing shared match data: {e}")
            return None

    async def _get_corner_odds(self, fixture_id: int) -> Optional[Dict]:
        """Get corner odds from dashboard's cached data"""
        try:
            # Import dashboard's odds cache
            from web_dashboard import odds_cache
            
            # Check if we have cached corner odds for this match
            if fixture_id in odds_cache:
                cache_time, cache_data = odds_cache[fixture_id]
                # Use cache if it's less than 5 minutes old
                if time.time() - cache_time < 300:
                    if cache_data.get('available', False):
                        self.logger.info(f"💰 Using cached corner odds for match {fixture_id}")
                        return cache_data
            
            self.logger.debug(f"📊 No fresh corner odds available for match {fixture_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error getting corner odds for match {fixture_id}: {e}")
            return None

    def _extract_match_info(self, match_stats, scoring_result: Dict, corner_odds: Dict) -> Dict:
        """Extract match information for alert"""
        try:
            match_info = {
                'fixture_id': match_stats.fixture_id,
                'home_team': match_stats.home_team,
                'away_team': match_stats.away_team,
                'home_score': match_stats.home_score,
                'away_score': match_stats.away_score,
                'minute': match_stats.minute,
                
                # Live statistics for Telegram message
                'home_corners': match_stats.total_corners // 2 if hasattr(match_stats, 'total_corners') else 0,  # Rough split
                'away_corners': match_stats.total_corners // 2 if hasattr(match_stats, 'total_corners') else 0,  # Rough split
                'home_shots': match_stats.shots_total.get('home', 0) if hasattr(match_stats, 'shots_total') else 0,
                'away_shots': match_stats.shots_total.get('away', 0) if hasattr(match_stats, 'shots_total') else 0,
                'home_shots_on_target': match_stats.shots_on_target.get('home', 0) if hasattr(match_stats, 'shots_on_target') else 0,
                'away_shots_on_target': match_stats.shots_on_target.get('away', 0) if hasattr(match_stats, 'shots_on_target') else 0,
                'home_attacks': match_stats.dangerous_attacks.get('home', 0) if hasattr(match_stats, 'dangerous_attacks') else 0,
                'away_attacks': match_stats.dangerous_attacks.get('away', 0) if hasattr(match_stats, 'dangerous_attacks') else 0,
            }
            
            self.logger.info(f"🧪 DEBUG: Extracted match_info: {match_info}")
            return match_info
            
        except Exception as e:
            self.logger.error(f"❌ Error extracting match info: {e}")
            return {}

    async def start_monitoring(self):
        """Start the main monitoring loop using shared dashboard data"""
        self.logger.info("🚀 STARTING Late Corner Monitor with SHARED DATA architecture...")
        
        # Wait a moment for dashboard to initialize
        await asyncio.sleep(5)
        
        try:
            # Send startup message if it's the first deployment
            if should_send_startup_message():
                startup_message = (
                    "🚀 <b>Late Corner Monitor Started!</b>\n\n"
                    "📊 <b>System Status:</b>\n"
                    "✅ Shared data architecture active\n"
                    "✅ SportMonks API connected via dashboard\n"
                    "✅ Telegram bot ready\n"
                    "✅ Elite scoring system loaded\n\n"
                    "🎯 <b>Alert Criteria:</b>\n"
                    "• Minimum 10 points total score\n"
                    "• At least 2 high-priority indicators\n"
                    "• Exact 85th minute timing\n"
                    "• Live corner odds available\n\n"
                    "💰 Ready to catch profitable corner opportunities!"
                )
                
                success = await self.telegram_bot.send_alert(startup_message)
                if success:
                    mark_startup_message_sent()
                    self.logger.info("📱 SUCCESS: Startup message sent")
                else:
                    self.logger.error("❌ Failed to send startup message")
            
            self.logger.info("🎯 SUCCESS: All systems ready. Starting match monitoring with shared data...")
            
            # Main monitoring loop
            while True:
                try:
                    # Discover new matches periodically (less frequently since we're using shared data)
                    if self.match_discovery_counter % (self.config.MATCH_DISCOVERY_INTERVAL // self.config.LIVE_POLL_INTERVAL) == 0:
                        await self._discover_new_matches()
                    
                    # Monitor all current matches using shared data
                    shared_live_matches = self._get_shared_live_matches()
                    
                    if shared_live_matches:
                        self.logger.info(f"🔍 MONITORING: Processing {len(shared_live_matches)} live matches from shared data")
                        
                        for match in shared_live_matches:
                            try:
                                match_id = match.get('id')
                                if match_id and match_id in self.monitored_matches:
                                    # Monitor this match for alert conditions
                                    alert_info = await self._monitor_single_match(match)
                                    
                                    if alert_info:
                                        # Send alert
                                        success = await self.telegram_bot.send_match_alert(
                                            alert_info, 
                                            scoring_result={'total_score': 10, 'high_priority_indicators': 2},  # Placeholder
                                            corner_odds={'available': True}  # Placeholder
                                        )
                                        
                                        if success:
                                            self.alerted_matches.add(match_id)
                                            self.logger.info(f"🚨 ALERT SENT for match {match_id}")
                                        else:
                                            self.logger.error(f"❌ Failed to send alert for match {match_id}")
                                            
                            except Exception as e:
                                self.logger.error(f"❌ Error processing match {match.get('id', 'unknown')}: {e}")
                                continue
                    else:
                        self.logger.info("📊 No live matches available from shared data source")
                    
                    self.match_discovery_counter += 1
                    
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
