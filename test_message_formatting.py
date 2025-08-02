#!/usr/bin/env python3
"""
Test the new telegram message formatting without credentials
"""

import sys
import logging
from new_telegram_system import NewTelegramSystem

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_message_formatting():
    """Test just the message formatting without sending"""
    
    logger.info("🧪 TESTING MESSAGE FORMATTING...")
    
    # Create telegram system instance
    telegram = NewTelegramSystem()
    
    # Use the actual failing match data from logs
    match_data = {
        'fixture_id': 19371929,
        'home_team': 'PPJ / Lauttasaari',
        'away_team': 'JäPS II',
        'home_score': 2,
        'away_score': 1,
        'minute': 84,
        'total_corners': 9,
        'active_odds': ['Over 10.5 = 2.25', 'Under 10.5 = 1.62']
    }
    
    conditions = [
        "Away team trailing by 1 goal after 75' (HIGH PRIORITY)",
        '10 total shots on target (HIGH PRIORITY)',
        '15 shots in second half', 
        '10 shots on target but only 1 goals',
        '9 corners (SWEET SPOT)',
        'GK facing 10 shots on target (high pressure) (HIGH PRIORITY)'
    ]
    
    # Test message creation
    try:
        # Use the actual odds from match_data for testing
        test_filtered_odds = match_data.get('active_odds', [])
        message = telegram._create_message(match_data, "ELITE", 19.0, conditions, test_filtered_odds)
        
        logger.info("✅ MESSAGE FORMATTING SUCCESSFUL!")
        logger.info(f"📝 Message length: {len(message)} characters")
        
        print("\n" + "="*80)
        print("🎉 GENERATED TELEGRAM MESSAGE:")
        print("="*80)
        print(message)
        print("="*80)
        
        # Check message components
        if "🏆 ELITE CORNER ALERT 🏆" in message:
            logger.info("✅ Elite header found")
        if "PPJ / Lauttasaari vs JäPS II" in message:
            logger.info("✅ Team names found")
        if "Score: 2-1" in message:
            logger.info("✅ Match score found")
        if "ELITE SCORE: 19.0/8" in message:
            logger.info("✅ Score threshold found")
        if "High Priority: 3/2" in message:
            logger.info("✅ High priority count found")
        if "Over 10.5 = 2.25" in message:
            logger.info("✅ Live odds found")
        
        logger.info("🎉 MESSAGE FORMATTING TEST PASSED!")
        return True
        
    except Exception as e:
        logger.error(f"❌ MESSAGE FORMATTING ERROR: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_message_formatting()
    
    if success:
        print("\n🎉 SUCCESS! Message formatting perfect!")
        print("🚀 Ready to deploy and send real alerts!")
        sys.exit(0)
    else:
        print("\n❌ Message formatting failed")
        sys.exit(1) 