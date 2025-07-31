#!/usr/bin/env python3
"""
Test PostgreSQL Database Connection
==================================
Verify that the PostgreSQL database is working correctly.
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_postgres_connection():
    """Test PostgreSQL database connection and basic operations"""
    
    logger.info("🔍 TESTING POSTGRESQL CONNECTION...")
    
    # Check if DATABASE_URL is available
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("❌ DATABASE_URL environment variable not found")
        logger.info("💡 For local testing, add to .env:")
        logger.info("   DATABASE_URL=postgresql://username:password@localhost:5432/dbname")
        return False
    
    logger.info(f"✅ DATABASE_URL found: {database_url[:30]}...")
    
    try:
        # Import and test the database
        from database_postgres import get_database
        
        logger.info("📊 Testing database initialization...")
        db = get_database()
        
        logger.info("✅ Database initialized successfully!")
        
        # Test basic operations
        logger.info("🧪 Testing performance stats (should be empty)...")
        stats = db.get_performance_stats()
        logger.info(f"📈 Stats: {stats}")
        
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
            
            # Get performance stats again
            stats = db.get_performance_stats()
            logger.info(f"📈 Updated stats: {stats}")
            
            # Get all alerts
            alerts = db.get_all_alerts(limit=5)
            logger.info(f"📋 Found {len(alerts)} alerts in database")
            
            logger.info("🎉 ALL POSTGRESQL TESTS PASSED!")
            return True
        else:
            logger.error("❌ Failed to save test alert")
            return False
            
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.info("💡 Make sure psycopg2-binary is installed:")
        logger.info("   pip install psycopg2-binary")
        return False
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        logger.info("💡 Common issues:")
        logger.info("   1. PostgreSQL service not running")
        logger.info("   2. Incorrect DATABASE_URL")
        logger.info("   3. Network/firewall issues")
        return False

def test_railway_requirements():
    """Check that all Railway requirements are met"""
    
    logger.info("🚀 CHECKING RAILWAY REQUIREMENTS...")
    
    # Check requirements.txt
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
            if 'psycopg2-binary' in requirements:
                logger.info("✅ psycopg2-binary found in requirements.txt")
            else:
                logger.error("❌ psycopg2-binary missing from requirements.txt")
                return False
    except FileNotFoundError:
        logger.error("❌ requirements.txt not found")
        return False
    
    # Check database files exist
    if os.path.exists('database_postgres.py'):
        logger.info("✅ database_postgres.py exists")
    else:
        logger.error("❌ database_postgres.py not found")
        return False
    
    if os.path.exists('database.py'):
        logger.info("✅ database.py exists (import wrapper)")
    else:
        logger.error("❌ database.py not found")
        return False
    
    logger.info("🎉 ALL RAILWAY REQUIREMENTS MET!")
    return True

if __name__ == "__main__":
    print("🗄️ POSTGRESQL RAILWAY TEST")
    print("="*40)
    
    # Test Railway requirements
    requirements_ok = test_railway_requirements()
    print()
    
    # Test PostgreSQL connection (only if requirements are OK)
    if requirements_ok:
        postgres_ok = test_postgres_connection()
        
        if postgres_ok:
            print("\n🎉 READY FOR RAILWAY DEPLOYMENT!")
            print("📋 Next steps:")
            print("   1. Add PostgreSQL service to Railway")
            print("   2. Deploy your code")
            print("   3. Watch the logs for database activity")
        else:
            print("\n⚠️ PostgreSQL test failed - check your setup")
    else:
        print("\n❌ Requirements not met - fix issues above") 