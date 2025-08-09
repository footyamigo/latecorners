#!/usr/bin/env python3
import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:jIwhlnuBmXDEiHjndVZzCmxNEkpquJAL@trolley.proxy.rlwy.net:24044/railway'

import sys
sys.path.append('.')
from alert_tracker import track_elite_alert
import psycopg2

print("🧪 FINAL COMPREHENSIVE TEST")
print("=" * 50)

# Test 1: Late Momentum Alert
print("\n🔥 Test 1: LATE_MOMENTUM Alert")
alert1 = {
    'fixture_id': 11111,
    'home_team': 'Arsenal',
    'away_team': 'Chelsea', 
    'home_score': 2,
    'away_score': 1,
    'minute': 87,
    'total_corners': 11,
    'draw_odds': 4.2,
    'active_odds': ['Over 12.5 = 1.85', 'Under 12.5 = 1.95']
}

momentum1 = {
    'combined_momentum10': 82,
    'momentum_home_total': 48,
    'momentum_away_total': 34,
    'draw_odds': 4.2,
}

success1 = track_elite_alert(
    match_data=alert1,
    tier='LATE_MOMENTUM',
    score=82,
    conditions=['Asian Odds Available', 'Minute 85-89', 'Combined Momentum >= 75', 'Total Corners >= 9'],
    momentum_indicators=momentum1
)
print(f"Result: {'✅ SUCCESS' if success1 else '❌ FAILED'}")

# Test 2: Late Corner Draw Alert
print("\n📈 Test 2: LATE_CORNER_DRAW Alert")
alert2 = {
    'fixture_id': 22222,
    'home_team': 'Liverpool',
    'away_team': 'Man City',
    'home_score': 1,
    'away_score': 1,
    'minute': 88,
    'total_corners': 10,
    'draw_odds': 1.35,
    'active_odds': ['Over 11.5 = 2.10', 'Under 11.5 = 1.75']
}

momentum2 = {
    'combined_momentum10': 45,
    'momentum_home_total': 22,
    'momentum_away_total': 23,
    'draw_odds': 1.35,
}

success2 = track_elite_alert(
    match_data=alert2,
    tier='LATE_CORNER_DRAW',
    score=0,
    conditions=['Asian Odds Available', 'Minute 85-89', 'Draw Odds <= 1.50'],
    momentum_indicators=momentum2
)
print(f"Result: {'✅ SUCCESS' if success2 else '❌ FAILED'}")

# Show results
print("\n📋 ALL ALERTS IN DATABASE:")
print("=" * 80)
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    cur.execute("""
        SELECT fixture_id, teams, alert_type, minute_sent, corners_at_alert, 
               asian_odds_snapshot, combined_momentum10, momentum_home_total, 
               momentum_away_total, draw_odds 
        FROM alerts 
        ORDER BY timestamp DESC LIMIT 5
    """)
    
    alerts = cur.fetchall()
    for i, alert in enumerate(alerts, 1):
        print(f"\n🚨 Alert #{i}:")
        print(f"  Fixture ID: {alert[0]}")
        print(f"  Teams: {alert[1]}")
        print(f"  Alert Type: {alert[2]}")
        print(f"  Minute: {alert[3]}")
        print(f"  Corners: {alert[4]}")
        print(f"  Asian Odds: {alert[5]}")  # Should be just Over odds now
        print(f"  Combined Momentum: {alert[6]}")
        print(f"  Home Momentum: {alert[7]}")
        print(f"  Away Momentum: {alert[8]}")
        print(f"  Draw Odds: {alert[9]}")
        print("-" * 40)
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")

print(f"\n📊 FINAL SUMMARY:")
print(f"  LATE_MOMENTUM Alert: {'✅' if success1 else '❌'}")
print(f"  LATE_CORNER_DRAW Alert: {'✅' if success2 else '❌'}")
print(f"  Overall: {'🎉 ALL SYSTEMS WORKING!' if (success1 and success2) else '❌ Issues detected'}")