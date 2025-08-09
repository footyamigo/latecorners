#!/usr/bin/env python3
"""Remove ONLY high_priority_ratio and tier_1 columns - keep shots on target."""
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

    # Columns we want to REMOVE (only these two)
    remove_columns = ['high_priority_ratio', 'tier_1']

    # Remove ONLY the specified columns
    removed_count = 0
    for col in remove_columns:
        if col in current_columns:
            try:
                cur.execute(f'ALTER TABLE alerts DROP COLUMN IF EXISTS "{col}"')
                print(f'✅ Removed: {col}')
                removed_count += 1
            except Exception as e:
                print(f'❌ Could not remove {col}: {e}')
        else:
            print(f'ℹ️ Column {col} does not exist')

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