#!/usr/bin/env python3
"""
FIRST HALF ASIAN CORNER MONITORING SYSTEM
=========================================
Complete monitoring loop for first half corner alerts (30-35 minutes).

Targets Market ID 63 "1st Half Asian Corners" with same high standards as late corner system.
Completely isolated from late corner system to avoid any interference.

Psychology Systems:
- Halftime Panic Favorites (heavy favorites under pressure)
- Halftime Giant Killers (massive underdogs defying odds)

Same database, same Telegram, same quality - just different timing and market!
"""

import asyncio
import copy
import logging
import time
from datetime import datetime
from typing import Dict, Set, Optional
import sys
import os

# Ensure DATABASE_URL is set
if 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = 'postgresql://postgres:jIwhlnuBmXDEiHjndVZzCmxNEkpquJAL@trolley.proxy.rlwy.net:24044/railway'

# Add parent directory to path to access main system modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import main system modules (same as late corner system)
from config import get_config
from database_postgres import get_database
from sportmonks_client import SportmonksClient

# Import first half system modules
from .first_half_analyzer import FirstHalfAnalyzer
from .first_half_telegram_system import FirstHalfTelegramSystem

class FirstHalfMonitor:
    """Monitor live matches for first half corner betting opportunities (30-35 minutes)"""
    
    def __init__(self):
        self.config = get_config()
        
        # Track which matches we've already alerted on for first half
        self.first_half_alerted_matches: Set[int] = set()
        self.monitored_matches: Set[int] = set()
        
        # Track previous stats for momentum calculation
        self.previous_stats = {}
        
        # Track discovery cycles
        self.match_discovery_counter = 0
        
        # Initialize first half analyzer (10-minute momentum window, same as late system)
        self.first_half_analyzer = FirstHalfAnalyzer()
        
        # Initialize first half telegram system
        self.first_half_telegram = FirstHalfTelegramSystem()
        
        # Initialize API client and database
        self.api_client = SportmonksClient()
        self.database = get_database()
        
        self.logger = self._setup_logging()
        
        self.logger.info("🏁 FIRST HALF MONITOR INITIALIZED")
        self.logger.info(f"   Target timing: 30-35 minutes")
        self.logger.info(f"   Target market: 63 '1st Half Asian Corners'")
        self.logger.info(f"   Psychology systems: Halftime Panic + Giant Killer")
        self.logger.info(f"   Same high standards as late corner system!")
        
    def _setup_logging(self):
        """Setup logging configuration for first half system"""
        
        # Create logger
        logger = logging.getLogger('first_half_monitor')
        logger.setLevel(getattr(logging, self.config.LOG_LEVEL))
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - FIRST_HALF - %(levelname)s - %(message)s'
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
        """Get live matches from shared dashboard data (SAME AS LATE CORNER SYSTEM)"""
        try:
            # Try dashboard buffer if available; otherwise fallback to direct API client (no console prints)
            try:
                from web_dashboard import live_matches_data  # type: ignore
                source_matches = list(live_matches_data) if live_matches_data else []
            except Exception:
                source_matches = []

            if not source_matches:
                # API fallback to avoid Unicode printing issues in web_dashboard
                self.logger.info("🏁 FIRST HALF: Using API fallback for live matches (dashboard buffer empty)")
                try:
                    from sportmonks_client import SportmonksClient
                    api_client = SportmonksClient()
                    api_matches = api_client.get_live_matches(filter_by_minute=False) or []
                    # Already SportMonks format → no conversion needed
                    self.logger.info(f"🏁 FIRST HALF: API fallback returned {len(api_matches)} live matches")
                    return api_matches
                except Exception as e:
                    self.logger.error(f"🏁 FIRST HALF: API fallback failed: {e}")
                    return []

            # Convert dashboard format to SportMonks-compatible format
            matches = []
            for dashboard_match in source_matches:
                converted_match = self._convert_dashboard_to_sportmonks_format(dashboard_match)
                if converted_match:
                    matches.append(converted_match)
            
            self.logger.info(f"🏁 FIRST HALF: Dashboard buffer returned {len(matches)} live matches")
            return matches
            
        except ImportError:
            # Avoid non-ASCII in error logs on some Windows terminals
            self.logger.error("🏁 FIRST HALF: Error: Cannot import dashboard data - dashboard not running?")
            return []
        except Exception as e:
            # Avoid non-ASCII in error logs on some Windows terminals
            self.logger.error(f"🏁 FIRST HALF: Error reading shared dashboard data: {e}")
            return []
    
    def _convert_dashboard_to_sportmonks_format(self, dashboard_match):
        """Convert dashboard match format to SportMonks format (COPIED FROM LATE CORNER SYSTEM)"""
        try:
            sportmonks_format = {
                'id': dashboard_match.get('match_id'),
                'localteam': {
                    'name': dashboard_match.get('home_team', 'Unknown Home'),
                    'data': {
                        'name': dashboard_match.get('home_team', 'Unknown Home')
                    }
                },
                'visitorteam': {
                    'name': dashboard_match.get('away_team', 'Unknown Away'),
                    'data': {
                        'name': dashboard_match.get('away_team', 'Unknown Away')
                    }
                },
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
                    'developer_name': 'INPLAY_1ST_HALF' if dashboard_match.get('minute', 0) <= 45 else 'INPLAY_2ND_HALF'
                },
                'league': {
                    'name': dashboard_match.get('league', 'Unknown League')
                },
                'statistics': self._convert_dashboard_stats_to_sportmonks(dashboard_match.get('statistics', {}))
            }
            
            return sportmonks_format
            
        except Exception as e:
            self.logger.error(f"🏁 FIRST HALF: Error converting dashboard match {dashboard_match.get('match_id', 'unknown')}: {e}")
            return None
    
    def _convert_dashboard_stats_to_sportmonks(self, dashboard_stats):
        """Convert dashboard statistics format to SportMonks format (COPIED FROM LATE CORNER SYSTEM)"""
        try:
            home_stats = dashboard_stats.get('home', {})
            away_stats = dashboard_stats.get('away', {})
            
            # Convert dashboard stats to SportMonks statistics format
            statistics = []
            
            # Map dashboard stat names to SportMonks type IDs
            stat_mapping = {
                'shots_on_target': 86,
                'shots_off_target': 87,
                'shots_total': 42,
                'dangerous_attacks': 44,
                'attacks': 43,
                'possession': 45,
                'corners': 33
            }
            
            for stat_name, type_id in stat_mapping.items():
                # Add home stat
                if stat_name in home_stats:
                    statistics.append({
                        'type_id': type_id,
                        'data': {'value': home_stats[stat_name]},
                        'location': 'home'
                    })
                
                # Add away stat
                if stat_name in away_stats:
                    statistics.append({
                        'type_id': type_id,
                        'data': {'value': away_stats[stat_name]},
                        'location': 'away'
                    })
            
            return statistics
            
        except Exception as e:
            self.logger.error(f"🏁 FIRST HALF: Error converting dashboard stats: {e}")
            return []

    def _is_first_half_target_match(self, match) -> bool:
        """Check if match is in first half target window (30-35 minutes)"""
        try:
            minute = match.get('minute', 0)
            state = match.get('state', {}).get('short_name', '')
            
            # Must be in 30-35 minute window and in first half
            if not (30 <= minute <= 35):
                return False
                
            # Must be in first half (1H) or general in-play
            if state not in ['1H', 'LIVE', 'HT']:  # HT = halftime is OK (might be just ending first half)
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking first half target match: {e}")
            return False
    
    def _extract_match_stats(self, match):
        """Extract match statistics in standardized format"""
        try:
            # Basic match info
            fixture_id = match.get('id', 0)
            minute = match.get('minute', 0)
            
            # Team names
            home_team = match.get('localteam', {}).get('name', 'Home Team')
            away_team = match.get('visitorteam', {}).get('name', 'Away Team')
            
            # Scores
            home_score = 0
            away_score = 0
            
            if 'scores' in match:
                for score in match['scores']:
                    if score.get('score') == 'localteam':
                        home_score = score.get('goal', 0)
                    elif score.get('score') == 'visitorteam':
                        away_score = score.get('goal', 0)
            
            # Statistics - initialize with defaults
            stats = {
                'shots_on_target': {'home': 0, 'away': 0},
                'shots_off_target': {'home': 0, 'away': 0},
                'shots_total': {'home': 0, 'away': 0},
                'dangerous_attacks': {'home': 0, 'away': 0},
                'attacks': {'home': 0, 'away': 0},
                'possession': {'home': 50, 'away': 50},
            }
            
            # Extract statistics from API response
            if 'statistics' in match:
                for stat in match['statistics']:
                    stat_id = stat.get('type_id')
                    location = stat.get('location', '').lower()
                    value = stat.get('data', {}).get('value', 0)
                    
                    try:
                        value = int(value) if value else 0
                    except:
                        value = 0
                    
                    # Map SportMonks stat IDs to our format
                    if stat_id == 86:  # Shots on target
                        if location == 'home':
                            stats['shots_on_target']['home'] = value
                        else:
                            stats['shots_on_target']['away'] = value
                    elif stat_id == 87:  # Shots off target  
                        if location == 'home':
                            stats['shots_off_target']['home'] = value
                        else:
                            stats['shots_off_target']['away'] = value
                    elif stat_id == 42:  # Total shots
                        if location == 'home':
                            stats['shots_total']['home'] = value
                        else:
                            stats['shots_total']['away'] = value
                    elif stat_id == 44:  # Dangerous attacks
                        if location == 'home':
                            stats['dangerous_attacks']['home'] = value
                        else:
                            stats['dangerous_attacks']['away'] = value
                    elif stat_id == 43:  # Attacks
                        if location == 'home':
                            stats['attacks']['home'] = value
                        else:
                            stats['attacks']['away'] = value
                    elif stat_id == 45:  # Possession
                        if location == 'home':
                            stats['possession']['home'] = value
                            stats['possession']['away'] = 100 - value
                        else:
                            stats['possession']['away'] = value
                            stats['possession']['home'] = 100 - value
            
            # Count corners
            total_corners = 0
            if 'events' in match:
                for event in match['events']:
                    if event.get('type', {}).get('name') == 'corner':
                        total_corners += 1
            
            # Calculate total shots for validation
            total_shots_on_target = stats['shots_on_target']['home'] + stats['shots_on_target']['away']
            total_shots = stats['shots_total']['home'] + stats['shots_total']['away']
            
            # Build match stats object
            match_stats = {
                'fixture_id': fixture_id,
                'minute': minute,
                'home_team': home_team,
                'away_team': away_team,
                'home_score': home_score,
                'away_score': away_score,
                'total_corners': total_corners,
                'total_shots': total_shots,
                'total_shots_on_target': total_shots_on_target,
                **stats
            }
            
            return match_stats
            
        except Exception as e:
            self.logger.error(f"Error extracting match stats: {e}")
            return None
    
    def _save_first_half_alert_to_database(self, alert_info: Dict) -> bool:
        """Save first half alert to database (same table as late corner system)"""
        try:
            # Add first half specific fields
            alert_info['market_type'] = '1st_half_asian_corners'
            alert_info['market_id'] = 63
            
            # Save to same alerts table
            success = self.database.save_alert(alert_info)
            
            if success:
                self.logger.info(f"✅ FIRST HALF: Alert saved to database")
                return True
            else:
                self.logger.error(f"❌ FIRST HALF: Failed to save alert to database")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ FIRST HALF: Database error: {e}")
            return False
    
    async def _analyze_first_half_opportunity(self, match, match_stats):
        """Analyze first half corner opportunity - build momentum from 20+ min, alert at 30-35 min"""
        
        fixture_id = match_stats['fixture_id']
        minute = match_stats['minute']
        
        # Always add snapshot to build momentum history (like late corner system)
        self.first_half_analyzer.add_match_snapshot(fixture_id, minute, match_stats)
        
        # Only proceed with ALERT analysis if in 30-35 minute window
        if not (30 <= minute <= 35):
            self.logger.info(f"📊 FIRST HALF MOMENTUM: Match at {minute}' - building history for future alerts")
            return None

        self.logger.info(f"✅ FIRST HALF TIMING CHECK PASSED: Match at {minute}' (within 30-35 minute window)")
        
        # Check if already alerted for this match in first half
        if fixture_id in self.first_half_alerted_matches:
            self.logger.info(f"📵 FIRST HALF: Already alerted on match {fixture_id} - skipping")
            return None
        
        try:
            # Analyze first half opportunity using psychology systems
            alert_data = self.first_half_analyzer.analyze_first_half_opportunity(
                fixture_id, match, match_stats
            )
            
            if not alert_data:
                self.logger.info(f"⏭️ FIRST HALF: No alert conditions met for match {fixture_id}")
                return None
            
            # Get first half corner odds (Market ID 63)
            first_half_odds = await self._get_first_half_odds(fixture_id)
            
            # Prepare alert info for database (same format as late system)
            alert_info = {
                'fixture_id': fixture_id,
                'home_team': match_stats['home_team'],
                'away_team': match_stats['away_team'],
                'home_score': match_stats['home_score'],
                'away_score': match_stats['away_score'],
                'minute': minute,
                'total_corners': match_stats['total_corners'],
                'tier': alert_data['tier'],
                'alert_type': alert_data['alert_type'],
                'total_probability': float(alert_data['combined_momentum']),
                'team_probability': None,  # Not used in first half system
                'conditions': alert_data['reasoning'],
                'active_odds': first_half_odds,
                'odds_details': first_half_odds,
                'market_type': '1st_half_asian_corners',
                'market_id': 63,
                'psychology_data': {
                    'type': alert_data.get('psychology_type', ''),
                    'confidence': alert_data.get('confidence_level', ''),
                    'momentum': alert_data['combined_momentum']
                }
            }
            
            # Save to database
            database_success = self._save_first_half_alert_to_database(alert_info)
            
            # Send Telegram alert
            telegram_success = self.first_half_telegram.send_first_half_alert(match_stats, alert_data)
            
            if database_success and telegram_success:
                # Mark as alerted
                self.first_half_alerted_matches.add(fixture_id)
                
                self.logger.info(f"🎉 FIRST HALF: Alert successfully sent and saved!")
                self.logger.info(f"   Type: {alert_data['alert_type']}")
                self.logger.info(f"   Market: 1st Half Asian Corners")
                self.logger.info(f"   Momentum: {alert_data['combined_momentum']:.0f} pts")
                
                return alert_data
            else:
                self.logger.error(f"❌ FIRST HALF: Alert processing failed (DB: {database_success}, TG: {telegram_success})")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ FIRST HALF: Error analyzing opportunity: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _get_first_half_odds(self, fixture_id: int) -> list:
        """Get first half corner odds from API (Market ID 63)"""
        try:
            # Attempt to get first half corner odds
            odds_data = self.api_client.get_corner_odds(fixture_id)
            
            # Filter for first half corner odds (Market ID 63)
            first_half_odds = []
            
            if odds_data:
                for odds_str in odds_data:
                    # Look for first half corner indicators
                    if any(keyword in odds_str.lower() for keyword in ['1st half', 'first half', 'half corner']):
                        first_half_odds.append(odds_str)
            
            # If no specific first half odds found, generate generic recommendations
            if not first_half_odds:
                first_half_odds = [
                    "1st Half Asian Corners (check live markets)",
                    "First Half Over X.5 Corners"
                ]
            
            return first_half_odds[:3]  # Max 3 odds
            
        except Exception as e:
            self.logger.error(f"Error fetching first half odds for {fixture_id}: {e}")
            return ["1st Half Asian Corners (check live markets)"]
    
    async def run_monitoring_cycle(self):
        """Run a single monitoring cycle for first half opportunities (COPIED FROM LATE CORNER SYSTEM)"""
        
        try:
            self.logger.info("🏁 FIRST HALF: DISCOVERING new live matches from shared data...")
            
            # Use shared data instead of direct API call (SAME AS LATE CORNER SYSTEM)
            live_matches = self._get_shared_live_matches()
            
            if not live_matches:
                self.logger.warning("🏁 FIRST HALF: ⚠️ No live matches from shared data source")
                return
            
            self.logger.info(f"🏁 FIRST HALF: 📊 Found {len(live_matches)} live matches from shared data")
            
            # Filter matches that are actually in play and worth monitoring (FOR FIRST HALF)
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
                    
                    self.logger.info(f"🏁 FIRST HALF: 🧪 DEBUG: Match {match_id} - minute: {minute}, state: {state}")
                    
                    # Monitor matches in FIRST HALF states from minute 20+ (to build momentum for 30-35 alerts)
                    if state in ['INPLAY_1ST_HALF', 'HT']:  # First half or halftime
                        if minute >= 20:  # Start monitoring from minute 20 to build momentum
                            eligible_matches.append(match)
                            if 30 <= minute <= 35:
                                self.logger.info(f"🏁 FIRST HALF: ✅ Alert Window: Match {match_id} at {minute}' ({state})")
                            else:
                                self.logger.info(f"🏁 FIRST HALF: 📊 Momentum Building: Match {match_id} at {minute}' ({state})")
                    
                except Exception as e:
                    self.logger.error(f"🏁 FIRST HALF: ❌ Error processing match during discovery: {e}")
                    continue
            
            if not eligible_matches:
                self.logger.info(f"🏁 FIRST HALF: No matches in 30-35 minute first half window (total live: {len(live_matches)})")
                return
            
            self.logger.info(f"🏁 FIRST HALF: 📊 MONITORING {len(eligible_matches)} first half matches")
            
            # Process each eligible match
            for match in eligible_matches:
                try:
                    match_stats = self._extract_match_stats(match)
                    if not match_stats:
                        continue
                    
                    fixture_id = match_stats['fixture_id']
                    minute = match_stats['minute']
                    
                    self.logger.info(f"🏁 FIRST HALF: 🔍 Analyzing {match_stats['home_team']} vs {match_stats['away_team']} ({minute}')")
                    
                    # Analyze first half opportunity
                    alert_result = await self._analyze_first_half_opportunity(match, match_stats)
                    
                    if alert_result:
                        self.logger.info(f"🏁 FIRST HALF: ✅ Alert generated for match {fixture_id}")
                    
                except Exception as e:
                    self.logger.error(f"🏁 FIRST HALF: ❌ Error processing match: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"🏁 FIRST HALF: ❌ Error in monitoring cycle: {e}")
            import traceback
            traceback.print_exc()
    
    async def run(self):
        """Main monitoring loop for first half system"""
        
        self.logger.info("🚀 FIRST HALF MONITOR STARTING...")
        self.logger.info("   Monitoring for 30-35 minute opportunities")
        self.logger.info("   Target: Market ID 63 '1st Half Asian Corners'")
        self.logger.info("   Psychology: Halftime Panic + Giant Killer systems")
        
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                start_time = time.time()
                
                self.logger.debug(f"🔄 FIRST HALF: Cycle {cycle_count} starting...")
                
                # Run monitoring cycle
                await self.run_monitoring_cycle()
                
                # Calculate cycle time
                cycle_time = time.time() - start_time
                self.logger.debug(f"⏱️ FIRST HALF: Cycle {cycle_count} completed in {cycle_time:.2f}s")
                
                # Wait before next cycle (30 seconds)
                await asyncio.sleep(30)
                
            except KeyboardInterrupt:
                self.logger.info("🛑 FIRST HALF: Monitor stopped by user")
                break
            except Exception as e:
                self.logger.error(f"❌ FIRST HALF: Error in main loop: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(60)  # Wait longer on errors

async def main():
    """Entry point for first half monitoring system"""
    
    print("🏁 FIRST HALF ASIAN CORNER MONITORING SYSTEM")
    print("=" * 50)
    print("Target: Market ID 63 '1st Half Asian Corners'")
    print("Timing: 30-35 minutes (halftime urgency)")
    print("Psychology: Panic Favorites + Giant Killers")
    print("Standards: Same high quality as late corner system")
    print("=" * 50)
    
    # Initialize and run monitor
    monitor = FirstHalfMonitor()
    await monitor.run()

# Entry point for combined_runner.py
async def first_half_main():
    """Entry point for combined runner integration"""
    monitor = FirstHalfMonitor()
    await monitor.run()

if __name__ == "__main__":
    asyncio.run(main())