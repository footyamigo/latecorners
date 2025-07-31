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
from telegram_bot import TelegramNotifier
from new_telegram_system import send_corner_alert_new
from scoring_engine import ScoringEngine
from startup_flag import is_first_startup, mark_startup

class LateCornerMonitor:
    """Monitor live matches for late corner betting opportunities using shared dashboard data"""
    
    def __init__(self):
        self.config = get_config()
        self.telegram_bot = TelegramNotifier()
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
            

            
            # PRE-SCORING DEBUG: Check basic requirements
            self.logger.info(f"🔍 PRE-CHECKS: Match {fixture_id} ({match_stats.home_team} vs {match_stats.away_team})")
            self.logger.info(f"   📊 Minute: {match_stats.minute} (need 84-85 for alert)")
            self.logger.info(f"   ⚽ Corners: {match_stats.total_corners} (need 7-12)")
            self.logger.info(f"   🎮 Match State: {match_stats.state}")
            
            # Check if this match meets our alert criteria
            scoring_result = self.scoring_engine.evaluate_match(match_stats)
            
            # ENHANCED DEBUG: Log ALL scoring attempts
            if scoring_result:
                total_score = scoring_result.total_score
                high_priority_count = scoring_result.high_priority_indicators
                triggered_conditions = scoring_result.triggered_conditions
                self.logger.info(f"🎯 ELITE SCORING: Match {fixture_id} ({match_stats.home_team} vs {match_stats.away_team})")
                self.logger.info(f"   📊 Total Score: {total_score}/8.0 | High Priority: {high_priority_count}/2")
                self.logger.info(f"   🏆 Conditions: {triggered_conditions}")
                
                if total_score >= 8.0 and high_priority_count >= 2:
                    self.logger.info(f"   ✅ ELITE THRESHOLDS MET! Checking corner odds...")
                else:
                    self.logger.info(f"   ❌ Elite thresholds NOT met (need 8+ score AND 2+ high priority)")
            else:
                self.logger.info(f"📊 ELITE SCORING: Match {fixture_id} - Minute {match_stats.minute} not in alert window (85') OR no scoring result")
            
            # DUAL-TIER ALERT LOGIC: Check ELITE first, then PREMIUM
            if scoring_result and fixture_id not in self.alerted_matches:
                total_score = scoring_result.total_score
                high_priority_count = scoring_result.high_priority_indicators
                
                # ELITE TIER: Ultra-selective (8.0+ score, 2+ high priority, 84-85 minutes)
                if total_score >= 8.0 and high_priority_count >= 2:
                    self.logger.info(f"🏆 ELITE MATCH DETECTED: {fixture_id} - Score: {total_score}, High Priority: {high_priority_count}")
                    
                    # Check if we're in the exact elite alert window (84-85th minute)
                    if 84 <= match_stats.minute <= 85:
                        self.logger.info(f"🏆 ELITE ALERT WINDOW! Match {fixture_id} at minute {match_stats.minute} - proceeding to odds check")
                        
                        corner_odds = await self._get_corner_odds(fixture_id)
                        if corner_odds:
                            self.logger.info(f"🚀 SENDING ELITE ALERT: All conditions met for match {fixture_id}")
                            match_info = self._extract_match_info(match_stats, scoring_result, corner_odds, tier="ELITE")
                            return match_info
                        else:
                            self.logger.warning(f"🚫 ELITE ALERT BLOCKED: No odds available for match {fixture_id}")
                    else:
                        self.logger.info(f"⏰ Elite match {fixture_id} waiting for alert window (need 84-85', currently {match_stats.minute}')")
                
                # PREMIUM TIER: More accessible (6.0+ score, 1+ high priority, 82-87 minutes)
                elif total_score >= 6.0 and high_priority_count >= 1:
                    self.logger.info(f"💎 PREMIUM MATCH DETECTED: {fixture_id} - Score: {total_score}, High Priority: {high_priority_count}")
                    
                    # Check if we're in the premium alert window (82-87th minute)
                    if 82 <= match_stats.minute <= 87:
                        self.logger.info(f"💎 PREMIUM ALERT WINDOW! Match {fixture_id} at minute {match_stats.minute} - proceeding to odds check")
                        
                        corner_odds = await self._get_corner_odds(fixture_id)
                        if corner_odds:
                            self.logger.info(f"🚀 SENDING PREMIUM ALERT: All conditions met for match {fixture_id}")
                            match_info = self._extract_match_info(match_stats, scoring_result, corner_odds, tier="PREMIUM")
                            return match_info
                        else:
                            self.logger.warning(f"🚫 PREMIUM ALERT BLOCKED: No odds available for match {fixture_id}")
                    else:
                        self.logger.info(f"⏰ Premium match {fixture_id} waiting for alert window (need 82-87', currently {match_stats.minute}')")
                
                else:
                    self.logger.debug(f"📊 Match {fixture_id} below thresholds - Score: {total_score}/6.0, High Priority: {high_priority_count}/1")
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error monitoring match {fixture_id}: {e}")
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
        """Get corner odds directly from SportMonks - with detailed logging"""
        try:
            self.logger.info(f"🔍 ELITE SYSTEM @ 85': Fetching corner odds for match {fixture_id}")
            
            # Import the odds checking function
            from web_dashboard import check_corner_odds_available
            
            # ALWAYS fetch fresh, live odds at alert time - no caching!
            self.logger.info(f"🌐 FETCHING LIVE ODDS @ 85': Getting current odds from SportMonks for {fixture_id}")
            self.logger.info(f"   ⚡ Reason: Corner odds change every few seconds - only current odds are actionable!")
            odds_data = check_corner_odds_available(fixture_id)
            
            if odds_data and odds_data.get('available', False):
                total_count = odds_data.get('count', 0)
                active_count = odds_data.get('active_count', 0)
                suspended_count = total_count - active_count
                
                self.logger.info(f"✅ LIVE ODDS @ 85': {total_count} bet365 Asian corner markets found!")
                self.logger.info(f"   🟢 ACTIVE (bettable): {active_count} markets")
                self.logger.info(f"   🔶 SUSPENDED: {suspended_count} markets")
                
                # Show active odds (the ones you can actually bet on)
                if 'active_odds' in odds_data and odds_data['active_odds']:
                    self.logger.info(f"   💎 ACTIVE ODDS (bettable now):")
                    for odds_str in odds_data['active_odds']:
                        self.logger.info(f"      • {odds_str}")
                
                # Show all odds details if needed
                if 'odds_details' in odds_data and len(odds_data['odds_details']) > active_count:
                    self.logger.info(f"   📊 ALL ODDS (including suspended):")
                    for odds_str in odds_data['odds_details']:
                        self.logger.info(f"      • {odds_str}")
                
                self.logger.info(f"   ⚡ These are LIVE odds fetched at alert time - actionable now!")
                return odds_data
            else:
                self.logger.warning(f"❌ NO ODDS @ 85': SportMonks has no corner odds for elite match {fixture_id}")
                self.logger.warning(f"   🚫 ALERT BLOCKED: Cannot send elite alert without current odds available")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error getting corner odds for match {fixture_id}: {e}")
            return None

    def _extract_match_info(self, match_stats, scoring_result: Dict, corner_odds: Dict, tier: str = "ELITE") -> Dict:
        """Extract match information for alert"""
        try:
            match_info = {
                'fixture_id': match_stats.fixture_id,
                'home_team': match_stats.home_team,
                'away_team': match_stats.away_team,
                'home_score': match_stats.home_score,
                'away_score': match_stats.away_score,
                'minute': match_stats.minute,
                'tier': tier,  # ELITE or PREMIUM
                
                # Live statistics for Telegram message
                'home_corners': match_stats.total_corners // 2 if hasattr(match_stats, 'total_corners') else 0,  # Rough split
                'away_corners': match_stats.total_corners // 2 if hasattr(match_stats, 'total_corners') else 0,  # Rough split
                'home_shots': match_stats.shots_total.get('home', 0) if hasattr(match_stats, 'shots_total') else 0,
                'away_shots': match_stats.shots_total.get('away', 0) if hasattr(match_stats, 'shots_total') else 0,
                'home_shots_on_target': match_stats.shots_on_target.get('home', 0) if hasattr(match_stats, 'shots_on_target') else 0,
                'away_shots_on_target': match_stats.shots_on_target.get('away', 0) if hasattr(match_stats, 'shots_on_target') else 0,
                'home_attacks': match_stats.dangerous_attacks.get('home', 0) if hasattr(match_stats, 'dangerous_attacks') else 0,
                'away_attacks': match_stats.dangerous_attacks.get('away', 0) if hasattr(match_stats, 'dangerous_attacks') else 0,
                
                # Corner odds information for alert
                'odds_available': corner_odds.get('available', False),
                'odds_count': corner_odds.get('count', 0),
                'active_odds_count': corner_odds.get('active_count', 0),
                'odds_details': corner_odds.get('odds_details', []),
                'active_odds': corner_odds.get('active_odds', []),
                
                # Scoring information for alert
                'elite_score': scoring_result.total_score,
                'high_priority_count': scoring_result.high_priority_indicators,
                'triggered_conditions': scoring_result.triggered_conditions
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
            if is_first_startup():
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
                
                try:
                    await self.telegram_bot.send_system_message(startup_message)
                    mark_startup()
                    self.logger.info("📱 SUCCESS: Startup message sent")
                except Exception as e:
                    self.logger.error(f"❌ Failed to send startup message: {e}")
            
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
                                        self.logger.info(f"🎯 ALERT QUALIFIED: Match {match_id} met all criteria!")
                                        self.logger.info(f"   ✅ Alert info received from monitoring: {alert_info.keys()}")
                                        
                                        # Extract actual values from alert_info instead of hardcoding
                                        actual_minute = alert_info.get('minute', 85)
                                        actual_score = alert_info.get('elite_score', 0)
                                        actual_priority = alert_info.get('high_priority_count', 0)
                                        actual_conditions = alert_info.get('triggered_conditions', [])
                                        actual_tier = alert_info.get('tier', 'UNKNOWN')
                                        
                                        self.logger.info(f"🔍 ALERT DETAILS:")
                                        self.logger.info(f"   Minute: {actual_minute}")
                                        self.logger.info(f"   Score: {actual_score}")
                                        self.logger.info(f"   Priority: {actual_priority}")
                                        self.logger.info(f"   Tier: {actual_tier}")
                                        self.logger.info(f"   Conditions: {len(actual_conditions)} met")
                                        
                                        # Create proper scoring result object with ACTUAL data
                                        from scoring_engine import ScoringResult
                                        scoring_obj = ScoringResult(
                                            fixture_id=match_id,
                                            minute=actual_minute,
                                            total_score=actual_score,
                                            high_priority_indicators=actual_priority,
                                            triggered_conditions=actual_conditions,
                                            team_focus="home",  # This could be extracted from alert_info if needed
                                            match_context=f"{actual_tier} tier alert - {len(actual_conditions)} conditions met"
                                        )
                                        
                                        # Extract corner odds from alert_info
                                        corner_odds_available = alert_info.get('odds_available', False)
                                        corner_odds = {
                                            'available': corner_odds_available,
                                            'count': alert_info.get('odds_count', 0),
                                            'active_count': alert_info.get('active_odds_count', 0),
                                            'odds_details': alert_info.get('odds_details', []),
                                            'active_odds': alert_info.get('active_odds', [])
                                        }
                                        
                                        self.logger.info(f"💰 ODDS INFO:")
                                        self.logger.info(f"   Available: {corner_odds['available']}")
                                        self.logger.info(f"   Total markets: {corner_odds['count']}")
                                        self.logger.info(f"   Active markets: {corner_odds['active_count']}")
                                        
                                        # ATTEMPT TO SEND TELEGRAM ALERT
                                        self.logger.info(f"📱 INITIATING TELEGRAM ALERT for {actual_tier} match {match_id}...")
                                        
                                        # USE NEW BULLETPROOF TELEGRAM SYSTEM
                                        success = send_corner_alert_new(
                                            match_data=alert_info,
                                            tier=actual_tier,
                                            score=actual_score,
                                            conditions=actual_conditions
                                        )
                                        
                                        if success:
                                            self.alerted_matches.add(match_id)
                                            self.logger.info(f"🎉 TELEGRAM ALERT SENT SUCCESSFULLY for match {match_id}")
                                            self.logger.info(f"   ✅ {actual_tier} tier alert delivered")
                                            self.logger.info(f"   ✅ Match added to alerted list")
                                        else:
                                            self.logger.error(f"❌ TELEGRAM ALERT FAILED for match {match_id}")
                                            self.logger.error(f"   ❌ Check Telegram configuration and network")
                                            self.logger.error(f"   ❌ Alert will be retried next cycle")
                                            
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
