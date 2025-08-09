#!/usr/bin/env python3
"""Check if win/loss result tracking is still in place."""
import os
import psycopg2

os.environ['DATABASE_URL'] = 'postgresql://postgres:jIwhlnuBmXDEiHjndVZzCmxNEkpquJAL@trolley.proxy.rlwy.net:24044/railway'

def check_result_tracking():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    print("🔍 Checking Win/Loss Tracking Functionality...")
    print("=" * 50)

    # Check if we have the result tracking columns
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'alerts' AND column_name IN ('result', 'final_corners', 'checked_at', 'match_finished')
        ORDER BY column_name
    """)
    result_columns = cur.fetchall()
    
    print("📊 Result tracking columns:")
    tracking_columns_present = 0
    for col, dtype in result_columns:
        print(f"  ✅ {col} ({dtype})")
        tracking_columns_present += 1

    # Check if all required columns are present
    required_columns = ['result', 'final_corners', 'checked_at', 'match_finished']
    missing_columns = []
    
    present_column_names = [col[0] for col in result_columns]
    for req_col in required_columns:
        if req_col not in present_column_names:
            missing_columns.append(req_col)
    
    if missing_columns:
        print(f"\n❌ Missing columns: {missing_columns}")
    else:
        print(f"\n✅ All result tracking columns present!")

    # Show sample of any existing data
    cur.execute("SELECT COUNT(*) FROM alerts")
    total_alerts = cur.fetchone()[0]
    
    if total_alerts > 0:
        cur.execute("""
            SELECT fixture_id, teams, alert_type, final_corners, result, match_finished 
            FROM alerts 
            ORDER BY timestamp DESC LIMIT 3
        """)
        
        print(f"\n📋 Sample alerts ({total_alerts} total):")
        for row in cur.fetchall():
            fixture_id, teams, alert_type, final_corners, result, match_finished = row
            print(f"  ID: {fixture_id}, Teams: {teams}")
            print(f"    Alert: {alert_type}, Final Corners: {final_corners}")
            print(f"    Result: {result}, Finished: {match_finished}")
            print()
    else:
        print(f"\n📋 No alerts in database yet")

    cur.close()
    conn.close()

    return len(missing_columns) == 0

if __name__ == "__main__":
    is_working = check_result_tracking()
    print(f"🎯 Win/Loss Tracking: {'✅ WORKING' if is_working else '❌ BROKEN'}")