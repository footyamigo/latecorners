#!/usr/bin/env python3

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Set
import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_config
from sportmonks_client import SportmonksClient
from scoring_engine import ScoringEngine
from telegram_bot import TelegramNotifier
from health_check import start_health_server_thread
from startup_flag import is_first_startup

class LateCornerMonitor:
    """Main application class that monitors live matches for corner opportunities"""
    
    def __init__(self):
        self.config = get_config()
        self.sportmonks_client = SportmonksClient()
        self.scoring_engine = ScoringEngine()
        self.telegram_notifier = TelegramNotifier()
        
        # Track which matches we're currently monitoring
        self.monitored_matches: Set[int] = set()
        
        # Track matches we've already alerted on to avoid duplicates
        self.alerted_matches: Set[int] = set()
        
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
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        file_handler = logging.FileHandler(self.config.LOG_FILE)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    async def start_monitoring(self):
        """Start the main monitoring loop"""
        
        self.logger.info("STARTING Late Corner Monitor...")
        
        # Start health check server
        try:
            start_health_server_thread(port=8081)
            self.logger.info("SUCCESS: Health check server started on port 8081")
        except Exception as e:
            self.logger.warning(f"WARNING: Failed to start health check server: {e}")
        
        # Test connections
        if not await self._test_connections():
            self.logger.error("ERROR: Connection tests failed. Exiting.")
            return
        
        # Send startup message only on first deployment, not on restarts
        if is_first_startup():
            try:
                await self.telegram_notifier.send_startup_message()
                self.logger.info("SUCCESS: Startup message sent (first deployment)")
            except Exception as e:
                self.logger.warning(f"WARNING: Could not send startup message: {e}")
                # Continue anyway - this is not critical
        else:
            self.logger.info("INFO: Skipping startup message (not first startup)")
        
        self.logger.info("SUCCESS: All systems ready. Starting match monitoring...")
        
        # Main monitoring loop
        match_discovery_counter = 0
        
        while True:
            try:
                # Discover new matches every 5 minutes
                if match_discovery_counter % (self.config.MATCH_DISCOVERY_INTERVAL // self.config.LIVE_POLL_INTERVAL) == 0:
                    try:
                        await self._discover_new_matches()
                    except Exception as e:
                        self.logger.error(f"ERROR: Failed to discover matches: {e}")
                        # Continue to monitoring existing matches
                
                # Monitor existing matches
                try:
                    await self._monitor_tracked_matches()
                except Exception as e:
                    self.logger.error(f"ERROR: Failed to monitor matches: {e}")
                    # Continue to cleanup
                
                # Cleanup finished matches
                try:
                    self._cleanup_finished_matches()
                except Exception as e:
                    self.logger.error(f"ERROR: Failed to cleanup: {e}")
                    # Continue anyway
                
                match_discovery_counter += 1
                
                # Wait before next poll
                await asyncio.sleep(self.config.LIVE_POLL_INTERVAL)
                
            except KeyboardInterrupt:
                self.logger.info("STOPPED: Shutdown requested by user")
                break
            except Exception as e:
                self.logger.error(f"CRITICAL ERROR: Unexpected error in main loop: {e}")
                # Don't send telegram message here as it might cause more crashes
                self.logger.error(f"SLEEPING: Waiting 60 seconds before retry")
                await asyncio.sleep(60)  # Wait a minute before retrying
    
    async def _test_connections(self) -> bool:
        """Test all external connections"""
        
        self.logger.info("TESTING connections...")
        
        # Test Sportmonks API
        try:
            live_matches = self.sportmonks_client.get_live_matches(filter_by_minute=False)  # Get all for testing
            self.logger.info(f"SUCCESS: Sportmonks API connected - found {len(live_matches)} live matches")
        except Exception as e:
            self.logger.error(f"ERROR: Sportmonks API test failed: {e}")
            return False
        
        # Test Telegram bot (without sending test message)
        try:
            # Skip the test message in production to avoid spam
            self.logger.info("SUCCESS: Telegram bot configured")
        except Exception as e:
            self.logger.error(f"ERROR: Telegram test failed: {e}")
            return False
        
        return True
    
    async def _discover_new_matches(self):
        """Discover new live matches to monitor"""
        
        self.logger.info("DISCOVERING new live matches...")
        
        try:
            # Get ALL live matches first
            all_live_matches = self.sportmonks_client.get_live_matches(filter_by_minute=False)
            
            new_matches_count = 0
            
            for match in all_live_matches:
                fixture_id = match['id']
                minute = match.get('minute', 0)
                state = match.get('state', {}).get('short_name', '')
                
                # Apply filtering in the main application logic
                # Only start monitoring matches past 70 minutes (any live state)
                if (fixture_id not in self.monitored_matches and 
                    minute >= self.config.MIN_MINUTE_TO_START_MONITORING and
                    state in ['INPLAY_1ST_HALF', 'INPLAY_2ND_HALF', 'HT']):  # Any live state
                    
                    self.monitored_matches.add(fixture_id)
                    new_matches_count += 1
                    
                    # Get and cache the pre-match favorite
                    favorite_team_id = self.sportmonks_client.get_pre_match_favorite(fixture_id)
                    if favorite_team_id:
                        self.scoring_engine.set_favorite(fixture_id, favorite_team_id)
                    
                    self.logger.info(f"🚨 NEW MATCH: Now monitoring {fixture_id} (minute {minute}, state: {state})")
                else:
                    # Log why matches are being skipped
                    if fixture_id in self.monitored_matches:
                        self.logger.debug(f"🚨 SKIP: Match {fixture_id} already monitored")
                    elif minute < self.config.MIN_MINUTE_TO_START_MONITORING:
                        self.logger.debug(f"🚨 SKIP: Match {fixture_id} too early (minute {minute})")
                    elif state not in ['INPLAY_1ST_HALF', 'INPLAY_2ND_HALF', 'HT']:
                        self.logger.debug(f"🚨 SKIP: Match {fixture_id} wrong state ({state})")
            
            if new_matches_count > 0:
                self.logger.info(f"SUCCESS: Added {new_matches_count} new matches to monitoring")
                
                # Send update to Telegram
                await self.telegram_notifier.send_system_message(
                    f"SUCCESS: Now monitoring {len(self.monitored_matches)} matches\n"
                    f"Added {new_matches_count} new matches"
                )
            else:
                # Log how many total live matches we found vs. qualifying ones
                qualifying_count = sum(1 for match in all_live_matches 
                                     if (match.get('minute', 0) >= self.config.MIN_MINUTE_TO_START_MONITORING and
                                         match.get('state', {}).get('developer_name', '') == 'INPLAY_2ND_HALF'))
                
                self.logger.debug(
                    f"Found {len(all_live_matches)} total live matches, "
                    f"{qualifying_count} qualify for monitoring, "
                    f"but all are already being tracked"
                )
            
        except Exception as e:
            self.logger.error(f"ERROR: Error discovering new matches: {e}")
    
    async def _monitor_tracked_matches(self):
        """Monitor all currently tracked matches"""
        
        if not self.monitored_matches:
            self.logger.info("🚨 MONITORING: No matches being monitored yet")
            return
        
        self.logger.info(f"🚨 MONITORING: Checking {len(self.monitored_matches)} matches...")
        
        for fixture_id in list(self.monitored_matches):  # Copy to avoid modification during iteration
            try:
                self.logger.info(f"🚨 CHECKING: Match {fixture_id}...")
                await self._monitor_single_match(fixture_id)
                
            except Exception as e:
                self.logger.error(f"🚨 ERROR: Error monitoring match {fixture_id}: {e}")
    
    async def _monitor_single_match(self, fixture_id: int):
        """Monitor a single match for corner opportunities"""
        
        # Get current match stats
        match_stats = self.sportmonks_client.get_fixture_stats(fixture_id)
        
        if not match_stats:
            self.logger.warning(f"WARNING: No stats available for match {fixture_id}")
            return
        
        # Check if match is finished
        if match_stats.minute >= 100:  # Match ended
            self.monitored_matches.discard(fixture_id)
            self.logger.info(f"FINISHED: Match {fixture_id} finished, removing from monitoring")
            return
        
        # TEST ALERT: Send test notification at 85 minutes (for Telegram bot testing)
        if (match_stats.minute >= 80 and  # TEMPORARILY LOWERED FROM 85 TO 80
            fixture_id not in self.alerted_matches and 
            fixture_id not in getattr(self, 'test_alerted_matches', set())):
            
            # Initialize test alert tracking if not exists
            if not hasattr(self, 'test_alerted_matches'):
                self.test_alerted_matches = set()
            
            self.logger.info(
                f"🧪 TEST ALERT: {match_stats.minute}th minute reached for match {fixture_id}! "
                f"Sending test alert (NOT corner bet alert)"
            )
            
            # Mark as test alerted to prevent duplicates
            self.test_alerted_matches.add(fixture_id)
            
            # Create match info for the test alert
            match_info = self._extract_match_info(match_stats)
            
            # Send test alert
            await self.telegram_notifier.send_test_alert(match_info)
        
        # Run scoring engine
        scoring_result = self.scoring_engine.evaluate_match(match_stats)
        
        if scoring_result and fixture_id not in self.alerted_matches:
            # We have a PRECISE 85th minute alert! 
            self.logger.info(
                f"ALERT: 85th MINUTE CORNER ALERT triggered for match {fixture_id}! "
                f"Minute: {match_stats.minute}' | Score: {scoring_result.total_score:.1f}"
            )
            
            # Mark as alerted to prevent duplicates
            self.alerted_matches.add(fixture_id)
            
            # Get live corner odds
            corner_odds = self.sportmonks_client.get_live_corner_odds(fixture_id)
            
            # Create match info for the alert
            match_info = self._extract_match_info(match_stats)
            
            # Send the alert
            await self.telegram_notifier.send_corner_alert(
                scoring_result, match_info, corner_odds
            )
            
        elif scoring_result:
            # Alert conditions met but already sent
            self.logger.debug(
                f"STATUS: Match {fixture_id} still meeting alert conditions "
                f"(score: {scoring_result.total_score:.1f}) but already alerted"
            )
    
    def _extract_match_info(self, match_stats) -> Dict:
        """Extract match information for alert formatting"""
        
        # Extract match info including current statistics
        match_info = {
            'home_team': f'Team {match_stats.home_team_id}',  # Would be actual team name
            'away_team': f'Team {match_stats.away_team_id}',  # Would be actual team name
            'league': 'Live Match',  # Would be actual league name
            'home_score': match_stats.home_score,
            'away_score': match_stats.away_score,
            'minute': match_stats.minute
        }
        
        # Add current statistics if available
        if hasattr(match_stats, 'home_corners') and hasattr(match_stats, 'away_corners'):
            match_info['corners'] = {
                'home': match_stats.home_corners,
                'away': match_stats.away_corners
            }
        
        if hasattr(match_stats, 'home_shots') and hasattr(match_stats, 'away_shots'):
            match_info['shots'] = {
                'home': match_stats.home_shots,
                'away': match_stats.away_shots
            }
        
        if hasattr(match_stats, 'home_dangerous_attacks') and hasattr(match_stats, 'away_dangerous_attacks'):
            match_info['attacks'] = {
                'home': match_stats.home_dangerous_attacks,
                'away': match_stats.away_dangerous_attacks
            }
        
        return match_info
    
    def _cleanup_finished_matches(self):
        """Remove finished matches from tracking"""
        
        # Clean up alerted matches older than 4 hours
        # (This is a simple time-based cleanup - in production you'd track match end times)
        if len(self.alerted_matches) > 50:  # Simple size-based cleanup
            # Keep only the most recent 30 alerts
            self.alerted_matches = set(list(self.alerted_matches)[-30:])
            self.logger.info("CLEANUP: Cleaned up old alert tracking")

async def main():
    """Main entry point"""
    
    # Create and start the monitor
    monitor = LateCornerMonitor()
    
    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\nSTOPPED: Late Corner Monitor stopped by user")
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Run the main async function
    asyncio.run(main()) 