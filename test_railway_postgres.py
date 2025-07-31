#!/usr/bin/env python3
"""
Test Railway PostgreSQL Connection
=================================
"""

import os
import logging

# Set the correct DATABASE_URL BEFORE importing database modules
os.environ['DATABASE_URL'] = 'postgresql://postgres:jIwhlnuBmXDEiHjndVZzCmxNEkpquJAL@trolley.proxy.rlwy.net:24044/railway'

# Now import database after setting the environment variable
from database_postgres import get_database

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_railway_postgres():
    """Test Railway PostgreSQL connection"""
    
    print("🚀 TESTING RAILWAY POSTGRESQL CONNECTION")
    print("="*50)
    
    try:
        # Test database initialization
        logger.info("📊 Testing database initialization...")
        db = get_database()
        logger.info("✅ Database initialized successfully!")
        
        # Test saving a dummy alert
        logger.info("💾 Testing alert save...")
        test_alert = {
            'fixture_id': 999999,
            'teams': 'Test Team A vs Test Team B',
            'score_at_alert': '1-0',
            'minute_sent': 85,
            'corners_at_alert': 8,
            'elite_score': 9.5,
            'over_line': '10.5',
            'over_odds': '1.95'
        }
        
        success = db.save_alert(test_alert)
        if success:
            logger.info("✅ Test alert saved successfully!")
            
            # Get performance stats
            stats = db.get_performance_stats()
            logger.info(f"📈 Stats: {stats}")
            
            # Get all alerts
            alerts = db.get_all_alerts(limit=5)
            logger.info(f"📋 Found {len(alerts)} alerts in database")
            
            print("\n🎉 ALL POSTGRESQL TESTS PASSED!")
            print("🚀 READY FOR RAILWAY DEPLOYMENT!")
            return True
        else:
            logger.error("❌ Failed to save test alert")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_railway_postgres()
    if success:
        print("\n✅ PostgreSQL is ready for deployment!")
    else:
        print("\n❌ PostgreSQL test failed") 