#!/usr/bin/env python3
"""
Check what columns actually exist in the alerts table
"""

import os
import psycopg2

# Ensure DATABASE_URL is set
if 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = 'postgresql://postgres:jIwhlnuBmXDEiHjndVZzCmxNEkpquJAL@trolley.proxy.rlwy.net:24044/railway'

def check_schema():
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'alerts'
        ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print("📋 ALERTS TABLE COLUMNS:")
        print("-" * 30)
        for col_name, data_type in columns:
            print(f"{col_name:<25} {data_type}")
        
        # Get sample data
        cursor.execute("SELECT * FROM alerts LIMIT 3")
        sample_data = cursor.fetchall()
        
        print(f"\n📊 SAMPLE DATA ({len(sample_data)} rows):")
        print("-" * 50)
        if sample_data:
            # Get column names
            cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'alerts'
            ORDER BY ordinal_position
            """)
            col_names = [row[0] for row in cursor.fetchall()]
            
            print("Columns:", col_names[:10])  # First 10 columns
            print("First row sample:", sample_data[0][:10])  # First 10 values
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()