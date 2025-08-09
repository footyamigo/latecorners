#!/usr/bin/env python3
"""Remove high_priority_ratio and tier_1 columns permanently."""
import os
import psycopg2

os.environ['DATABASE_URL'] = 'postgresql://postgres:jIwhlnuBmXDEiHjndVZzCmxNEkpquJAL@trolley.proxy.rlwy.net:24044/railway'

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Remove these two columns
try:
    cur.execute('ALTER TABLE alerts DROP COLUMN IF EXISTS high_priority_ratio')
    print('✅ Removed high_priority_ratio')
except Exception as e:
    print(f'❌ Error removing high_priority_ratio: {e}')

try:
    cur.execute('ALTER TABLE alerts DROP COLUMN IF EXISTS tier_1')
    print('✅ Removed tier_1')
except Exception as e:
    print(f'❌ Error removing tier_1: {e}')

conn.commit()

# Show final columns
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'alerts' 
    ORDER BY ordinal_position
""")
columns = [row[0] for row in cur.fetchall()]
print(f'\n📋 Final columns: {columns}')

cur.close()
conn.close()