#!/usr/bin/env python3
"""
Reset Alerts to Pending
======================
Reset the 4 alerts to pending status so we can rerun with correct corner extraction.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Set database URL for local testing
os.environ['DATABASE_URL'] = 'postgresql://postgres:jIwhlnuBmXDEiHjndVZzCmxNEkpquJAL@trolley.proxy.rlwy.net:24044/railway'

from database import get_database

def reset_alerts_to_pending():
    """Reset all 4 alerts to pending status"""
    
    print("🔄 RESETTING ALERTS TO PENDING STATUS")
    print("="*50)
    
    try:
        db = get_database()
        
        # Get all alerts that were just processed
        all_alerts = db.get_all_alerts(limit=10)
        
        print(f"📋 Found {len(all_alerts)} total alerts")
        
        # Reset the 4 test alerts
        fixture_ids = [999999, 19428967, 19467972, 19396363]
        
        for alert in all_alerts:
            if alert['fixture_id'] in fixture_ids and alert['match_finished']:
                print(f"🔄 Resetting alert {alert['id']}: {alert['teams']}")
                print(f"   Fixture ID: {alert['fixture_id']}")
                print(f"   Previous result: {alert['result']} ({alert['final_corners']} corners)")
                
                # Reset to pending
                success = reset_single_alert(db, alert['id'])
                if success:
                    print(f"   ✅ Reset to pending status")
                else:
                    print(f"   ❌ Failed to reset")
                print()
        
        print("✅ All alerts reset to pending status!")
        
    except Exception as e:
        print(f"❌ Error resetting alerts: {e}")
        import traceback
        traceback.print_exc()

def reset_single_alert(db, alert_id):
    """Reset a single alert to pending status"""
    
    try:
        # Use raw SQL to reset the alert
        import psycopg2
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE alerts 
            SET final_corners = NULL, 
                result = NULL, 
                checked_at = NULL, 
                match_finished = FALSE
            WHERE id = %s
        """, (alert_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error resetting alert {alert_id}: {e}")
        return False

if __name__ == "__main__":
    reset_alerts_to_pending() 