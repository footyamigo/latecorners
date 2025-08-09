#!/usr/bin/env python3
"""Comprehensive test to verify alert saving with all database details."""
import os
import sys

# Set DATABASE_URL
os.environ['DATABASE_URL'] = 'postgresql://postgres:jIwhlnuBmXDEiHjndVZzCmxNEkpquJAL@trolley.proxy.rlwy.net:24044/railway'

from alert_tracker import track_elite_alert
import psycopg2
from datetime import datetime

def test_late_momentum_alert():
    """Test Late Momentum alert saving."""
    print("🔥 Testing LATE_MOMENTUM Alert...")
    
    # Test data for Late Momentum alert
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

    # Save the alert
    success = track_elite_alert(
        match_data=alert_data,
        tier='LATE_MOMENTUM',
        score=82,
        conditions=['Asian Odds Available', 'Minute 85-89', 'Combined Momentum >= 75', 'Total Corners >= 9'],
        momentum_indicators=momentum_indicators,
        detected_patterns=[]
    )
    
    print(f"Alert saved: {'✅ SUCCESS' if success else '❌ FAILED'}")
    return success

def test_late_corner_draw_alert():
    """Test Late Corner Draw Odds alert saving."""
    print("\n📈 Testing LATE_CORNER_DRAW Alert...")
    
    # Test data for Draw Odds alert
    alert_data = {
        'fixture_id': 67890,
        'home_team': 'Liverpool',
        'away_team': 'Manchester City',
        'home_score': 1,
        'away_score': 1,
        'minute': 88,
        'total_corners': 10,
        'draw_odds': 1.35,  # Low draw odds
        'active_odds': ['Over 11.5 = 2.10', 'Under 11.5 = 1.75']
    }

    momentum_indicators = {
        'combined_momentum10': 45,  # Not using momentum for this alert type
        'momentum_home_total': 22,
        'momentum_away_total': 23,
        'draw_odds': 1.35,
    }

    # Save the alert
    success = track_elite_alert(
        match_data=alert_data,
        tier='LATE_CORNER_DRAW',
        score=0,  # No score needed for draw odds alerts
        conditions=['Asian Odds Available', 'Minute 85-89', 'Draw Odds <= 1.50'],
        momentum_indicators=momentum_indicators,
        detected_patterns=[]
    )
    
    print(f"Alert saved: {'✅ SUCCESS' if success else '❌ FAILED'}")
    return success

def show_database_contents():
    """Show all alerts in the database with full details."""
    print("\n📋 Current Database Contents:")
    print("=" * 80)
    
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        
        # Get column names first
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'alerts' 
            ORDER BY ordinal_position
        """)
        columns = [row[0] for row in cur.fetchall()]
        print(f"📊 Columns: {', '.join(columns)}")
        print("-" * 80)
        
        # Get all alerts
        cur.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 5")
        alerts = cur.fetchall()
        
        if not alerts:
            print("❌ No alerts found in database")
        else:
            for i, alert in enumerate(alerts, 1):
                print(f"\n🚨 Alert #{i}:")
                for col, value in zip(columns, alert):
                    if col == 'timestamp':
                        print(f"  {col}: {value}")
                    elif col in ['draw_odds', 'combined_momentum10', 'momentum_home_total', 'momentum_away_total']:
                        print(f"  {col}: {value}")
                    elif col == 'asian_odds_snapshot':
                        print(f"  {col}: {value}")
                    else:
                        print(f"  {col}: {value}")
                print("-" * 40)
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error reading database: {e}")

if __name__ == "__main__":
    print("🧪 COMPREHENSIVE ALERT DATABASE TEST")
    print("=" * 50)
    
    # Test both alert types
    test1 = test_late_momentum_alert()
    test2 = test_late_corner_draw_alert()
    
    # Show database contents
    show_database_contents()
    
    # Summary
    print(f"\n📊 Test Summary:")
    print(f"  Late Momentum Alert: {'✅' if test1 else '❌'}")
    print(f"  Late Corner Draw Alert: {'✅' if test2 else '❌'}")
    print(f"  Overall: {'✅ ALL TESTS PASSED' if (test1 and test2) else '❌ SOME TESTS FAILED'}")