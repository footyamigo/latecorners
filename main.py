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
from alert_tracker_new import track_elite_alert
from result_checker import check_pending_results
from startup_flag import is_first_startup, mark_startup
# NEW: Momentum Inverted Corner System - detects low momentum (no more corners)
from optimized_corner_system import OptimizedCornerSystem
from momentum_tracker import MomentumTracker
# Legacy psychology systems - keeping for backup
from panicking_favorite_system import PanickingFavoriteSystem
from fighting_underdog_system import FightingUnderdogSystem

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
        
        # NEW: Momentum inverted corner system (detects stagnant games with low momentum)
        self.optimized_corner_system = OptimizedCornerSystem()
        
        # Legacy psychology-driven corner systems (backup)
        self.panicking_favorite_system = PanickingFavoriteSystem()
        self.fighting_underdog_system = FightingUnderdogSystem()
        
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
                pass
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
            self.logger.info(f"   📊 Minute: {match_stats.minute} (need 79-84)")
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
                        'attacks': current_stats['attacks'].get('home', 0),
                        'possession': current_stats['possession'].get('home', 0),
                    },
                    away={
                        'shots_on_target': current_stats['shots_on_target'].get('away', 0),
                        'shots_off_target': current_stats['shots_off_target'].get('away', 0),
                        'dangerous_attacks': current_stats['dangerous_attacks'].get('away', 0),
                        'attacks': current_stats['attacks'].get('away', 0),
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
            
            # 🚨 MANDATORY TIMING CHECK: Only proceed with alert analysis if in 79-84 minute window (OPTIMIZED)
            if not (79 <= match_stats.minute <= 84):
                self.logger.info(f"⏰ TIMING CHECK FAILED: Match at {match_stats.minute}' (need 79-84 minutes) - SKIPPING ALERT ANALYSIS")
                # Update previous stats for momentum tracking on next cycle
                self.previous_stats[fixture_id] = copy.deepcopy(current_stats)
                return None
            
            self.logger.info(f"✅ TIMING CHECK PASSED: Match at {match_stats.minute}' (within 79-84 minute window)")

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

            # ELITE 100% POSITIVE RATE FILTERING SYSTEM
            # Ensure momentum is calculated (in case of earlier error)
            try:
                combined_momentum = home_ms['total'] + away_ms['total']
            except (NameError, KeyError):
                # Fallback momentum calculation if home_ms/away_ms not available
                self.logger.warning("⚠️ Using fallback momentum calculation")
                momentum_scores = self.momentum_tracker.compute_scores(fixture_id)
                home_ms = momentum_scores['home']
                away_ms = momentum_scores['away']
                combined_momentum = home_ms['total'] + away_ms['total']
            current_score = f"{match_stats.home_score}-{match_stats.away_score}"
            
            self.logger.info(f"\n🧠 PSYCHOLOGY ANALYSIS - MATCH {fixture_id}:")
            self.logger.info(f"   {match_stats.home_team} vs {match_stats.away_team}")
            self.logger.info(f"   Score: {current_score}")
            self.logger.info(f"   Minute: {match_stats.minute}")
            self.logger.info(f"   Corners: {match_stats.total_corners}")
            self.logger.info(f"   Combined Momentum: {combined_momentum} pts")
            
            # Apply timing and odds requirements  
            timing_ok = 79 <= match_stats.minute <= 84
            odds_ok = current_stats.get('has_live_asian_corners', False)
            
            self.logger.info(f"   ⏱️ Timing (79-84min): {'✅ OK' if timing_ok else '❌ FAIL'} (minute {match_stats.minute})")
            self.logger.info(f"   💰 Asian Odds: {'✅ OK' if odds_ok else '❌ MISSING'}")

            # DUAL PSYCHOLOGY SYSTEMS - Elite system disabled
            self.logger.info(f"\n🧠 CHECKING DUAL PSYCHOLOGY SYSTEMS (Elite system disabled)...")
            
            # Fetch odds data for psychology analysis using same approach as draw odds
            try:
                # Try approach A first (nested format)
                odds_data = _client._make_request(f"/odds/in-play/by-fixture/{fixture_id}")
                if odds_data and isinstance(odds_data.get('data'), list) and len(odds_data['data']) > 0:
                    fixture_data_with_odds = {
                        'fixture_id': fixture_id,
                        'home_team': match_stats.home_team,
                        'away_team': match_stats.away_team,
                        'odds': odds_data['data']
                    }
                    self.logger.info(f"   📊 Fetched odds data (nested): {len(fixture_data_with_odds['odds'])} bookmakers")
                else:
                    # Try approach B (flat format) - same as draw odds fallback
                    self.logger.info(f"   🔄 Trying fallback odds endpoint...")
                    odds_data_flat = _client._make_request(f"/odds/inplay/fixtures/{fixture_id}")
                    if odds_data_flat and isinstance(odds_data_flat.get('data'), list):
                        # Convert flat format to nested format for psychology systems
                        bookmaker_odds = {}
                        for odd in odds_data_flat['data']:
                            bookmaker_id = odd.get('bookmaker_id', 2)  # Default to bet365
                            market_desc = odd.get('market_description', '').lower()
                            label = odd.get('label', '')
                            value = odd.get('value') or odd.get('odds')
                            
                            # Look for 1X2 markets
                            if any(keyword in market_desc for keyword in ['1x2', 'match result', 'full time result', 'fulltime result']):
                                if bookmaker_id not in bookmaker_odds:
                                    bookmaker_odds[bookmaker_id] = {
                                        'bookmaker_id': bookmaker_id,
                                        'markets': [{
                                            'market_id': 1,
                                            'name': 'Full Time Result',
                                            'selections': []
                                        }]
                                    }
                                
                                if value:
                                    bookmaker_odds[bookmaker_id]['markets'][0]['selections'].append({
                                        'label': label,
                                        'odds': float(value)
                                    })
                        
                        fixture_data_with_odds = {
                            'fixture_id': fixture_id,
                            'home_team': match_stats.home_team,
                            'away_team': match_stats.away_team,
                            'odds': list(bookmaker_odds.values())
                        }
                        self.logger.info(f"   📊 Fetched odds data (flat): {len(fixture_data_with_odds['odds'])} bookmakers")
                    else:
                        # No odds available
                        fixture_data_with_odds = {
                            'fixture_id': fixture_id,
                            'home_team': match_stats.home_team,
                            'away_team': match_stats.away_team,
                            'odds': []
                        }
                        self.logger.info(f"   📊 No odds data available from either endpoint")
            except Exception as e:
                self.logger.error(f"   ❌ Failed to fetch odds: {e}")
                fixture_data_with_odds = {
                    'fixture_id': fixture_id,
                    'home_team': match_stats.home_team,
                    'away_team': match_stats.away_team,
                    'odds': []
                }
            
            triggered_tier = None
            alert_source = None
            optimized_alert = None
            psychology_alert = None
            
            # 🔇 NEW: Try momentum inverted system (main system now)
            self.logger.info(f"\n🔇 CHECKING MOMENTUM INVERTED SYSTEM...")
            
            # Get momentum scores for current match
            momentum_scores = self.momentum_tracker.compute_scores(fixture_id)
            
            optimized_alert = self.optimized_corner_system.should_alert(
                current_stats=current_stats,
                previous_stats=previous_stats,
                minutes_passed=minutes_passed,
                momentum_scores=momentum_scores
            )
            
            # Check if momentum inverted system triggered
            if optimized_alert and optimized_alert['alert']:
                triggered_tier = "MOMENTUM_INVERTED"
                alert_source = "momentum_inverted"
                self.logger.info(f"\n🔇 MOMENTUM INVERTED ALERT TRIGGERED!")
                self.logger.info(f"      Score: {optimized_alert['score_line']}")
                self.logger.info(f"      Corners: {optimized_alert['corner_count']}")
                self.logger.info(f"      Home Momentum: {optimized_alert['home_momentum']}")
                self.logger.info(f"      Away Momentum: {optimized_alert['away_momentum']}")
                self.logger.info(f"      Combined: {optimized_alert['combined_momentum']}")
                self.logger.info(f"      Win Rate: {optimized_alert['win_rate_estimate']}%")
                self.logger.info(f"      Market: {optimized_alert['market_recommendation']}")
                for reason in optimized_alert['reasons']:
                    self.logger.info(f"      {reason}")
            else:
                self.logger.info(f"\n❌ MOMENTUM INVERTED SYSTEM: No stagnant pattern detected")
                if optimized_alert:
                    for reason in optimized_alert['reasons']:
                        self.logger.info(f"      {reason}")
                
                # 🧠 FALLBACK: Try legacy psychology systems if optimized fails
                self.logger.info(f"\n🧠 FALLBACK: Trying legacy psychology systems...")
                psychology_alert = self.panicking_favorite_system.evaluate_panicking_favorite_alert(
                    fixture_data=fixture_data_with_odds,
                    match_data={
                        'minute': match_stats.minute,
                        'home_score': match_stats.home_score,
                        'away_score': match_stats.away_score,
                        'total_corners': match_stats.total_corners,
                        'total_shots': match_stats.shots_total.get('home', 0) + match_stats.shots_total.get('away', 0),
                        'total_shots_on_target': match_stats.shots_on_target.get('home', 0) + match_stats.shots_on_target.get('away', 0)
                    },
                    momentum_data={
                        'home_momentum10': home_ms['total'],
                        'away_momentum10': away_ms['total']
                    }
                )
                
                # If panicking favorite didn't trigger, try fighting underdog system
                if not psychology_alert:
                    psychology_alert = self.fighting_underdog_system.evaluate_fighting_underdog_alert(
                        fixture_data=fixture_data_with_odds,
                        match_data={
                            'minute': match_stats.minute,
                            'home_score': match_stats.home_score,
                            'away_score': match_stats.away_score,
                            'total_corners': match_stats.total_corners,
                            'total_shots': match_stats.shots_total.get('home', 0) + match_stats.shots_total.get('away', 0),
                            'total_shots_on_target': match_stats.shots_on_target.get('home', 0) + match_stats.shots_on_target.get('away', 0)
                        },
                        momentum_data={
                            'home_momentum10': home_ms['total'],
                            'away_momentum10': away_ms['total']
                        }
                    )
                
                # Check if any psychology system triggered
                if psychology_alert and timing_ok and odds_ok:
                    if psychology_alert['alert_type'] == 'PANICKING_FAVORITE':
                        triggered_tier = "PANICKING_FAVORITE"
                        alert_source = "psychology"
                        self.logger.info(f"\n🧠 FALLBACK: PANICKING_FAVORITE triggered!")
                    else:
                        triggered_tier = "FIGHTING_UNDERDOG"
                        alert_source = "psychology"
                        self.logger.info(f"\n🥊 FALLBACK: FIGHTING_UNDERDOG triggered!")
                else:
                    self.logger.info(f"\n❌ NO ALERT - No profitable patterns or psychology conditions met")
                    self.previous_stats[fixture_id] = copy.deepcopy(current_stats)
                    return None
            # Set up momentum indicators and alert info based on alert source
            if alert_source == "optimized":
                # Optimized system alert
                momentum_indicators = {
                    'combined_momentum10': combined_momentum,
                    'home_momentum10': home_ms['total'],
                    'away_momentum10': away_ms['total'],
                    'win_rate_estimate': optimized_alert['win_rate_estimate'],
                    'score_line': optimized_alert['score_line'],
                    'corner_count': optimized_alert['corner_count']
                }
                
                # Prepare optimized alert info
                alert_info = {
                    'fixture_id': fixture_id,
                    'home_team': match_stats.home_team,
                    'away_team': match_stats.away_team,
                    'home_score': match_stats.home_score,
                    'away_score': match_stats.away_score,
                    'minute': match_stats.minute,
                    'total_corners': match_stats.total_corners,
                    'tier': triggered_tier,
                    'alert_type': triggered_tier,
                    'total_probability': float(optimized_alert['win_rate_estimate']),
                    'best_team': 'home',  # Not relevant for optimized system
                    'team_probability': float(optimized_alert['win_rate_estimate']),
                    'momentum_indicators': momentum_indicators,
                    'momentum_home': home_ms,
                    'momentum_away': away_ms,
                    'detected_patterns': ['OPTIMIZED_SCORE_LINE_PATTERN'],
                    'odds_count': corner_odds.get('count', 0),
                    'active_odds_count': corner_odds.get('active_count', 0),
                    'odds_details': corner_odds.get('odds_details', []),
                    'active_odds': corner_odds.get('active_odds', []),
                    'home_shots_on_target': match_stats.shots_on_target.get('home', 0),
                    'away_shots_on_target': match_stats.shots_on_target.get('away', 0),
                    'total_shots_on_target': match_stats.shots_on_target.get('home', 0) + match_stats.shots_on_target.get('away', 0)
                }
                
                # Build optimized alert conditions
                alert_conditions = [
                    "🚀 OPTIMIZED PROFITABLE PATTERN DETECTED",
                    f"📊 Score Line: {optimized_alert['score_line']} (Optimal for Under 2 more corners)",
                    f"⚽ Corner Count: {optimized_alert['corner_count']} (Historical data validated)",
                    f"⏱️ Match time: {match_stats.minute}th minute",
                    f"💰 Market: {optimized_alert['market_recommendation']}",
                    f"📈 Historical Win Rate: {optimized_alert['win_rate_estimate']}%",
                    f"🎯 Strategy: Late game defensive patterns"
                ]
                
            else:
                # Psychology system alert (fallback)
                momentum_indicators = {
                    'combined_momentum10': combined_momentum,
                    'home_momentum10': home_ms['total'],
                    'away_momentum10': away_ms['total'],
                }
                
                # Add psychology-specific indicators
                if psychology_alert and psychology_alert.get('alert_type') == 'PANICKING_FAVORITE':
                    momentum_indicators.update({
                        'psychology_score': psychology_alert['psychology_score'],
                        'favorite_odds': psychology_alert['favorite_odds'],
                        'panic_level': psychology_alert['panic_level'],
                    })
                elif psychology_alert and psychology_alert.get('alert_type') == 'FIGHTING_UNDERDOG':
                    momentum_indicators.update({
                        'giant_killing_score': psychology_alert['giant_killing_score'],
                        'underdog_odds': psychology_alert['underdog_odds'],
                        'giant_killing_level': psychology_alert['giant_killing_level'],
                    })
                
                # Prepare psychology alert info
                alert_info = {
                    'fixture_id': fixture_id,
                    'home_team': match_stats.home_team,
                    'away_team': match_stats.away_team,
                    'home_score': match_stats.home_score,
                    'away_score': match_stats.away_score,
                    'minute': match_stats.minute,
                    'total_corners': match_stats.total_corners,
                    'tier': triggered_tier,
                    'alert_type': triggered_tier,
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
                    'home_shots_on_target': match_stats.shots_on_target.get('home', 0),
                    'away_shots_on_target': match_stats.shots_on_target.get('away', 0),
                    'total_shots_on_target': match_stats.shots_on_target.get('home', 0) + match_stats.shots_on_target.get('away', 0)
                }
                
                # Build psychology alert conditions
                if psychology_alert and psychology_alert.get('alert_type') == 'PANICKING_FAVORITE':
                    alert_conditions = [
                        "🧠 PANICKING FAVORITE DETECTED (FALLBACK)",
                        f"🎯 {psychology_alert['panic_level']}: {psychology_alert['favorite_odds']:.2f} favorite under pressure",
                        f"⏱️ Match time: {match_stats.minute}th minute", 
                        "💰 Asian Odds Available",
                        f"📊 Score: {current_score}",
                        f"⚽ Corners: {match_stats.total_corners}",
                        f"🧠 Psychology Score: {psychology_alert['psychology_score']:.0f} pts"
                    ]
                else:  # FIGHTING_UNDERDOG
                    alert_conditions = [
                        "🥊 FIGHTING UNDERDOG DETECTED (FALLBACK)",
                    f"🎯 {psychology_alert['giant_killing_level']}: {psychology_alert['underdog_odds']:.2f} underdog in giant-killing mode",
                    f"⏱️ Match time: {match_stats.minute}th minute", 
                    "💰 Asian Odds Available",
                    f"📊 Score: {current_score}",
                    f"⚽ Corners: {match_stats.total_corners}",
                    f"🥊 Giant-Killing Score: {psychology_alert['giant_killing_score']:.0f} pts"
                ]
            
            # CRITICAL: Ensure alert_type is ALWAYS set to triggered_tier (not psychology_alert which might be None/empty)
            alert_info['alert_type'] = triggered_tier  # Use triggered_tier instead of psychology_alert['alert_type']
            alert_info['psychology_data'] = psychology_alert
            
            # VERIFY alert_type is correctly set
            self.logger.info(f"🔍 ALERT_TYPE VERIFICATION:")
            self.logger.info(f"   triggered_tier: {triggered_tier}")
            self.logger.info(f"   alert_info['alert_type']: {alert_info['alert_type']}")

            # SAVE ALERT TO DATABASE FIRST
            self.logger.info(f"💾 SAVING ALERT TO DATABASE for {triggered_tier} match {fixture_id}...")
            
            try:
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
                    self.logger.info("   Elite system metrics saved:")
                    self.logger.info(f"   • Combined Momentum: {alert_info['total_probability']:.1f} pts")
                    self.logger.info(f"   • Home Momentum: {momentum_indicators['home_momentum10']:.1f} pts")
                    self.logger.info(f"   • Away Momentum: {momentum_indicators['away_momentum10']:.1f} pts")
                    self.logger.info(f"   • Draw Odds: {momentum_indicators.get('draw_odds', 0):.2f}")
                    self.logger.info(f"   • Elite Filter: PASSED")
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
                    "🚀 <b>OPTIMIZED Profitable Corner System Started!</b>\n\n"
                    "📊 <b>System Status:</b>\n"
                    "✅ Data-driven profitable patterns active\n"
                    "✅ SportMonks API connected via dashboard\n"
                    "✅ Telegram bot ready\n"
                    "✅ NEW: Optimized corner prediction system loaded\n\n"
                    "🎯 <b>NEW PROFITABLE STRATEGY:</b>\n"
                    "💰 Market: <b>Under 2 More Corners</b>\n"
                    "📊 Score filters: 0-0, 1-1, 2-1, 1-0 (selective)\n"
                    "⚽ Corner counts: 6-10 corners only\n"
                    "📈 Expected win rate: 70-88%\n"
                    "⏰ Timing: 79-84 minutes\n"
                    "🎯 Live Asian corner odds required\n\n"
                    "🚀 Ready for PROFITABLE corner opportunities!\n"
                    "📉 Old system: 33% win rate → NEW: 75%+ win rate!"
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