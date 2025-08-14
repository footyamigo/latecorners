#!/usr/bin/env python3

import asyncio
import copy
import logging
import time
from datetime import datetime
from typing import Dict, Set, Optional
import sys
import os
import json

# Ensure DATABASE_URL is set for production deployment
if 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = 'postgresql://postgres:jIwhlnuBmXDEiHjndVZzCmxNEkpquJAL@trolley.proxy.rlwy.net:24044/railway'

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_config
from new_telegram_system import send_corner_alert_new, send_system_message_new
from alert_tracker import track_elite_alert # Using the original tracker
from result_checker import check_pending_results
from startup_flag import is_first_startup, mark_startup
# Corner prediction systems
from first_half_system import FirstHalfCornerSystem
from reliable_corner_system import ReliableCornerSystem
from momentum_tracker import MomentumTracker


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
        # Momentum tracker (10-minute window)
        self.momentum_tracker = MomentumTracker(window_minutes=10)
        
        # Corner prediction systems
        self.first_half_system = FirstHalfCornerSystem()  # For 30-35 minute alerts
        self.reliable_system = ReliableCornerSystem()     # For 85-89 minute alerts
        
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
            from web_dashboard import live_matches_data
            source_matches = list(live_matches_data) if live_matches_data else []
        except (ImportError, Exception):
             source_matches = []

        if not source_matches:
            self.logger.info("Using API fallback for live matches (dashboard buffer empty or failed)")
            try:
                from sportmonks_client import SportmonksClient
                api_client = SportmonksClient()
                api_matches = api_client.get_live_matches(filter_by_minute=False) or []
                self.logger.info(f"API fallback returned {len(api_matches)} live matches")
                return api_matches
            except Exception as e:
                self.logger.error(f"API fallback failed: {e}")
                return []

        # Convert dashboard format to SportMonks-compatible format
        matches = []
        for dashboard_match in source_matches:
            converted_match = self._convert_dashboard_to_sportmonks_format(dashboard_match)
            if converted_match:
                matches.append(converted_match)
        
        self.logger.info(f"Dashboard buffer returned {len(matches)} live matches")
        return matches

    def _convert_dashboard_to_sportmonks_format(self, dashboard_match):
        """Convert dashboard match format to SportMonks format for compatibility"""
        try:
            return {
                'id': dashboard_match.get('match_id'),
                'participants': [
                    {'name': dashboard_match.get('home_team', 'Unknown'), 'meta': {'location': 'home'}},
                    {'name': dashboard_match.get('away_team', 'Unknown'), 'meta': {'location': 'away'}}
                ],
                'scores': [
                    {'description': 'CURRENT', 'score': {'goals': dashboard_match.get('home_score', 0), 'participant': 'home'}},
                    {'description': 'CURRENT', 'score': {'goals': dashboard_match.get('away_score', 0), 'participant': 'away'}}
                ],
                'periods': [{'ticking': True, 'minutes': dashboard_match.get('minute', 0)}],
                'state': {'developer_name': dashboard_match.get('state', 'UNKNOWN')},
                'statistics': self._convert_dashboard_stats_to_sportmonks(dashboard_match.get('statistics', {}))
            }
        except Exception as e:
            self.logger.error(f"❌ Error converting dashboard match {dashboard_match.get('match_id', 'unknown')}: {e}")
            return None
    
    def _convert_dashboard_stats_to_sportmonks(self, dashboard_stats):
        """Convert dashboard statistics format to SportMonks format"""
        statistics = []
        stat_mapping = {
            'corners': 33, 'possession': 45, 'shots_off_target': 41, 'shots_total': 42,
            'dangerous_attacks': 44, 'attacks': 43, 'shots_on_target': 86
        }
        for location in ['home', 'away']:
            for stat_name, value in dashboard_stats.get(location, {}).items():
                stat_id = stat_mapping.get(stat_name)
                if stat_id:
                    statistics.append({'type_id': stat_id, 'data': {'value': value}, 'location': location})
        return statistics
    
    async def _discover_new_matches(self):
        """Discover new live matches using shared dashboard data"""
        try:
            self.logger.info("🔍 DISCOVERING new live matches...")
            live_matches = self._get_shared_live_matches()
            
            if not live_matches:
                self.logger.warning("⚠️ No live matches from shared data source")
                return
            
            self.logger.info(f"📊 Found {len(live_matches)} live matches from shared data")
            
            for match in live_matches:
                match_id = match.get('id')
                state = match.get('state', {}).get('developer_name', 'unknown')
                minute = next((p.get('minutes', 0) for p in match.get('periods', []) if p.get('ticking')), 0)

                if match_id and state in ['INPLAY_1ST_HALF', 'INPLAY_2ND_HALF'] and minute >= 20:
                    if match_id not in self.monitored_matches:
                        self.monitored_matches.add(match_id)
                        self.logger.info(f"➕ ADDED match {match_id} to monitoring (Minute: {minute}, State: {state})")
        
        except Exception as e:
            self.logger.error(f"❌ Error in match discovery: {e}")

    async def _monitor_single_match(self, match_data: Dict) -> Optional[Dict]:
        """Central hub to monitor a single match and delegate to the correct system."""
        fixture_id = match_data.get('id')
        if not fixture_id:
            return None
        
        from sportmonks_client import SportmonksClient
        client = SportmonksClient()
        match_stats = client._parse_live_match_data(match_data)
        
        if not match_stats:
            return None
        
        self.logger.info(f"--- Processing Match: {fixture_id} ({match_stats.home_team} vs {match_stats.away_team}) at {match_stats.minute}' ---")

        current_stats = self._extract_current_stats(match_stats)
        
        # Always update momentum tracker
        self.momentum_tracker.add_snapshot(fixture_id, match_stats.minute, current_stats.get('home_stats',{}), current_stats.get('away_stats',{}))

        # Delegate to the correct handler based on timing
        is_first_half = match_stats.state in ['INPLAY_1ST_HALF', 'FIRST_HALF']
        
        alert_info = None
        if is_first_half and 30 <= match_stats.minute <= 35:
            alert_info = await self._handle_first_half_alert(fixture_id, match_stats, current_stats)
        elif not is_first_half and 85 <= match_stats.minute <= 89:
            alert_info = await self._handle_late_game_alert(fixture_id, match_stats, current_stats)
        
        # CRITICAL: Update previous_stats for the *next* cycle's momentum calculation
        self.previous_stats[fixture_id] = copy.deepcopy(current_stats)
        
        return alert_info

    def _extract_current_stats(self, match_stats) -> Dict:
        """Extracts a standardized dictionary of stats from the MatchStats object."""
        return {
            'minute': match_stats.minute,
            'total_corners': match_stats.total_corners,
            'home_score': match_stats.home_score,
            'away_score': match_stats.away_score,
            'score_diff': match_stats.home_score - match_stats.away_score,
            'attacks': match_stats.attacks or {},
            'dangerous_attacks': match_stats.dangerous_attacks or {},
            'shots_total': match_stats.shots_total or {},
            'shots_on_target': match_stats.shots_on_target or {},
            'shots_off_target': match_stats.shots_off_target or {},
            'possession': match_stats.possession or {},
            'home_stats': {
                'attacks': match_stats.attacks.get('home', 0),
                'dangerous_attacks': match_stats.dangerous_attacks.get('home', 0),
                'shots_total': match_stats.shots_total.get('home', 0),
                'shots_on_target': match_stats.shots_on_target.get('home', 0),
                'shots_off_target': match_stats.shots_off_target.get('home', 0),
                'possession': match_stats.possession.get('home', 0)
            },
            'away_stats': {
                'attacks': match_stats.attacks.get('away', 0),
                'dangerous_attacks': match_stats.dangerous_attacks.get('away', 0),
                'shots_total': match_stats.shots_total.get('away', 0),
                'shots_on_target': match_stats.shots_on_target.get('away', 0),
                'shots_off_target': match_stats.shots_off_target.get('away', 0),
                'possession': match_stats.possession.get('away', 0)
            }
        }

    async def _handle_first_half_alert(self, fixture_id: int, match_stats, current_stats: Dict) -> Optional[Dict]:
        """Handles alert logic for the first half window (30-35 mins)."""
        self.logger.info(f"-> Evaluating FIRST HALF logic for {fixture_id} at {match_stats.minute}'")

        if fixture_id in self.alerted_matches:
            self.logger.info(f"⏭️ Already alerted for {fixture_id}.")
            return None

        corner_odds = await self._get_corner_odds(fixture_id, is_first_half=True)
        if not corner_odds or not corner_odds.get('available'):
            self.logger.warning(f"🚫 No ACTIVE first-half odds for {fixture_id}.")
            return None
            
        previous_stats = self.previous_stats.get(fixture_id)
        if not previous_stats:
            self.logger.info("⏳ First snapshot for this match, need one more for momentum.")
            return None

        minutes_passed = max(1, current_stats['minute'] - previous_stats.get('minute', current_stats['minute'] - 1))
        
        result = self.first_half_system.should_alert(current_stats, previous_stats, minutes_passed)
        
        if result.get('alert'):
            self.logger.info(f"🎉 *** FIRST HALF ALERT for {fixture_id}! ***")
            alert_data = self._prepare_alert_data(match_stats, 'FIRST_HALF_CORNER', result, corner_odds)
            
            if track_elite_alert(alert_data):
                self.logger.info(f"✅ DB save success for {fixture_id}.")
                send_corner_alert_new(match_info=alert_data, corner_odds=corner_odds, tier='FIRST_HALF_CORNER')
                self.alerted_matches.add(fixture_id)
                return alert_data
        else:
            self.logger.info(f"❌ No FH alert for {fixture_id}. Reasons: {result.get('reasons')}")
        
        return None

    async def _handle_late_game_alert(self, fixture_id: int, match_stats, current_stats: Dict) -> Optional[Dict]:
        """Handles alert logic for the late game window (85-89 mins)."""
        self.logger.info(f"-> Evaluating LATE GAME logic for {fixture_id} at {match_stats.minute}'")

        if fixture_id in self.alerted_matches:
            self.logger.info(f"⏭️ Already alerted for {fixture_id}.")
            return None

        corner_odds = await self._get_corner_odds(fixture_id, is_first_half=False)
        if not corner_odds or not corner_odds.get('available'):
            self.logger.warning(f"🚫 No ACTIVE late-game odds for {fixture_id}.")
            return None

        previous_stats = self.previous_stats.get(fixture_id)
        if not previous_stats:
            self.logger.info("⏳ First snapshot for this match, need one more for momentum.")
            return None
            
        minutes_passed = max(1, current_stats['minute'] - previous_stats.get('minute', current_stats['minute'] - 1))

        result = self.reliable_system.should_alert(current_stats, previous_stats, minutes_passed)

        if result.get('alert'):
            self.logger.info(f"🎉 *** LATE GAME ALERT for {fixture_id}! ***")
            alert_data = self._prepare_alert_data(match_stats, 'RELIABLE_SYSTEM', result, corner_odds)
            
            if track_elite_alert(
                match_data=alert_data,
                tier='RELIABLE_SYSTEM',
                score=result.get('total_probability', 0),
                conditions=[p['description'] for p in result.get('detected_patterns', [])],
                momentum_indicators=result.get('momentum_indicators', {}),
                detected_patterns=[p['name'] for p in result.get('detected_patterns', [])]
            ):
                self.logger.info(f"✅ DB save success for {fixture_id}.")
                send_corner_alert_new(match_info=alert_data, tier='RELIABLE_SYSTEM', score=result.get('total_probability',0), conditions=[p['description'] for p in result.get('detected_patterns', [])])
                self.alerted_matches.add(fixture_id)
                return alert_data
            else:
                self.logger.info(f"❌ No LG alert for {fixture_id}. System criteria not met.")
                
            return None

    def _prepare_alert_data(self, match_stats, tier: str, result: Dict, corner_odds: Dict) -> Dict:
        """Prepares a consistent data dictionary for database tracking and Telegram."""
        return {
            'fixture_id': match_stats.fixture_id,
            'home_team': match_stats.home_team,
            'away_team': match_stats.away_team,
            'home_score': match_stats.home_score,
            'away_score': match_stats.away_score,
            'minute': match_stats.minute,
            'total_corners': match_stats.total_corners,
            'alert_type': tier,
            'tier': tier,
            **result,
            **corner_odds
        }
            
    async def _get_corner_odds(self, fixture_id: int, is_first_half: bool = False) -> Optional[Dict]:
        """Get corner odds from the dashboard, specifying the match half."""
        try:
            from web_dashboard import check_corner_odds_available
            log_prefix = "FIRST HALF" if is_first_half else "LATE GAME"
            self.logger.info(f"🔍 Fetching {log_prefix} odds for match {fixture_id}")
            
            odds_data = check_corner_odds_available(fixture_id, is_first_half=is_first_half)
            
            if odds_data and odds_data.get('available'):
                self.logger.info(f"✅ Found {odds_data.get('active_count')} active Asian corner markets for {fixture_id}.")
                return odds_data
            else:
                self.logger.warning(f"❌ No active odds found for {fixture_id} for {log_prefix}.")
                return None
        except Exception as e:
            self.logger.error(f"❌ Error getting odds for {fixture_id}: {e}")
            return None

    async def start_monitoring(self):
        """Start the main monitoring loop using shared dashboard data"""
        self.logger.info("🚀 STARTING Late Corner Monitor...")
        
        # Send startup message if it's the first deployment
        if is_first_startup():
            startup_message = (
                "🚀 <b>Late Corner Monitor Started!</b>\n\n"
                "📊 <b>System Status:</b>\n"
                "✅ Logic refactored for stability\n"
                "✅ First-Half & Late-Game systems active\n"
                "✅ Odds markets correctly identified\n\n"
                "🎯 Now monitoring for all corner opportunities."
            )
            try:
                send_system_message_new(startup_message)
                mark_startup()
                self.logger.info("📱 SUCCESS: Startup message sent")
            except Exception as e:
                self.logger.error(f"❌ Failed to send startup message: {e}")

        await asyncio.sleep(5)
            
        # Main monitoring loop
        while True:
            try:
            # Discover new matches periodically
                if self.match_discovery_counter % (self.config.MATCH_DISCOVERY_INTERVAL // self.config.LIVE_POLL_INTERVAL) == 0:
                    await self._discover_new_matches()
                
                # Monitor all current matches using shared data
                shared_live_matches = self._get_shared_live_matches()
                
                if shared_live_matches:
                    self.logger.info(f"🔍 Processing {len(shared_live_matches)} live matches...")
                    for match in shared_live_matches:
                        await self._monitor_single_match(match)
                else:
                    self.logger.info("...No live matches found...")
                
                self.match_discovery_counter += 1
            
                await asyncio.sleep(self.config.LIVE_POLL_INTERVAL)
                
            except Exception as e:
                self.logger.error(f"❌ Error in main loop: {e}", exc_info=True)
                await asyncio.sleep(30)

async def main():
    """Main entry point"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    try:
        monitor = LateCornerMonitor()
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        logger.info("👋 Shutting down gracefully...")
    except Exception as e:
        logger.error(f"❌ FATAL ERROR: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main()) 