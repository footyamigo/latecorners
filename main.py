#!/usr/bin/env python3

import asyncio
import copy
import logging
import time
from datetime import datetime
from typing import Dict, Set, Optional
import sys
import os

# Ensure DATABASE_URL is set for production deployment
if 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = 'postgresql://postgres:jIwhlnuBmXDEiHjndVZzCmxNEkpquJAL@trolley.proxy.rlwy.net:24044/railway'

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_config
from new_telegram_system import send_corner_alert_new, send_system_message_new
from alert_tracker import track_elite_alert
from result_checker import check_pending_results
from startup_flag import is_first_startup, mark_startup
# ReliableCornerSystem removed in favor of Late Momentum alerts
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
            # Try dashboard buffer if available; otherwise fallback to direct API client (no console prints)
            try:
                from web_dashboard import live_matches_data  # type: ignore
                source_matches = list(live_matches_data) if live_matches_data else []
            except Exception:
                source_matches = []

            if not source_matches:
                # API fallback to avoid Unicode printing issues in web_dashboard
                self.logger.info("Using API fallback for live matches (dashboard buffer empty)")
                try:
                    from sportmonks_client import SportmonksClient
                    api_client = SportmonksClient()
                    api_matches = api_client.get_live_matches(filter_by_minute=False) or []
                    # Already SportMonks format → no conversion needed
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
            
        except ImportError:
            # Avoid non-ASCII in error logs on some Windows terminals
            self.logger.error("Error: Cannot import dashboard data - dashboard not running?")
            return []
        except Exception as e:
            # Avoid non-ASCII in error logs on some Windows terminals
            self.logger.error(f"Error reading shared dashboard data: {e}")
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
        # Align dashboard->SportMonks type IDs with livescores/inplay mapping
        stat_mapping = {
            'corners': 33,                # CORNERS (live feed)
            'possession': 45,             # POSSESSION % (live feed commonly uses 45)
            'shots_off_target': 41,       # SHOTS_OFF_TARGET
            'shots_total': 42,            # SHOTS_TOTAL
            'dangerous_attacks': 44,      # DANGEROUS_ATTACKS
            'attacks': 43,                # ATTACKS (when present)
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
            
            # Log minimal live stats only (avoid noisy unused fields)
            try:
                minimal_log = {
                    'fixture_id': fixture_id,
                    'minute': match_stats.minute,
                    'home_team': match_stats.home_team,
                    'away_team': match_stats.away_team,
                    'score': f"{match_stats.home_score}-{match_stats.away_score}",
                    'total_corners': match_stats.total_corners,
                    'shots_on_target': match_stats.shots_on_target,
                    'shots_total': match_stats.shots_total,
                    'possession': match_stats.possession,
                    'dangerous_attacks': match_stats.dangerous_attacks,
                    'attacks': match_stats.attacks,
                }
                self.logger.info(f"🧪 DEBUG (minimal): {minimal_log}")
            except Exception:
                # Fallback to raw object if something goes wrong
                self.logger.info(f"🧪 DEBUG: Stats for match {fixture_id}: {match_stats}")
            
            # Store current stats for momentum tracking
            current_stats = {
                'minute': match_stats.minute,
                'attacks': (match_stats.attacks or {}).copy(),
                'dangerous_attacks': (match_stats.dangerous_attacks or {}).copy(),
                'shots_total': (match_stats.shots_total or {}).copy(),
                'shots_on_target': (match_stats.shots_on_target or {}).copy(),
                # Minimal reliable set only; ignore crosses/offsides/blocked/etc.
                'shots_off_target': (match_stats.shots_off_target or {}).copy(),
                'possession': (match_stats.possession or {}).copy(),
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
            # Update momentum tracker and log 10-minute momentum
            try:
                self.momentum_tracker.add_snapshot(
                    fixture_id=fixture_id,
                    minute=match_stats.minute,
                    home={
                        'shots_on_target': current_stats['shots_on_target'].get('home', 0),
                        'shots_off_target': current_stats['shots_off_target'].get('home', 0),
                        'dangerous_attacks': current_stats['dangerous_attacks'].get('home', 0),
                        'possession': current_stats['possession'].get('home', 0),
                    },
                    away={
                        'shots_on_target': current_stats['shots_on_target'].get('away', 0),
                        'shots_off_target': current_stats['shots_off_target'].get('away', 0),
                        'dangerous_attacks': current_stats['dangerous_attacks'].get('away', 0),
                        'possession': current_stats['possession'].get('away', 0),
                    },
                )
                momentum_scores = self.momentum_tracker.compute_scores(fixture_id)
                home_ms = momentum_scores['home']
                away_ms = momentum_scores['away']
                combined_total = home_ms['total'] + away_ms['total']
                coverage_min = max(home_ms.get('window_covered', 0), away_ms.get('window_covered', 0))
                self.logger.info(
                    f"   ⚡ Momentum10 (window {coverage_min}m): HOME {home_ms['total']} pts (SOT {home_ms['on_target_points']}, SOFF {home_ms['off_target_points']}, DA {home_ms['dangerous_points']}, POS {home_ms['possession_points']})"
                )
                self.logger.info(
                    f"                                 AWAY {away_ms['total']} pts (SOT {away_ms['on_target_points']}, SOFF {away_ms['off_target_points']}, DA {away_ms['dangerous_points']}, POS {away_ms['possession_points']})"
                )
                self.logger.info(f"   Σ Combined Momentum10: {combined_total} pts")
            except Exception as e:
                self.logger.error(f"❌ Momentum tracker error: {e}")
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

            # Fetch live draw odds (Fulltime Result market)
            try:
                from sportmonks_client import SportmonksClient
                _client = SportmonksClient()
                draw_odds = _client.get_live_draw_odds(fixture_id)
                self.logger.info(f"   🧮 Draw odds: {draw_odds}")
            except Exception as e:
                draw_odds = None
                self.logger.error(f"   ❌ Draw odds fetch error: {e}")

            # Get previous stats or empty dict if first time
            previous_stats = self.previous_stats.get(fixture_id, {})
            # Compute minutes passed between snapshots (1-5 clamp)
            if previous_stats and isinstance(previous_stats, dict) and 'minute' in previous_stats:
                raw_minutes_passed = max(0, match_stats.minute - int(previous_stats.get('minute', match_stats.minute)))
                minutes_passed = min(5, max(1, raw_minutes_passed))
            else:
                minutes_passed = 5

            # New Late Momentum system
            combined_momentum = home_ms['total'] + away_ms['total']
            self.logger.info(f"   🔢 Late Momentum combined: {combined_momentum} pts")
            late_momentum_ok = (
                85 <= match_stats.minute <= 89 and
                current_stats.get('has_live_asian_corners', False) and
                match_stats.total_corners >= 9 and
                combined_momentum >= 75
            )

            # Log the analysis
            self.logger.info(f"\n📊 ANALYZING MATCH {fixture_id}:")
            self.logger.info(f"   {match_stats.home_team} vs {match_stats.away_team}")
            self.logger.info(f"   Score: {match_stats.home_score}-{match_stats.away_score}")
            self.logger.info(f"   Minute: {match_stats.minute}")
            self.logger.info(f"   Corners: {match_stats.total_corners}")

            # New system 2: Late Corner using Draw Odds (now also requires momentum >= 75)
            draw_odds_ok = (
                85 <= match_stats.minute <= 89 and
                current_stats.get('has_live_asian_corners', False) and
                (draw_odds is not None and draw_odds <= 1.50) and
                combined_momentum >= 75
            )

            if not (late_momentum_ok or draw_odds_ok):
                self.logger.info("\n❌ NO ALERT - Late Momentum system:")
                self.logger.info(f"   • Odds: {'OK' if current_stats.get('has_live_asian_corners') else 'MISSING'}")
                self.logger.info(f"   • Combined Momentum10: {combined_momentum} (need ≥ 75)")
                self.logger.info(f"   • Total corners: {match_stats.total_corners} (need ≥ 9)")
                self.logger.info("❌ NO ALERT - Draw Odds system:")
                self.logger.info(f"   • Draw odds: {draw_odds if draw_odds is not None else 'N/A'} (need ≤ 1.50)")
                self.logger.info(f"   • Combined Momentum10: {combined_momentum} (need ≥ 75)")
                # Update previous stats for momentum tracking on next cycle
                self.previous_stats[fixture_id] = copy.deepcopy(current_stats)
                return None

            # If we get here, the alert is triggered
            triggered_tier = "LATE_MOMENTUM" if late_momentum_ok else "LATE_MOMENTUM_DRAW"
            self.logger.info(f"\n✅ ALERT TRIGGERED! ({'Late Momentum' if late_momentum_ok else 'Late Momentum using Draw Odds'})")
            momentum_indicators = {
                'combined_momentum10': combined_momentum,
                'home_momentum10': home_ms['total'],
                'away_momentum10': away_ms['total'],
                'draw_odds': draw_odds if draw_odds is not None else 0.0,
            }

            # Prepare alert info
            alert_info = {
                'fixture_id': fixture_id,
                'home_team': match_stats.home_team,
                'away_team': match_stats.away_team,
                'home_score': match_stats.home_score,
                'away_score': match_stats.away_score,
                'minute': match_stats.minute,
                'total_corners': match_stats.total_corners,
                'tier': triggered_tier,
                # Store combined probability as the alert score
                'total_probability': float(combined_momentum),
                'best_team': 'home' if home_ms['total'] >= away_ms['total'] else 'away',
                'team_probability': float(max(home_ms['total'], away_ms['total'])),
                'momentum_indicators': momentum_indicators,
                'momentum_home': home_ms,
                'momentum_away': away_ms,
                'detected_patterns': [],
                'odds_count': corner_odds.get('count', 0),
                'active_odds_count': corner_odds.get('active_count', 0),
                'odds_details': corner_odds.get('odds_details', []),
                'active_odds': corner_odds.get('active_odds', []),
                # Add shots on target statistics for database storage
                'home_shots_on_target': match_stats.shots_on_target.get('home', 0),
                'away_shots_on_target': match_stats.shots_on_target.get('away', 0),
                'total_shots_on_target': match_stats.shots_on_target.get('home', 0) + match_stats.shots_on_target.get('away', 0)
            }

            # Build human-readable conditions for the alert
            if triggered_tier == "LATE_MOMENTUM":
                alert_conditions = [
                    "Asian Odds Available",
                    "Match time 85-89th",
                    f"Combined Momentum ≥ 75 (now {combined_momentum:.0f})",
                    f"Total Corners ≥ 9 (now {match_stats.total_corners})",
                ]
            else:
                alert_conditions = [
                    "Asian Odds Available",
                    "Match time 85-89th",
                    f"Combined Momentum ≥ 75 (now {combined_momentum:.0f})",
                    f"Draw odds ≤ 1.50 (now {draw_odds:.2f})",
                ]

            # SAVE ALERT TO DATABASE FIRST
            self.logger.info(f"💾 SAVING ALERT TO DATABASE for {triggered_tier} match {fixture_id}...")
            
            try:
                # Save alert with new system metrics
                # Add draw odds and alert_type into alert info for DB/Telegram visibility
                alert_info['draw_odds'] = draw_odds
                alert_info['alert_type'] = 'LATE_MOMENTUM' if late_momentum_ok else 'LATE_MOMENTUM_DRAW'

                track_success = track_elite_alert(
                    match_data=alert_info,
                    tier=triggered_tier,
                    score=alert_info['total_probability'],
                    conditions=alert_conditions,
                    momentum_indicators=momentum_indicators,
                    detected_patterns=[]
                )
                
                if track_success:
                    self.logger.info(f"✅ ALERT SAVED TO DATABASE")
                    self.logger.info("   Metrics saved:")
                    self.logger.info(f"   • Combined Probability: {alert_info['total_probability']:.1f}%")
                    self.logger.info(f"   • Attack Quality: {momentum_indicators['attack_intensity']:.1f}%")
                    self.logger.info(f"   • Corner Momentum: {momentum_indicators['corner_momentum']:.1f}%")
                    self.logger.info(f"   • Score Context: {momentum_indicators['score_context']:.1f}%")
                    self.logger.info(f"   • Patterns: 0")
                else:
                    self.logger.error(f"❌ DATABASE SAVE FAILED: Alert not saved to database")
            except Exception as e:
                self.logger.error(f"❌ DATABASE SAVE ERROR: {e}")
                import traceback
                self.logger.error(traceback.format_exc())

            # THEN ATTEMPT TO SEND TELEGRAM ALERT
            self.logger.info(f"📱 SENDING TELEGRAM ALERT for {triggered_tier} match {fixture_id}...")
            
            try:
                telegram_success = send_corner_alert_new(
                    match_data=alert_info,
                    tier=triggered_tier,
                    score=alert_info['total_probability'],
                    conditions=alert_conditions
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
                
                # Look for corners in statistics (33 or 34 depending on feed)
                for stat in match_stats.statistics:
                    if stat.get('type_id') in (33, 34):  # Corners
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
                        # Always feed momentum tracker for ALL live matches from minute 0
                        try:
                            for m in shared_live_matches:
                                try:
                                    parsed = self._parse_match_data_from_shared(m)
                                    if not parsed:
                                        continue
                                    self.momentum_tracker.add_snapshot(
                                        fixture_id=parsed.fixture_id,
                                        minute=parsed.minute,
                                        home={
                                            'shots_on_target': parsed.shots_on_target.get('home', 0),
                                            'shots_off_target': parsed.shots_off_target.get('home', 0),
                                            'dangerous_attacks': parsed.dangerous_attacks.get('home', 0),
                                            'possession': parsed.possession.get('home', 0),
                                        },
                                        away={
                                            'shots_on_target': parsed.shots_on_target.get('away', 0),
                                            'shots_off_target': parsed.shots_off_target.get('away', 0),
                                            'dangerous_attacks': parsed.dangerous_attacks.get('away', 0),
                                            'possession': parsed.possession.get('away', 0),
                                        },
                                    )
                                except Exception:
                                    continue
                        except Exception:
                            pass
                        
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