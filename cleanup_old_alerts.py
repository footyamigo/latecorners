#!/usr/bin/env python3
"""
Clean up old alerts that don't have high_priority_count values.
This removes alerts created before the high_priority_count feature was implemented.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def cleanup_old_alerts():
    """Delete old alerts that don't have meaningful high_priority_count values"""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        return False
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("🔍 ANALYZING CURRENT ALERTS...")
        
        # First, let's see what we have
        cursor.execute("""
            SELECT 
                COUNT(*) as total_alerts,
                COUNT(CASE WHEN high_priority_count IS NULL OR high_priority_count = 0 THEN 1 END) as old_alerts,
                COUNT(CASE WHEN high_priority_count > 0 THEN 1 END) as new_alerts
            FROM alerts
        """)
        
        stats = cursor.fetchone()
        print(f"📊 CURRENT DATABASE STATE:")
        print(f"   • Total alerts: {stats['total_alerts']}")
        print(f"   • Old alerts (high_priority_count = 0 or NULL): {stats['old_alerts']}")
        print(f"   • New alerts (high_priority_count > 0): {stats['new_alerts']}")
        
        if stats['old_alerts'] == 0:
            print("✅ No old alerts to delete! Database is already clean.")
            return True
        
        # Show some examples of what will be deleted
        print(f"\n🗑️ ALERTS TO BE DELETED (first 5 examples):")
        cursor.execute("""
            SELECT id, created_at, teams, high_priority_count, high_priority_ratio
            FROM alerts 
            WHERE high_priority_count IS NULL OR high_priority_count = 0
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        old_alerts = cursor.fetchall()
        for alert in old_alerts:
            print(f"   • ID {alert['id']}: {alert['teams']} ({alert['created_at']}) - Priority: {alert['high_priority_count']}")
        
        # Show some examples of what will be kept
        print(f"\n✅ ALERTS TO BE KEPT (first 5 examples):")
        cursor.execute("""
            SELECT id, created_at, teams, high_priority_count, high_priority_ratio
            FROM alerts 
            WHERE high_priority_count > 0
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        new_alerts = cursor.fetchall()
        for alert in new_alerts:
            print(f"   • ID {alert['id']}: {alert['teams']} ({alert['created_at']}) - Priority: {alert['high_priority_count']} ({alert['high_priority_ratio']})")
        
        # Ask for confirmation
        print(f"\n⚠️  CONFIRMATION REQUIRED:")
        print(f"This will DELETE {stats['old_alerts']} old alerts and KEEP {stats['new_alerts']} new alerts.")
        print(f"Are you sure you want to proceed? This action cannot be undone!")
        
        response = input("Type 'DELETE' to confirm or anything else to cancel: ").strip()
        
        if response != 'DELETE':
            print("❌ Operation cancelled. No alerts were deleted.")
            return False
        
        # Perform the deletion
        print(f"\n🗑️  DELETING OLD ALERTS...")
        cursor.execute("""
            DELETE FROM alerts 
            WHERE high_priority_count IS NULL OR high_priority_count = 0
        """)
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        print(f"✅ SUCCESS!")
        print(f"   • Deleted: {deleted_count} old alerts")
        print(f"   • Remaining: {stats['new_alerts']} alerts with high_priority_count")
        
        # Final verification
        cursor.execute("SELECT COUNT(*) as remaining FROM alerts")
        final_count = cursor.fetchone()['remaining']
        print(f"   • Final total: {final_count} alerts in database")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("🧹 CLEANING UP OLD ALERTS FROM DATABASE")
    print("="*60)
    
    success = cleanup_old_alerts()
    
    if success:
        print("\n🎉 CLEANUP COMPLETE!")
        print("Your database now only contains alerts with high_priority_count values.")
    else:
        print("\n❌ CLEANUP FAILED!")
        
    sys.exit(0 if success else 1) 