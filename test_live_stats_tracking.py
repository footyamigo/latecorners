#!/usr/bin/env python3
"""
Test live statistics tracking with time windows
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from latecorners.match_state_tracker import MatchStateTracker
from latecorners.sportmonks_client import SportmonksClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_live_stats_tracking():
    """Test tracking live stats with time windows"""
    
    logger.info("🧪 TESTING LIVE STATS TRACKING")
    
    # Initialize clients
    client = SportmonksClient()
    
    # Get live matches
    live_matches = client.get_live_matches()
    
    if not live_matches:
        logger.warning("⚠️ No live matches found")
        return
        
    # Create trackers for each match
    trackers = {}
    for match in live_matches:
        fixture_id = match['id']
        trackers[fixture_id] = MatchStateTracker(fixture_id)
        
    logger.info(f"📊 Monitoring {len(trackers)} live matches")
    
    # Simulate monitoring loop
    for i in range(3):  # Test 3 updates
        logger.info(f"\n📡 UPDATE {i+1}")
        
        for fixture_id, tracker in trackers.items():
            # Get latest match stats
            match_stats = client.get_fixture_stats(fixture_id)
            if not match_stats:
                continue
                
            # Convert stats to our format
            current_stats = {
                'shots_on_target': match_stats.shots_on_target,
                'shots_off_target': match_stats.shots_off_target,
                'shots_total': match_stats.shots_total,
                'dangerous_attacks': match_stats.dangerous_attacks,
                'attacks': match_stats.attacks,
                'possession': match_stats.possession,
                'corners': {'home': 0, 'away': 0}  # Total corners handled differently
            }
            
            # Update tracker
            tracker.update_stats(current_stats)
            
            # Get stats for different windows
            all_windows = tracker.get_all_windows_stats()
            
            logger.info(f"\n🎯 Match {fixture_id} ({match_stats.home_team} vs {match_stats.away_team})")
            logger.info(f"   Current minute: {match_stats.minute}")
            
            for window_size, stats in all_windows.items():
                logger.info(f"\n   📊 Last {window_size} minutes:")
                
                for stat_name, values in stats.items():
                    if values['home'] > 0 or values['away'] > 0:  # Only show non-zero stats
                        logger.info(f"      {stat_name:20} Home: {values['home']:2} Away: {values['away']:2}")
        
        # Wait between updates (5 seconds for testing)
        import time
        time.sleep(5)
    
    logger.info("\n✅ Live stats tracking test complete!")

def main():
    """Main entry point"""
    try:
        test_live_stats_tracking()
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()