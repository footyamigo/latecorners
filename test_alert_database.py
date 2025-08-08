#!/usr/bin/env python3
"""
Test alert database integration
"""

import logging
from typing import Dict
from alert_tracker import track_elite_alert
# Legacy reliable system removed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_test_match_data() -> Dict:
    """Create test match data"""
    return {
        'fixture_id': 12345,
        'home_team': 'Test Home',
        'away_team': 'Test Away',
        'home_score': 1,
        'away_score': 1,
        'minute': 87,
        'total_corners': 8,
        'corners_last_15': 3,
        'dangerous_attacks_last_5': 8,
        'attacks_last_5': 12,
        'home_shots_on_target': 3,
        'away_shots_on_target': 2,
        'active_odds': ['Over 9.5 = 1.95', 'Under 9.5 = 1.85'],
        'has_live_asian_corners': True
    }

def test_database_integration():
    """Test saving alerts with new metrics"""
    
    logger.info("\n🧪 TESTING DATABASE INTEGRATION")
    logger.info("----------------------------------------")
    
    # Create test data
    match_data = create_test_match_data()
    
    # Create momentum indicators
    momentum_indicators = {
        'attack_intensity': 75.5,
        'shot_efficiency': 66.7,
        'attack_volume': 80.0,
        'corner_momentum': 70.0,
        'score_context': 85.0,
        'overall': 82.5
    }
    
    # Create detected patterns
    detected_patterns = [
        {'name': 'Tight Game Push', 'weight': 3.0},
        {'name': 'Corner Cluster', 'weight': 2.7},
        {'name': 'Attack Pressure', 'weight': 2.0}
    ]
    
    # Test saving alert
    logger.info("\n📝 Saving test alert with new metrics...")
    
    success = track_elite_alert(
        match_data=match_data,
        tier="TIER_1",
        score=82.5,  # Total probability
        conditions=["High attack intensity", "Multiple corners recent", "Good shot accuracy"],
        momentum_indicators=momentum_indicators,
        detected_patterns=detected_patterns
    )
    
    if success:
        logger.info("✅ Alert saved successfully with new metrics!")
    else:
        logger.error("❌ Failed to save alert!")

def main():
    """Main entry point"""
    try:
        test_database_integration()
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()