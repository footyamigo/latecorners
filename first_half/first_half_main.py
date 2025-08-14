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
from first_half_analyzer import FirstHalfAnalyzer
from first_half_telegram_system import FirstHalfTelegramSystem

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
    
    def _get_live_matches(self):
        """Get live matches from SportMonks API"""
        try:
            matches = self.api_client.get_live_matches(filter_by_minute=False)
            return matches or []
        except Exception as e:
            self.logger.error(f"Error fetching live matches: {e}")
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
        """Analyze first half corner opportunity for 30-35 minute alerts"""
        
        fixture_id = match_stats['fixture_id']
        minute = match_stats['minute']
        
        # 🚨 MANDATORY TIMING CHECK: Only proceed with alert analysis if in 30-35 minute window
        if not (30 <= minute <= 35):
            self.logger.info(f"⏰ FIRST HALF TIMING CHECK FAILED: Match at {minute}' (need 30-35 minutes) - SKIPPING ANALYSIS")
            # Still update momentum tracking for next cycle
            self.first_half_analyzer.add_match_snapshot(fixture_id, minute, match_stats)
            return None

        self.logger.info(f"✅ FIRST HALF TIMING CHECK PASSED: Match at {minute}' (within 30-35 minute window)")
        
        # Check if already alerted for this match in first half
        if fixture_id in self.first_half_alerted_matches:
            self.logger.info(f"📵 FIRST HALF: Already alerted on match {fixture_id} - skipping")
            return None
        
        try:
            # Add current snapshot to momentum tracker
            self.first_half_analyzer.add_match_snapshot(fixture_id, minute, match_stats)
            
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
        """Run a single monitoring cycle for first half opportunities"""
        
        try:
            # Get live matches
            live_matches = self._get_live_matches()
            
            if not live_matches:
                self.logger.debug("🏁 FIRST HALF: No live matches found")
                return
            
            # Filter for first half target matches (30-35 minutes)
            first_half_matches = [match for match in live_matches if self._is_first_half_target_match(match)]
            
            if not first_half_matches:
                self.logger.debug(f"🏁 FIRST HALF: No matches in 30-35 minute window (total live: {len(live_matches)})")
                return
            
            self.logger.info(f"🏁 FIRST HALF: Found {len(first_half_matches)} matches in 30-35 minute window")
            
            # Analyze each match
            for match in first_half_matches:
                try:
                    match_stats = self._extract_match_stats(match)
                    if not match_stats:
                        continue
                    
                    fixture_id = match_stats['fixture_id']
                    minute = match_stats['minute']
                    
                    self.logger.info(f"🔍 FIRST HALF: Analyzing {match_stats['home_team']} vs {match_stats['away_team']} ({minute}')")
                    
                    # Analyze first half opportunity
                    alert_result = await self._analyze_first_half_opportunity(match, match_stats)
                    
                    if alert_result:
                        self.logger.info(f"✅ FIRST HALF: Alert generated for match {fixture_id}")
                    
                except Exception as e:
                    self.logger.error(f"❌ FIRST HALF: Error processing match: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"❌ FIRST HALF: Error in monitoring cycle: {e}")
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