import os
import logging
from datetime import datetime
from typing import List, Dict, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import sql

logger = logging.getLogger(__name__)

class PostgreSQLDatabase:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(self.database_url)
            return conn
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    def init_database(self):
        """Initialize database tables"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Create alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fixture_id INTEGER NOT NULL,
                    teams VARCHAR(255) NOT NULL,
                    score_at_alert VARCHAR(50),
                    minute_sent INTEGER,
                    corners_at_alert INTEGER,
                    elite_score FLOAT,
                    high_priority_count INTEGER DEFAULT 0,
                    high_priority_ratio VARCHAR(20),
                    home_shots_on_target INTEGER DEFAULT 0,
                    away_shots_on_target INTEGER DEFAULT 0,
                    total_shots_on_target INTEGER DEFAULT 0,
                    over_line VARCHAR(20),
                    over_odds VARCHAR(20),
                    final_corners INTEGER DEFAULT NULL,
                    result VARCHAR(20) DEFAULT NULL,
                    checked_at TIMESTAMP DEFAULT NULL,
                    match_finished BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tier_1 VARCHAR(3) DEFAULT 'No'
                )
            """)
            
            # Run migrations for schema updates
            self._run_migrations(cursor)
            
            # Create index on fixture_id for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_fixture_id 
                ON alerts(fixture_id)
            """)
            
            # Create index on match_finished for pending queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_finished 
                ON alerts(match_finished)
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("✅ PostgreSQL database initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    def _run_migrations(self, cursor):
        """Run database migrations for schema updates"""
        # Migration: Add high_priority_count column if it doesn't exist
        try:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'alerts' AND column_name = 'high_priority_count'
            """)
            
            if not cursor.fetchone():
                logger.info("🔄 MIGRATION: Adding high_priority_count column...")
                cursor.execute("""
                    ALTER TABLE alerts 
                    ADD COLUMN high_priority_count INTEGER DEFAULT 0
                """)
                logger.info("✅ MIGRATION: high_priority_count column added")
            else:
                logger.debug("⏭️ MIGRATION: high_priority_count column already exists")
                
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            # Don't raise - migrations are non-critical for basic functionality

        # Migration: Add high_priority_ratio column if it doesn't exist
        try:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'alerts' AND column_name = 'high_priority_ratio'
            """)
            
            if not cursor.fetchone():
                logger.info("🔄 MIGRATION: Adding high_priority_ratio column...")
                cursor.execute("""
                    ALTER TABLE alerts 
                    ADD COLUMN high_priority_ratio VARCHAR(20)
                """)
                logger.info("✅ MIGRATION: high_priority_ratio column added")
            else:
                logger.debug("⏭️ MIGRATION: high_priority_ratio column already exists")
                
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
                
        # Migration: Add home_shots_on_target column if it doesn't exist
        try:
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'alerts' AND column_name = 'home_shots_on_target'
            """)
            
            if not cursor.fetchone():
                logger.info("🔄 MIGRATION: Adding home_shots_on_target column...")
                cursor.execute("""
                    ALTER TABLE alerts 
                    ADD COLUMN home_shots_on_target INTEGER DEFAULT 0
                """)
                logger.info("✅ MIGRATION: home_shots_on_target column added")
            else:
                logger.debug("⏭️ MIGRATION: home_shots_on_target column already exists")
                
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            
        # Migration: Add away_shots_on_target column if it doesn't exist
        try:
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'alerts' AND column_name = 'away_shots_on_target'
            """)
            
            if not cursor.fetchone():
                logger.info("🔄 MIGRATION: Adding away_shots_on_target column...")
                cursor.execute("""
                    ALTER TABLE alerts 
                    ADD COLUMN away_shots_on_target INTEGER DEFAULT 0
                """)
                logger.info("✅ MIGRATION: away_shots_on_target column added")
            else:
                logger.debug("⏭️ MIGRATION: away_shots_on_target column already exists")
                
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            
        # Migration: Add total_shots_on_target column if it doesn't exist
        try:
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'alerts' AND column_name = 'total_shots_on_target'
            """)
            
            if not cursor.fetchone():
                logger.info("🔄 MIGRATION: Adding total_shots_on_target column...")
                cursor.execute("""
                    ALTER TABLE alerts 
                    ADD COLUMN total_shots_on_target INTEGER DEFAULT 0
                """)
                logger.info("✅ MIGRATION: total_shots_on_target column added")
            else:
                logger.debug("⏭️ MIGRATION: total_shots_on_target column already exists")
                
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            # Don't raise - migrations are non-critical for basic functionality

        # Migration: Add tier_1 column if it doesn't exist
        try:
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'alerts' AND column_name = 'tier_1'
            """)
            
            if not cursor.fetchone():
                logger.info("🔄 MIGRATION: Adding tier_1 column...")
                cursor.execute("""
                    ALTER TABLE alerts 
                    ADD COLUMN tier_1 VARCHAR(3) DEFAULT 'No'
                """)
                logger.info("✅ MIGRATION: tier_1 column added")
            else:
                logger.debug("⏭️ MIGRATION: tier_1 column already exists")
                
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")

    def save_alert(self, alert_data: Dict) -> bool:
        """Save alert to database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO alerts (
                    fixture_id, teams, score_at_alert, minute_sent,
                    corners_at_alert, elite_score, high_priority_count, 
                    high_priority_ratio, home_shots_on_target, away_shots_on_target,
                    total_shots_on_target, over_line, over_odds, tier_1
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                alert_data['fixture_id'],
                alert_data['teams'],
                alert_data['score_at_alert'],
                alert_data['minute_sent'],
                alert_data['corners_at_alert'],
                alert_data['elite_score'],
                alert_data.get('high_priority_count', 0),
                alert_data.get('high_priority_ratio', None),
                alert_data.get('home_shots_on_target', 0),
                alert_data.get('away_shots_on_target', 0),
                alert_data.get('total_shots_on_target', 0),
                alert_data['over_line'],
                alert_data['over_odds'],
                'Yes'  # All new alerts are TIER 1
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Alert saved to PostgreSQL: {alert_data['fixture_id']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save alert: {e}")
            return False
    
    def get_unfinished_alerts(self) -> List[Dict]:
        """Get alerts where match is not finished"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM alerts 
                WHERE match_finished = FALSE 
                ORDER BY timestamp ASC
            """)
            
            alerts = [dict(row) for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            
            logger.info(f"📋 Found {len(alerts)} unfinished alerts")
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Failed to get unfinished alerts: {e}")
            return []
    
    def update_alert_result(self, alert_id: int, final_corners: int, result: str) -> bool:
        """Update alert with final result"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE alerts 
                SET final_corners = %s, result = %s, 
                    checked_at = CURRENT_TIMESTAMP, match_finished = TRUE
                WHERE id = %s
            """, (final_corners, result, alert_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Alert {alert_id} updated: {final_corners} corners = {result}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update alert {alert_id}: {e}")
            return False
    
    def get_all_alerts(self, limit: int = 100) -> List[Dict]:
        """Get all alerts with limit"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM alerts 
                ORDER BY timestamp DESC 
                LIMIT %s
            """, (limit,))
            
            alerts = [dict(row) for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Failed to get alerts: {e}")
            return []
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get overall stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_alerts,
                    COUNT(CASE WHEN result = 'WIN' THEN 1 END) as wins,
                    COUNT(CASE WHEN result = 'LOSS' THEN 1 END) as losses,
                    COUNT(CASE WHEN result = 'REFUND' THEN 1 END) as refunds,
                    COUNT(CASE WHEN match_finished = FALSE THEN 1 END) as pending
                FROM alerts
            """)
            
            stats = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if stats:
                total_alerts, wins, losses, refunds, pending = stats
                
                # Calculate win rate
                completed = wins + losses  # Don't count refunds in win rate
                win_rate = (wins / completed * 100) if completed > 0 else 0
                
                return {
                    'total_alerts': total_alerts,
                    'wins': wins,
                    'losses': losses,
                    'refunds': refunds,
                    'pending': pending,
                    'win_rate': round(win_rate, 1)
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"❌ Failed to get performance stats: {e}")
            return {}

# Global instance
postgres_db = PostgreSQLDatabase()

def get_database():
    """Get the PostgreSQL database instance"""
    return postgres_db 