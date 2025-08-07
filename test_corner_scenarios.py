#!/usr/bin/env python3
"""
Test different corner prediction scenarios
"""

import logging
from typing import Dict
from reliable_corner_system import ReliableCornerSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_test_stats(
    minute: int,
    score_home: int,
    score_away: int,
    attacks: Dict[str, int],
    dangerous_attacks: Dict[str, int],
    shots: Dict[str, int],
    shots_on_target: Dict[str, int],
    total_corners: int,
    corners_last_15: int,
    has_odds: bool = True,
    is_home: bool = True
) -> Dict:
    """Create test match stats"""
    return {
        'minute': minute,
        'score_diff': score_home - score_away if is_home else score_away - score_home,
        'is_home': is_home,
        'has_live_asian_corners': has_odds,
        'attacks': attacks,
        'dangerous_attacks': dangerous_attacks,
        'shots_total': shots,
        'shots_on_target': shots_on_target,
        'total_corners': total_corners,
        'corners_last_15': corners_last_15,
        'possession': {'home': 55, 'away': 45}  # Default possession
    }

def test_scenarios():
    """Test various corner prediction scenarios"""
    
    system = ReliableCornerSystem()
    
    # Test Scenario 1: Perfect Scenario (Should Alert)
    logger.info("\n🧪 TEST SCENARIO 1: Perfect Late Game Scenario")
    logger.info("----------------------------------------")
    
    current_stats = create_test_stats(
        minute=87,
        score_home=1,
        score_away=1,
        attacks={'home': 65, 'away': 58},
        dangerous_attacks={'home': 45, 'away': 35},
        shots={'home': 12, 'away': 10},
        shots_on_target={'home': 6, 'away': 4},
        total_corners=8,
        corners_last_15=3,
        has_odds=True
    )
    
    # Create previous stats (5 minutes ago)
    previous_stats = create_test_stats(
        minute=82,
        score_home=1,
        score_away=1,
        attacks={'home': 55, 'away': 50},
        dangerous_attacks={'home': 38, 'away': 30},
        shots={'home': 10, 'away': 8},
        shots_on_target={'home': 5, 'away': 3},
        total_corners=5,
        corners_last_15=2
    )
    
    result = system.should_alert(current_stats, previous_stats, 5)
    
    logger.info("\nALERT DECISION SUMMARY:")
    for team in ['home', 'away']:
        logger.info(f"\n{team.upper()} TEAM:")
        logger.info(f"Alert: {'🎯 YES' if result[team]['alert'] else '❌ NO'}")
        logger.info("\nReasons:")
        for reason in result[team]['reasons']:
            logger.info(f"• {reason}")
        
        metrics = result[team]['metrics']
        if metrics:
            logger.info("\nMetrics:")
            logger.info(f"• Total Probability: {metrics['total_probability']:.1f}%")
            logger.info(f"• Attack Intensity: {metrics['attack_intensity']:.1f}")
            logger.info(f"• Corner Momentum: {metrics['corner_momentum']:.1f}")
            logger.info(f"• Patterns Found: {metrics['patterns_count']}")
            if metrics['patterns_count'] > 0:
                logger.info(f"• Strongest Pattern Weight: {metrics['strongest_pattern_weight']:.1f}")
    
    logger.info("\nExpected: Should alert for home team")
    
    # Test Scenario 2: Wrong Timing (Should Not Alert)
    logger.info("\n🧪 TEST SCENARIO 2: Wrong Timing")
    logger.info("----------------------------------------")
    
    current_stats['minute'] = 82  # Too early
    alerts = system.should_alert(current_stats, previous_stats, 5)
    logger.info(f"Wrong Timing Alert Status: {alerts}")
    logger.info(f"Expected: Should not alert (too early)")
    
    # Test Scenario 3: No Odds Available (Should Not Alert)
    logger.info("\n🧪 TEST SCENARIO 3: No Odds Available")
    logger.info("----------------------------------------")
    
    current_stats['minute'] = 87  # Fix timing
    current_stats['has_live_asian_corners'] = False
    alerts = system.should_alert(current_stats, previous_stats, 5)
    logger.info(f"No Odds Alert Status: {alerts}")
    logger.info(f"Expected: Should not alert (no odds)")
    
    # Test Scenario 4: Not Tight Game (Should Not Alert)
    logger.info("\n🧪 TEST SCENARIO 4: Not Tight Game")
    logger.info("----------------------------------------")
    
    current_stats['has_live_asian_corners'] = True
    current_stats['score_diff'] = 3  # 3-0 score
    alerts = system.should_alert(current_stats, previous_stats, 5)
    logger.info(f"Not Tight Game Alert Status: {alerts}")
    logger.info(f"Expected: Should not alert (score difference too high)")
    
    # Test Scenario 5: Low Activity (Should Not Alert)
    logger.info("\n🧪 TEST SCENARIO 5: Low Activity")
    logger.info("----------------------------------------")
    
    current_stats['score_diff'] = 0  # Fix score
    current_stats['attacks'] = {'home': 45, 'away': 40}
    current_stats['dangerous_attacks'] = {'home': 20, 'away': 18}
    alerts = system.should_alert(current_stats, previous_stats, 5)
    logger.info(f"Low Activity Alert Status: {alerts}")
    logger.info(f"Expected: Should not alert (insufficient activity)")
    
    # Test Scenario 6: Perfect Away Team Scenario (Should Alert)
    logger.info("\n🧪 TEST SCENARIO 6: Perfect Away Team Scenario")
    logger.info("----------------------------------------")
    
    away_current_stats = create_test_stats(
        minute=88,
        score_home=0,
        score_away=1,
        attacks={'home': 50, 'away': 65},
        dangerous_attacks={'home': 30, 'away': 45},
        shots={'home': 8, 'away': 12},
        shots_on_target={'home': 3, 'away': 6},
        total_corners=9,
        corners_last_15=4,
        is_home=False
    )
    
    away_previous_stats = create_test_stats(
        minute=83,
        score_home=0,
        score_away=1,
        attacks={'home': 45, 'away': 55},
        dangerous_attacks={'home': 25, 'away': 38},
        shots={'home': 7, 'away': 10},
        shots_on_target={'home': 2, 'away': 5},
        total_corners=6,
        corners_last_15=3,
        is_home=False
    )
    
    alerts = system.should_alert(away_current_stats, away_previous_stats, 5)
    logger.info(f"Away Team Perfect Scenario Alert Status: {alerts}")
    logger.info(f"Expected: Should alert for away team")
    
    # Test Scenario 7: Late Equalizer Effect (Should Alert)
    logger.info("\n🧪 TEST SCENARIO 7: Late Equalizer Effect")
    logger.info("----------------------------------------")
    
    # Team just equalized, high momentum
    equalizer_current_stats = create_test_stats(
        minute=86,
        score_home=1,
        score_away=1,  # Just equalized
        attacks={'home': 70, 'away': 55},
        dangerous_attacks={'home': 48, 'away': 35},
        shots={'home': 14, 'away': 9},
        shots_on_target={'home': 7, 'away': 4},
        total_corners=10,
        corners_last_15=4
    )
    
    equalizer_previous_stats = create_test_stats(
        minute=81,
        score_home=0,
        score_away=1,  # Was losing before
        attacks={'home': 58, 'away': 50},
        dangerous_attacks={'home': 40, 'away': 32},
        shots={'home': 11, 'away': 8},
        shots_on_target={'home': 5, 'away': 4},
        total_corners=7,
        corners_last_15=3
    )
    
    alerts = system.should_alert(equalizer_current_stats, equalizer_previous_stats, 5)
    logger.info(f"Late Equalizer Effect Alert Status: {alerts}")
    logger.info(f"Expected: Should alert (high momentum after equalizer)")

def main():
    """Main entry point"""
    try:
        test_scenarios()
        logger.info("\n✅ All test scenarios completed!")
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()