#!/usr/bin/env python3
"""
Test enhanced match tracking with derived metrics
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from latecorners.enhanced_match_tracker import EnhancedMatchTracker
from latecorners.sportmonks_client import SportmonksClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_enhanced_tracking():
    """Test enhanced match tracking with derived metrics"""
    
    logger.info("🧪 TESTING ENHANCED MATCH TRACKING")
    
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
        trackers[fixture_id] = EnhancedMatchTracker(fixture_id)
        
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
                # Basic stats
                'shots_on_target': match_stats.shots_on_target,
                'shots_off_target': match_stats.shots_off_target,
                'shots_total': match_stats.shots_total,
                'shots_blocked': match_stats.shots_blocked,
                'shots_inside_box': match_stats.shots_inside_box,
                'shots_outside_box': match_stats.shots_outside_box,
                
                # Attack indicators
                'dangerous_attacks': match_stats.dangerous_attacks,
                'attacks': match_stats.attacks,
                'counter_attacks': match_stats.counter_attacks,
                'big_chances_created': match_stats.big_chances_created,
                'big_chances_missed': match_stats.big_chances_missed,
                
                # Possession and control
                'possession': match_stats.possession,
                'crosses_total': match_stats.crosses_total,
                'key_passes': match_stats.key_passes,
                'successful_dribbles': match_stats.successful_dribbles,
                
                # Set pieces
                'corners': {'home': 0, 'away': 0},  # Total corners handled differently
                'free_kicks': match_stats.free_kicks,
                'throwins': match_stats.throwins,
                
                # Additional
                'passes': match_stats.passes,
                'pass_accuracy': match_stats.pass_accuracy
            }
            
            # Update tracker
            tracker.update_stats(current_stats)
            
            # Get comprehensive analysis
            logger.info(f"\n🎯 Match {fixture_id} ({match_stats.home_team} vs {match_stats.away_team})")
            logger.info(f"   Current minute: {match_stats.minute}")
            
            # 1. Get stats for different windows
            for window_size in [5, 10, 15]:
                stats = tracker.get_window_stats(window_size)
                if not stats:
                    continue
                    
                logger.info(f"\n   📊 Last {window_size} minutes:")
                
                # Show key stats
                key_stats = [
                    'dangerous_attacks', 'shots_on_target', 'shots_inside_box',
                    'crosses_total', 'possession'
                ]
                
                for stat in key_stats:
                    values = stats[stat]
                    logger.info(f"      {stat:20} Home: {values['home']:6.1f} Away: {values['away']:6.1f}")
                
                # Show derived metrics
                derived_metrics = [
                    'dangerous_attack_ratio', 'shots_on_target_ratio',
                    'shots_inside_box_ratio', 'crosses_per_attack'
                ]
                
                logger.info("\n      Derived Metrics:")
                for metric in derived_metrics:
                    values = stats[metric]
                    logger.info(f"      {metric:20} Home: {values['home']:6.1f}% Away: {values['away']:6.1f}%")
            
            # 2. Get attack momentum (last 5 minutes)
            momentum = tracker.get_attack_momentum(5)
            logger.info("\n   🔄 Attack Momentum (last 5 mins):")
            logger.info(f"      Home: {momentum['home']:6.1f}")
            logger.info(f"      Away: {momentum['away']:6.1f}")
            
            # 3. Get corner probability factors
            factors = tracker.get_corner_probability_factors(5)
            logger.info("\n   🎯 Corner Probability Factors (last 5 mins):")
            for team in ['home', 'away']:
                logger.info(f"\n      {team.upper()}:")
                for factor, value in factors[team].items():
                    logger.info(f"      {factor:25} {value:6.1f}")
        
        # Wait between updates (5 seconds for testing)
        import time
        time.sleep(5)
    
    logger.info("\n✅ Enhanced tracking test complete!")

def main():
    """Main entry point"""
    try:
        test_enhanced_tracking()
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()