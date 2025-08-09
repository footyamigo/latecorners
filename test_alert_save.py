#!/usr/bin/env python3
import os
import sys

# Set DATABASE_URL
os.environ['DATABASE_URL'] = 'postgresql://postgres:jIwhlnuBmXDEiHjndVZzCmxNEkpquJAL@trolley.proxy.rlwy.net:24044/railway'

from alert_tracker import track_elite_alert

# Test alert data similar to what main.py creates
test_alert_data = {
    'fixture_id': 99999,
    'home_team': 'Test Home',
    'away_team': 'Test Away',
    'home_score': 1,
    'away_score': 1,
    'minute': 87,
    'total_corners': 10,
    'total_probability': 85,
    'alert_type': 'LATE_MOMENTUM',
    'draw_odds': 3.5,
    'combined_momentum10': 85,
    'momentum_home': {'total': 45},
    'momentum_away': {'total': 40},
    'active_odds': ['Over 11 = 2.1', 'Under 11 = 1.8']
}

test_momentum_indicators = {
    'combined_momentum10': 85,
    'momentum_home_total': 45,
    'momentum_away_total': 40,
    'draw_odds': 3.5,
}

print("Testing alert save...")
try:
    success = track_elite_alert(
        match_data=test_alert_data,
        tier='LATE_MOMENTUM',
        score=85,
        conditions=['Test condition'],
        momentum_indicators=test_momentum_indicators,
        detected_patterns=[]
    )
    print(f"Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()