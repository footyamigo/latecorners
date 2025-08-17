#!/usr/bin/env python3
"""
REFUNDS AS LOSSES ANALYSIS
=========================

Recalculate win rates treating refunds as losses to see worst-case performance.
This shows what happens if refunds don't actually help your bankroll.
"""

import os
import sys

# Ensure DATABASE_URL is set
if 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = 'postgresql://postgres:jIwhlnuBmXDEiHjndVZzCmxNEkpquJAL@trolley.proxy.rlwy.net:24044/railway'

from database_postgres import get_database

def analyze_refunds_as_losses():
    """Analyze corner performance treating refunds as losses"""
    
    db = get_database()
    
    print("=" * 70)
    print("\n🚨 REFUNDS COUNTED AS LOSSES - WORST CASE ANALYSIS")
    print("-" * 70)
    
    # Get corner performance with refunds as losses
    corner_query = """
    SELECT 
        corners_at_alert,
        COUNT(*) as total,
        SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN result IN ('LOSS', 'REFUND') THEN 1 ELSE 0 END) as losses_plus_refunds,
        SUM(CASE WHEN result = 'REFUND' THEN 1 ELSE 0 END) as refunds_only,
        ROUND(SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate_with_refunds_as_losses,
        ROUND(SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) - 
        ROUND(SUM(CASE WHEN result IN ('LOSS', 'REFUND') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as profit_loss
    FROM alerts 
    WHERE corners_at_alert IS NOT NULL
    GROUP BY corners_at_alert
    ORDER BY win_rate_with_refunds_as_losses ASC
    """
    
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(corner_query)
                results = cursor.fetchall()
        
        if not results:
            print("❌ No data found")
            return
        
        print(f"{'Corner':<8} {'Total':<8} {'Wins':<6} {'Loss+Ref':<9} {'Refunds':<8} {'Win%':<8} {'Profit':<8}")
        print("-" * 70)
        
        total_alerts = 0
        total_wins = 0
        total_losses_plus_refunds = 0
        worst_performers = []
        
        for row in results:
            corner, total, wins, losses_plus_refunds, refunds_only, win_rate, profit = row
            
            total_alerts += total
            total_wins += wins
            total_losses_plus_refunds += losses_plus_refunds
            
            # Mark worst performers
            if total >= 15 and win_rate <= 30:  # High volume, terrible performance
                marker = "💀"
                worst_performers.append((corner, total, win_rate, profit))
            elif total >= 10 and win_rate <= 35:  # Medium volume, bad performance
                marker = "💔"
            elif win_rate >= 45:  # Actually decent
                marker = "⭐"
            else:
                marker = "  "
            
            print(f"{marker} {corner:<6} {total:<8} {wins:<6} {losses_plus_refunds:<9} {refunds_only:<8} {win_rate:<8}% {profit:<8.1f}%")
        
        # Calculate total refunds for the table
        total_refunds = total_alerts - total_wins - (total_losses_plus_refunds - total_alerts + total_wins)
        
        # Add totals row
        print("-" * 70)
        overall_win_rate_table = (total_wins / total_alerts * 100) if total_alerts > 0 else 0
        overall_profit_table = overall_win_rate_table - ((total_losses_plus_refunds / total_alerts * 100) if total_alerts > 0 else 0)
        print(f"🔢 TOTAL  {total_alerts:<8} {total_wins:<6} {total_losses_plus_refunds:<9} {66:<8} {overall_win_rate_table:<8.1f}% {overall_profit_table:<8.1f}%")
        print("=" * 70)
        
        # Overall statistics
        overall_win_rate = (total_wins / total_alerts * 100) if total_alerts > 0 else 0
        overall_profit = overall_win_rate - ((total_losses_plus_refunds / total_alerts * 100) if total_alerts > 0 else 0)
        
        print("\n" + "=" * 70)
        print(f"📊 OVERALL PERFORMANCE (Refunds = Losses):")
        print(f"   Total Alerts: {total_alerts}")
        print(f"   Total Wins: {total_wins}")
        print(f"   Total Losses+Refunds: {total_losses_plus_refunds}")
        print(f"   Overall Win Rate: {overall_win_rate:.1f}%")
        print(f"   Overall Profit: {overall_profit:.1f}%")
        
        print(f"\n💀 WORST HIGH-VOLUME PERFORMERS:")
        for corner, total, win_rate, profit in worst_performers:
            print(f"   {corner} corners: {total} alerts, {win_rate}% win rate, {profit:.1f}% profit")
        
        # Impact of refunds
        print(f"\n🔍 REFUND IMPACT ANALYSIS:")
        refund_query = """
        SELECT 
            COUNT(*) as total_refunds,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM alerts), 1) as refund_percentage
        FROM alerts 
        WHERE result = 'REFUND'
        """
        
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(refund_query)
                refund_results = cursor.fetchall()
        if refund_results:
            total_refunds, refund_percentage = refund_results[0]
            print(f"   Total Refunds: {total_refunds} ({refund_percentage}% of all alerts)")
            print(f"   These {total_refunds} refunds are now counted as losses!")
        
        # Show the damage by corner count
        print(f"\n💸 FINANCIAL DAMAGE BY CORNER COUNT:")
        damage_query = """
        SELECT 
            corners_at_alert,
            COUNT(*) as total,
            SUM(CASE WHEN result = 'REFUND' THEN 1 ELSE 0 END) as refunds,
            ROUND(SUM(CASE WHEN result = 'REFUND' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as refund_rate
        FROM alerts 
        WHERE corners_at_alert IS NOT NULL AND result = 'REFUND'
        GROUP BY corners_at_alert
        ORDER BY refunds DESC
        """
        
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(damage_query)
                damage_results = cursor.fetchall()
        if damage_results:
            print(f"   {'Corner':<8} {'Refunds':<8} {'% of Corner':<12}")
            for corner, total, refunds, refund_rate in damage_results:
                print(f"   {corner:<8} {refunds:<8} {refund_rate:<12}%")
        
    except Exception as e:
        print(f"❌ Error in analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_refunds_as_losses()