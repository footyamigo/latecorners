#!/usr/bin/env python3
"""
Test reliable corner prediction system
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from latecorners.reliable_corner_system import ReliableCornerSystem
from latecorners.sportmonks_client import SportmonksClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_reliable_system():
    """Test reliable corner prediction system"""
    
    logger.info("🧪 TESTING RELIABLE CORNER SYSTEM")
    
    # Initialize systems
    client = SportmonksClient()
    corner_system = ReliableCornerSystem()
    
    # Get live matches
    live_matches = client.get_live_matches()
    
    if not live_matches:
        logger.warning("⚠️ No live matches found")
        return
        
    # Track previous stats for each match
    previous_stats = {}
    
    logger.info(f"📊 Monitoring {len(live_matches)} live matches")
    
    # Simulate monitoring loop
    for i in range(3):  # Test 3 updates
        logger.info(f"\n📡 UPDATE {i+1}")
        
        for match in live_matches:
            fixture_id = match['id']
            
            # Get latest match stats
            match_stats = client.get_fixture_stats(fixture_id)
            if not match_stats:
                continue
            
            # Extract reliable stats only
            current_stats = {
                'shots_on_target': match_stats.shots_on_target,
                'shots_off_target': match_stats.shots_off_target,
                'shots_total': match_stats.shots_total,
                'dangerous_attacks': match_stats.dangerous_attacks,
                'attacks': match_stats.attacks,
                'possession': match_stats.possession,
                'total_corners': match_stats.total_corners,  # Added corners
                'minute': match_stats.minute,
                'score_diff': match_stats.home_score - match_stats.away_score,  # For home team
                'is_home': True,  # This will be flipped for away team
                'has_live_asian_corners': True,  # For testing - in real system this comes from odds data
                'corners_last_15': 3  # For testing - in real system this is calculated
            }
            
            # Initialize previous stats if needed
            if fixture_id not in previous_stats:
                previous_stats[fixture_id] = current_stats
                continue
            
            # Calculate time passed (use 5 minutes for testing)
            minutes_passed = 5
            
            # Analyze with corner system
            logger.info(f"\n🎯 Match {fixture_id} ({match_stats.home_team} vs {match_stats.away_team})")
            logger.info(f"   Current minute: {match_stats.minute}")
            
            # 1. Calculate momentum
            momentum = corner_system.calculate_momentum(
                current_stats, previous_stats[fixture_id], minutes_passed
            )
            
            logger.info("\n   🔄 MOMENTUM INDICATORS:")
            for team in ['home', 'away']:
                logger.info(f"\n      {team.upper()}:")
                logger.info(f"      Attack Intensity:  {momentum[team].attack_intensity:6.1f}")
                logger.info(f"      Shot Efficiency:   {momentum[team].shot_efficiency:6.1f}")
                logger.info(f"      Attack Volume:     {momentum[team].attack_volume:6.1f}")
                logger.info(f"      Overall Momentum:  {momentum[team].overall_momentum:6.1f}")
            
            # 2. Calculate differences and detect patterns
            diff_stats = corner_system.calculate_stats_differences(
                current_stats, previous_stats[fixture_id], 5
            )
            patterns = corner_system.detect_patterns(diff_stats)
            
            logger.info("\n   🎯 DETECTED PATTERNS:")
            for team in ['home', 'away']:
                logger.info(f"\n      {team.upper()}:")
                if patterns[team]:
                    for pattern in patterns[team]:
                        logger.info(f"      • {pattern.name} (Weight: {pattern.weight})")
                else:
                    logger.info("      • No patterns detected")
            
            # 3. Calculate corner probability
            probabilities = corner_system.calculate_corner_probability(
                current_stats, previous_stats[fixture_id], minutes_passed
            )
            
            logger.info("\n   📊 CORNER PROBABILITIES:")
            for team in ['home', 'away']:
                prob = probabilities[team]
                logger.info(f"\n      {team.upper()}:")
                logger.info(f"      Total Probability:     {prob['total_probability']:6.1f}%")
                logger.info(f"      Momentum Contribution: {prob['momentum_contribution']:6.1f}%")
                logger.info(f"      Pattern Contribution: {prob['pattern_contribution']:6.1f}%")
            
            # 4. Check if should alert
            alerts = corner_system.should_alert(
                current_stats, previous_stats[fixture_id], minutes_passed
            )
            
            logger.info("\n   🚨 ALERT STATUS:")
            for team in ['home', 'away']:
                status = "ALERT!" if alerts[team] else "No alert"
                logger.info(f"      {team.upper()}: {status}")
            
            # Update previous stats
            previous_stats[fixture_id] = current_stats
        
        # Wait between updates
        import time
        time.sleep(5)
    
    logger.info("\n✅ Reliable system test complete!")

def main():
    """Main entry point"""
    try:
        test_reliable_system()
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()