#!/usr/bin/env python3
"""
Test High Priority Count Database Tracking
==========================================
Verifies that high_priority_count is saved and analyzed correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# Set DATABASE_URL before importing database modules
if 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = "postgresql://postgres:PASSWORD@trolley.proxy.rlwy.net:24044/railway"

from alert_tracker import AlertTracker
from analyze_performance import PerformanceAnalyzer
from database import get_database

def test_high_priority_tracking():
    """Test high priority count tracking end-to-end"""
    
    print("🧪 TESTING HIGH PRIORITY COUNT TRACKING...")
    
    # Test database connection and migration
    print("\n1️⃣ TESTING DATABASE MIGRATION...")
    try:
        db = get_database()
        db.init_database()  # This will run migrations
        print("✅ Database initialized with high_priority_count column")
    except Exception as e:
        print(f"❌ Database error: {e}")
        return
    
    # Test alert tracking
    print("\n2️⃣ TESTING ALERT TRACKING...")
    tracker = AlertTracker()
    
    # Mock match data with different high priority counts
    test_alerts = [
        {
            'fixture_id': 999991,
            'home_team': 'Test Team A',
            'away_team': 'Test Team B', 
            'home_score': 1,
            'away_score': 1,
            'minute': 85,
            'total_corners': 8,
            'high_priority_count': 2,  # Minimum for ELITE
            'active_odds': ['Over 9 = 1.80', 'Under 9 = 2.00']
        },
        {
            'fixture_id': 999992,
            'home_team': 'Test Team C',
            'away_team': 'Test Team D',
            'home_score': 0,
            'away_score': 0,
            'minute': 85,
            'total_corners': 10,
            'high_priority_count': 4,  # High priority alert
            'active_odds': ['Over 11 = 1.67', 'Under 11 = 2.15']
        },
        {
            'fixture_id': 999993,
            'home_team': 'Test Team E',
            'away_team': 'Test Team F',
            'home_score': 2,
            'away_score': 1,
            'minute': 85,
            'total_corners': 12,
            'high_priority_count': 3,  # Medium priority
            'active_odds': ['Over 13 = 1.95', 'Under 13 = 1.85']
        }
    ]
    
    for i, alert_data in enumerate(test_alerts, 1):
        print(f"   📝 Saving test alert {i} (Priority: {alert_data['high_priority_count']})...")
        success = tracker.save_elite_alert(alert_data, "ELITE", 18.0 + i, [])
        if success:
            print(f"   ✅ Alert {i} saved successfully")
        else:
            print(f"   ❌ Alert {i} failed to save")
    
    # Test retrieval and analysis
    print("\n3️⃣ TESTING DATA RETRIEVAL...")
    try:
        recent_alerts = db.get_all_alerts(5)
        print(f"✅ Retrieved {len(recent_alerts)} recent alerts")
        
        # Check if high_priority_count is in the data
        for alert in recent_alerts[-3:]:  # Check last 3 (our test alerts)
            if 'high_priority_count' in alert and alert['high_priority_count'] is not None:
                print(f"   ✅ Alert {alert['fixture_id']}: Priority {alert['high_priority_count']}")
            else:
                print(f"   ❌ Alert {alert['fixture_id']}: Missing high_priority_count")
                
    except Exception as e:
        print(f"❌ Retrieval error: {e}")
    
    # Test performance analysis with priority patterns
    print("\n4️⃣ TESTING PERFORMANCE ANALYSIS...")
    try:
        analyzer = PerformanceAnalyzer()
        print("📊 PERFORMANCE REPORT WITH HIGH PRIORITY PATTERNS:")
        analyzer.show_performance_report()
    except Exception as e:
        print(f"❌ Analysis error: {e}")
    
    print("\n🎉 HIGH PRIORITY TRACKING TEST COMPLETE!")

if __name__ == "__main__":
    test_high_priority_tracking() 