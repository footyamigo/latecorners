#!/usr/bin/env python3
"""
Check the last saved alert in the database
"""

import logging
from database import get_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_last_alert():
    """Check the most recently saved alert"""
    db = get_database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Get the most recent alert with all our new columns
        cursor.execute("""
            SELECT 
                fixture_id,
                teams,
                score_at_alert,
                minute_sent,
                corners_at_alert,
                total_probability,
                attack_intensity,
                shot_efficiency,
                attack_volume,
                corner_momentum,
                score_context,
                detected_patterns,
                corners_last_15,
                dangerous_attacks_last_5,
                attacks_last_5
            FROM alerts 
            ORDER BY id DESC 
            LIMIT 1
        """)
        
        alert = cursor.fetchone()
        
        if alert:
            logger.info("\n📊 LAST SAVED ALERT:")
            logger.info(f"   Match: {alert[1]}")  # teams
            logger.info(f"   Score: {alert[2]} | Minute: {alert[3]}")
            logger.info(f"   Corners: {alert[4]}")
            logger.info("\n   METRICS:")
            logger.info(f"   • Total Probability: {alert[5]:.1f}")
            logger.info(f"   • Attack Intensity: {alert[6]:.1f}")
            logger.info(f"   • Shot Efficiency: {alert[7]:.1f}")
            logger.info(f"   • Attack Volume: {alert[8]:.1f}")
            logger.info(f"   • Corner Momentum: {alert[9]:.1f}")
            logger.info(f"   • Score Context: {alert[10]:.1f}")
            logger.info(f"\n   PATTERNS: {alert[11]}")
            logger.info("\n   RECENT STATS:")
            logger.info(f"   • Corners (15'): {alert[12]}")
            logger.info(f"   • Dangerous Attacks (5'): {alert[13]}")
            logger.info(f"   • Total Attacks (5'): {alert[14]}")
        else:
            logger.warning("❌ No alerts found in database!")
    
    except Exception as e:
        logger.error(f"❌ Error checking alert: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        cursor.close()
        conn.close()

def main():
    """Main entry point"""
    try:
        check_last_alert()
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()