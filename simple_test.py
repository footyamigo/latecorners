#!/usr/bin/env python3
import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:jIwhlnuBmXDEiHjndVZzCmxNEkpquJAL@trolley.proxy.rlwy.net:24044/railway'

# Direct import without module path issues
import sys
sys.path.append('.')

from alert_tracker import track_elite_alert
import psycopg2

print("🧪 SIMPLE ALERT TEST")

# Test Late Momentum Alert
alert_data = {
    'fixture_id': 99999,
    'home_team': 'Test Home',
    'away_team': 'Test Away',
    'home_score': 1,
    'away_score': 1,
    'minute': 87,
    'total_corners': 10,
    'draw_odds': 3.5,
    'active_odds': ['Over 11.5 = 2.1', 'Under 11.5 = 1.8']
}

momentum_indicators = {
    'combined_momentum10': 85,
    'momentum_home_total': 45,
    'momentum_away_total': 40,
    'draw_odds': 3.5,
}

print("Saving LATE_MOMENTUM alert...")
success = track_elite_alert(
    match_data=alert_data,
    tier='LATE_MOMENTUM',
    score=85,
    conditions=['Test condition'],
    momentum_indicators=momentum_indicators
)

print(f"Result: {'✅ SUCCESS' if success else '❌ FAILED'}")

# Show what's in database
print("\n📋 Database Contents:")
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    cur.execute("SELECT fixture_id, teams, alert_type, asian_odds_snapshot, combined_momentum10, draw_odds FROM alerts ORDER BY timestamp DESC LIMIT 3")
    for row in cur.fetchall():
        print(f"  ID: {row[0]}, Teams: {row[1]}, Type: {row[2]}")
        print(f"  Asian Odds: {row[3]}, Momentum: {row[4]}, Draw Odds: {row[5]}")
        print()
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ DB Error: {e}")