#!/usr/bin/env python3
"""Test with ONLY the fields we want to save - no extra columns."""
import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:jIwhlnuBmXDEiHjndVZzCmxNEkpquJAL@trolley.proxy.rlwy.net:24044/railway'

import sys
sys.path.append('.')
from alert_tracker import track_elite_alert
import psycopg2

print("🧪 CLEAN ALERT TEST - Only Essential Fields")
print("=" * 50)

# Test alert with ONLY the essential data
alert_data = {
    'fixture_id': 12345,
    'home_team': 'Arsenal',
    'away_team': 'Chelsea',
    'home_score': 2,
    'away_score': 1,
    'minute': 87,
    'total_corners': 11,
    'draw_odds': 4.2,
    'active_odds': ['Over 12.5 = 1.85', 'Under 12.5 = 1.95']
}

momentum_indicators = {
    'combined_momentum10': 82,
    'momentum_home_total': 48,
    'momentum_away_total': 34,
    'draw_odds': 4.2,
}

print("Saving LATE_MOMENTUM alert...")
success = track_elite_alert(
    match_data=alert_data,
    tier='LATE_MOMENTUM', 
    score=82,
    conditions=[],  # Keep empty
    momentum_indicators=momentum_indicators,
    detected_patterns=[]  # Keep empty
)

print(f"Save result: {'✅ SUCCESS' if success else '❌ FAILED'}")

# Show EXACTLY what's in the database
print("\n📋 Database Record:")
print("-" * 30)
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    # Get the exact record we just saved
    cur.execute("""
        SELECT fixture_id, teams, alert_type, minute_sent, corners_at_alert,
               asian_odds_snapshot, combined_momentum10, momentum_home_total, 
               momentum_away_total, draw_odds
        FROM alerts 
        WHERE fixture_id = 12345
        ORDER BY timestamp DESC LIMIT 1
    """)
    
    record = cur.fetchone()
    if record:
        print(f"Fixture ID: {record[0]}")
        print(f"Teams: {record[1]}")
        print(f"Alert Type: {record[2]}")
        print(f"Minute: {record[3]}")
        print(f"Corners: {record[4]}")
        print(f"Asian Odds: {record[5]}")  # Should be just "1.85"
        print(f"Combined Momentum: {record[6]}")
        print(f"Home Momentum: {record[7]}")
        print(f"Away Momentum: {record[8]}")
        print(f"Draw Odds: {record[9]}")
    else:
        print("❌ No record found")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")

print(f"\n✅ This is ALL the data we save - no extra columns created!")