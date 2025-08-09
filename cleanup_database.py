#!/usr/bin/env python3
"""Clean up the alerts database to remove unnecessary columns."""
import os
import psycopg2

# Set DATABASE_URL
os.environ['DATABASE_URL'] = 'postgresql://postgres:jIwhlnuBmXDEiHjndVZzCmxNEkpquJAL@trolley.proxy.rlwy.net:24044/railway'

def cleanup_database():
    """Remove unnecessary columns from alerts table."""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    try:
        print("🧹 Cleaning up database columns...")
        
        # List of columns to remove
        columns_to_remove = [
            'high_priority_ratio',
            'tier_1', 
            'shot_efficiency',
            'attack_volume', 
            'score_context',
            'detected_patterns',
            'corners_last_15',
            'dangerous_attacks_last_5', 
            'attacks_last_5',
            'corner_momentum',
            'home_shots_on_target',
            'away_shots_on_target',
            'total_shots_on_target',
            'attack_intensity',
            'high_priority_count',
            'shots_on_target',
            'over_line',
            'over_odds',
            'total_probability'
        ]
        
        # Remove each column if it exists
        for column in columns_to_remove:
            try:
                cur.execute(f"ALTER TABLE alerts DROP COLUMN IF EXISTS {column}")
                print(f"  ✅ Removed column: {column}")
            except Exception as e:
                print(f"  ⚠️ Could not remove {column}: {e}")
        
        conn.commit()
        print("✅ Database cleanup completed!")
        
        # Show remaining columns
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'alerts' 
            ORDER BY ordinal_position
        """)
        
        print("\n📋 Remaining columns:")
        for row in cur.fetchall():
            print(f"  • {row[0]} ({row[1]})")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    cleanup_database()