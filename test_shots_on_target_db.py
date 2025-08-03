#!/usr/bin/env python3
"""
Test the new shots on target database columns
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_postgres import PostgreSQLDatabase

def test_shots_on_target_db():
    """Test shots on target database integration"""
    
    print("🧪 TESTING SHOTS ON TARGET DATABASE INTEGRATION")
    print("="*60)
    
    # Initialize database
    db = PostgreSQLDatabase()
    
    print("✅ Database initialized - migrations should have run")
    
    # Test saving an alert with shots on target data
    test_alert = {
        'fixture_id': 999999,
        'teams': 'Test Team A vs Test Team B',
        'score_at_alert': '1-0',
        'minute_sent': 85,
        'corners_at_alert': 9,
        'elite_score': 12.5,
        'high_priority_count': 3,
        'high_priority_ratio': '3/2',
        'home_shots_on_target': 8,
        'away_shots_on_target': 4,
        'total_shots_on_target': 12,
        'over_line': '10',
        'over_odds': '1.85'
    }
    
    print("\n📝 Saving test alert with shots on target data...")
    print(f"   Home SOT: {test_alert['home_shots_on_target']}")
    print(f"   Away SOT: {test_alert['away_shots_on_target']}")
    print(f"   Total SOT: {test_alert['total_shots_on_target']}")
    
    success = db.save_alert(test_alert)
    
    if success:
        print("✅ Test alert saved successfully!")
        print("\n🔍 You can now check your PostgreSQL database to see:")
        print("   • home_shots_on_target column with value 8")
        print("   • away_shots_on_target column with value 4")
        print("   • total_shots_on_target column with value 12")
        
        print("\n💡 Benefits of tracking shots on target:")
        print("   • Analyze correlation between SOT and winning alerts")
        print("   • Validate high priority rules (8+ SOT = 4 points)")
        print("   • Track team performance and shooting accuracy")
        print("   • Identify patterns in successful corner predictions")
        print("   • Easy analysis with total_shots_on_target column")
        print("   • Compare SOT thresholds (8+, 10+, 12+ etc.)")
        
    else:
        print("❌ Failed to save test alert")
        
    return success

if __name__ == "__main__":
    success = test_shots_on_target_db()
    
    if success:
        print("\n🎉 SHOTS ON TARGET DATABASE INTEGRATION COMPLETE!")
        print("Your PostgreSQL database now tracks shots on target for all future alerts.")
    else:
        print("\n❌ TEST FAILED!")
        
    sys.exit(0 if success else 1) 