#!/usr/bin/env python3
"""FINAL database cleanup - remove ALL unwanted columns permanently."""
import os
import psycopg2

os.environ['DATABASE_URL'] = 'postgresql://postgres:jIwhlnuBmXDEiHjndVZzCmxNEkpquJAL@trolley.proxy.rlwy.net:24044/railway'

def fix_database():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    # Get current columns
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'alerts' 
        ORDER BY ordinal_position
    """)
    current_columns = [row[0] for row in cur.fetchall()]
    print(f"Current columns: {current_columns}")

    # Columns we want to KEEP (essential only)
    keep_columns = [
        'id', 'timestamp', 'fixture_id', 'teams', 'score_at_alert', 
        'minute_sent', 'corners_at_alert', 'final_corners', 'result', 
        'checked_at', 'match_finished', 'alert_type', 'draw_odds', 
        'combined_momentum10', 'momentum_home_total', 'momentum_away_total', 
        'asian_odds_snapshot'
    ]

    # Remove ALL unwanted columns
    removed_count = 0
    for col in current_columns:
        if col not in keep_columns:
            try:
                cur.execute(f'ALTER TABLE alerts DROP COLUMN IF EXISTS "{col}"')
                print(f'✅ Removed: {col}')
                removed_count += 1
            except Exception as e:
                print(f'❌ Could not remove {col}: {e}')

    conn.commit()
    print(f'\n🧹 Removed {removed_count} unwanted columns!')
    
    # Show final columns
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'alerts' 
        ORDER BY ordinal_position
    """)
    final_columns = [row[0] for row in cur.fetchall()]
    print(f"\n✅ Final columns: {final_columns}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    fix_database()