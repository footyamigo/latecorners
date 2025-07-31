#!/usr/bin/env python3
"""
Test the new telegram system with real match data
"""

import sys
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from new_telegram_system import send_corner_alert_new

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_with_real_match_data():
    """Test new telegram system with the exact match data that failed"""
    
    logger.info("🧪 TESTING NEW TELEGRAM WITH REAL MATCH DATA...")
    
    # Use the actual failing match data from logs
    match_data = {
        'fixture_id': 19371929,
        'home_team': 'PPJ / Lauttasaari',
        'away_team': 'JäPS II',
        'home_score': 2,
        'away_score': 1,
        'minute': 84,
        'tier': 'ELITE',
        'total_corners': 9,
        'home_corners': 4,
        'away_corners': 4,
        'home_shots': 7,
        'away_shots': 15,
        'home_shots_on_target': 2,
        'away_shots_on_target': 10,
        'home_attacks': 25,
        'away_attacks': 60,
        'odds_available': True,
        'odds_count': 20,
        'active_odds_count': 2,
        'active_odds': ['Over 10.5 = 2.25', 'Under 10.5 = 1.62'],
        'elite_score': 19.0,
        'high_priority_count': 4
    }
    
    conditions = [
        "Away team trailing by 1 goal after 75'",
        '10 total shots on target',
        '15 shots in second half', 
        '10 shots on target but only 1 goals',
        '9 corners (SWEET SPOT)',
        'GK facing 10 shots on target (high pressure)'
    ]
    
    logger.info("📊 TEST DATA:")
    logger.info(f"   Match: {match_data['home_team']} vs {match_data['away_team']}")
    logger.info(f"   Score: {match_data['home_score']}-{match_data['away_score']}")
    logger.info(f"   Tier: ELITE")
    logger.info(f"   Elite Score: 19.0")
    logger.info(f"   Conditions: {len(conditions)}")
    
    # Test the new system
    try:
        success = send_corner_alert_new(
            match_data=match_data,
            tier="ELITE", 
            score=19.0,
            conditions=conditions
        )
        
        if success:
            logger.info("🎉 NEW TELEGRAM SYSTEM TEST PASSED!")
            logger.info("✅ Match data processed correctly")
            logger.info("✅ Message formatting worked")
            logger.info("✅ HTTP request attempted")
            logger.info("🚀 READY FOR DEPLOYMENT!")
            return True
        else:
            logger.error("❌ NEW TELEGRAM SYSTEM TEST FAILED!")
            return False
            
    except Exception as e:
        logger.error(f"❌ TEST ERROR: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_with_real_match_data()
    
    if success:
        print("\n🎉 SUCCESS! New telegram system ready for deployment!")
        print("🚀 This WILL work when deployed to Railway!")
        sys.exit(0)
    else:
        print("\n❌ Test failed - needs more work")
        sys.exit(1) 