#!/usr/bin/env python3
"""
Test corner momentum and pattern detection system
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from latecorners.corner_momentum_system import CornerMomentumSystem
from latecorners.sportmonks_client import SportmonksClient
from latecorners.enhanced_match_tracker import EnhancedMatchTracker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_corner_momentum():
    """Test corner momentum system with live matches"""
    
    logger.info("🧪 TESTING CORNER MOMENTUM SYSTEM")
    
    # Initialize systems
    client = SportmonksClient()
    momentum_system = CornerMomentumSystem()
    
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
                
            # Get enhanced stats from tracker
            tracker.update_stats({
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
                'crosses': match_stats.crosses_total,
                
                # Possession and control
                'possession': match_stats.possession,
                'territory': {'home': 0, 'away': 0},  # Would need to calculate from stats
                'successful_dribbles': match_stats.successful_dribbles,
                'key_passes': match_stats.key_passes
            })
            
            # Get last 5 minutes stats
            recent_stats = tracker.get_window_stats(5)
            if not recent_stats:
                continue
            
            # Add territory estimation (from possession and successful actions)
            for team in ['home', 'away']:
                possession = recent_stats['possession'][team]
                dribbles = recent_stats['successful_dribbles'][team]
                attacks = recent_stats['attacks'][team]
                
                # Estimate territory control (0-100)
                territory = min(100, (
                    possession * 0.5 +
                    dribbles * 5 +
                    attacks * 2
                ))
                recent_stats['territory'][team] = territory
            
            # Analyze with momentum system
            logger.info(f"\n🎯 Match {fixture_id} ({match_stats.home_team} vs {match_stats.away_team})")
            logger.info(f"   Current minute: {match_stats.minute}")
            
            # 1. Calculate momentum
            momentum = momentum_system.calculate_momentum(recent_stats)
            
            logger.info("\n   🔄 MOMENTUM INDICATORS:")
            for team in ['home', 'away']:
                logger.info(f"\n      {team.upper()}:")
                logger.info(f"      Attack Momentum:    {momentum[team].attack_momentum:6.1f}")
                logger.info(f"      Territory Momentum: {momentum[team].territory_momentum:6.1f}")
                logger.info(f"      Pressure Momentum:  {momentum[team].pressure_momentum:6.1f}")
                logger.info(f"      Overall Momentum:   {momentum[team].overall_momentum:6.1f}")
            
            # 2. Detect patterns
            patterns = momentum_system.detect_patterns(recent_stats)
            
            logger.info("\n   🎯 DETECTED PATTERNS:")
            for team in ['home', 'away']:
                logger.info(f"\n      {team.upper()}:")
                if patterns[team]:
                    for pattern in patterns[team]:
                        logger.info(f"      • {pattern.name} (Weight: {pattern.weight})")
                else:
                    logger.info("      • No patterns detected")
            
            # 3. Calculate corner probability
            probabilities = momentum_system.calculate_corner_probability(recent_stats)
            
            logger.info("\n   📊 CORNER PROBABILITIES:")
            for team in ['home', 'away']:
                prob = probabilities[team]
                logger.info(f"\n      {team.upper()}:")
                logger.info(f"      Total Probability:     {prob['total_probability']:6.1f}%")
                logger.info(f"      Momentum Contribution: {prob['momentum_contribution']:6.1f}%")
                logger.info(f"      Pattern Contribution: {prob['pattern_contribution']:6.1f}%")
            
            # 4. Check if should alert
            alerts = momentum_system.should_alert(recent_stats)
            
            logger.info("\n   🚨 ALERT STATUS:")
            for team in ['home', 'away']:
                status = "ALERT!" if alerts[team] else "No alert"
                logger.info(f"      {team.upper()}: {status}")
        
        # Wait between updates
        import time
        time.sleep(5)
    
    logger.info("\n✅ Corner momentum test complete!")

def main():
    """Main entry point"""
    try:
        test_corner_momentum()
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()