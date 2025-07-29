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
        self.alerted_matches: Set[int] = set()  # Elite alerts sent
        self.relaxed_alerted_matches: Set[int] = set()  # Relaxed alerts sent
        
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
        """Discover new live matches to monitor (NO FILTERING - DEBUG MODE)"""
        self.logger.info("🚨 DISCOVERING new live matches (NO FILTERING)...")
        try:
            all_live_matches = self.sportmonks_client.get_live_matches(filter_by_minute=False)
            self.logger.info(f"🚨 DISCOVERY: Found {len(all_live_matches)} total live matches from API")
            new_matches_count = 0
            for match in all_live_matches:
                fixture_id = match['id']
                minute = match.get('minute', 0)
                state = match.get('state', {}).get('developer_name', '')
                state_full = match.get('state', {}).get('name', 'Unknown')
                self.logger.info(f"🚨 FORCED MONITOR: Adding match {fixture_id} (minute:{minute}, state:'{state}'/'{state_full}') to monitored_matches")
                if fixture_id not in self.monitored_matches:
                    self.monitored_matches.add(fixture_id)
                    new_matches_count += 1
            if new_matches_count > 0:
                self.logger.info(f"🚨 FORCED: Added {new_matches_count} new matches to monitoring (NO FILTERING)")
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
        """Monitor a single match for corner opportunities using the WORKING livescores/inplay endpoint"""
        
        # 🎯 FIX: Use the SAME endpoint as dashboard (livescores/inplay) instead of individual fixtures
        try:
            # Get ALL live matches from the working endpoint
            live_matches = self.sportmonks_client.get_live_matches(filter_by_minute=False)
            
            # Find our specific match in the live feed
            match_data = None
            for match in live_matches:
                if match['id'] == fixture_id:
                    match_data = match
                    break
            
            if not match_data:
                self.logger.warning(f"🧪 WARNING: Match {fixture_id} not found in live feed - may have finished")
                # Remove from monitoring if not in live feed
                self.monitored_matches.discard(fixture_id)
                return
            
            # Extract match stats from live feed data (same as dashboard)
            match_stats = self.sportmonks_client._parse_live_match_data(match_data)
            if not match_stats:
                self.logger.warning(f"WARNING: Could not parse stats for match {fixture_id}")
                return
                
            self.logger.info(f"🧪 DEBUG: Live feed stats for match {fixture_id}: minute={match_stats.minute}, state={match_stats.state}")
            
        except Exception as e:
            self.logger.error(f"🧪 ERROR: Failed to get live feed data for match {fixture_id}: {e}")
            return
        
        # Check if match is finished
        if match_stats.minute >= 100 or getattr(match_stats, 'state', '') == 'FT':
            self.monitored_matches.discard(fixture_id)
            self.logger.info(f"FINISHED: Match {fixture_id} finished (minute={match_stats.minute}, state={getattr(match_stats, 'state', '')}), removing from monitoring")
            return
            
        # Check for ELITE alerts first (priority)
        elite_result = self.scoring_engine.evaluate_match(match_stats)
        if elite_result and fixture_id not in self.alerted_matches:
            # Check for live odds
            corner_odds = self.sportmonks_client.get_live_corner_odds(fixture_id)
            if not corner_odds:
                self.logger.info(f"🧪 DEBUG: No live odds for match {fixture_id}, skipping ELITE alert.")
            else:
                self.logger.info(f"🚨 ELITE ALERT: 85th MINUTE CORNER ALERT triggered for match {fixture_id}! Minute: {match_stats.minute}' | Score: {elite_result.total_score:.1f} | High-priority: {self.scoring_engine._count_high_priority_indicators(elite_result)} | Odds: {corner_odds}")
                self.alerted_matches.add(fixture_id)
                match_info = self._extract_match_info(match_stats)
                await self.telegram_notifier.send_corner_alert(elite_result, match_info, corner_odds)
                return  # Don't check relaxed if elite was sent
        
        # Check for RELAXED alerts (only if no elite alert was sent)
        if fixture_id not in self.alerted_matches and fixture_id not in self.relaxed_alerted_matches:
            relaxed_result = self.scoring_engine.evaluate_match_relaxed(match_stats)
            if relaxed_result:
                # Check for live odds
                corner_odds = self.sportmonks_client.get_live_corner_odds(fixture_id)
                if not corner_odds:
                    self.logger.info(f"🧪 DEBUG: No live odds for match {fixture_id}, skipping RELAXED alert.")
                else:
                    self.logger.info(f"🟡 RELAXED ALERT: 85th MINUTE CORNER ALERT triggered for match {fixture_id}! Minute: {match_stats.minute}' | Score: {relaxed_result.total_score:.1f} | High-priority: {self.scoring_engine._count_high_priority_indicators(relaxed_result)} | Odds: {corner_odds}")
                    self.relaxed_alerted_matches.add(fixture_id)
                    match_info = self._extract_match_info(match_stats)
                    await self.telegram_notifier.send_corner_alert(relaxed_result, match_info, corner_odds)
        
        # Debug logging
        if elite_result and fixture_id in self.alerted_matches:
            self.logger.info(f"🧪 DEBUG: Match {fixture_id} meets ELITE conditions but already alerted.")
        elif not elite_result:
            self.logger.info(f"🧪 DEBUG: Match {fixture_id} does not meet ELITE conditions at minute {match_stats.minute}.")
    
    def _extract_match_info(self, match_stats) -> Dict:
        """Extract match information for alert formatting (FIXED: use team names)"""
        self.logger.info(f"🧪 DEBUG: Extracting match info for alert (fixture_id={match_stats.fixture_id})")
        match_info = {
            'home_team': getattr(match_stats, 'home_team', 'Unknown'),  # Use name, not ID
            'away_team': getattr(match_stats, 'away_team', 'Unknown'),  # Use name, not ID
            'league': 'Live Match',  # Would be actual league name
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
    
    def _cleanup_finished_matches(self):
        """Remove finished matches from tracking"""
        
        # Clean up alerted matches older than 4 hours
        # (This is a simple time-based cleanup - in production you'd track match end times)
        if len(self.alerted_matches) > 50:  # Simple size-based cleanup
            # Keep only the most recent 30 alerts
            self.alerted_matches = set(list(self.alerted_matches)[-30:])
            self.logger.info("CLEANUP: Cleaned up old ELITE alert tracking")
            
        if len(self.relaxed_alerted_matches) > 50:  # Simple size-based cleanup
            # Keep only the most recent 30 alerts
            self.relaxed_alerted_matches = set(list(self.relaxed_alerted_matches)[-30:])
            self.logger.info("CLEANUP: Cleaned up old RELAXED alert tracking")

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
