#!/usr/bin/env python3
"""
FLIP THE SCRIPT ANALYSIS
========================

If we're betting "Over 2 more corners" and losing, what if we bet "Under 2 more corners" instead?

Current Logic:
- WIN = 2+ more corners happened
- LOSS = 0 more corners happened  
- REFUND = exactly 1 more corner happened

Flipped Logic (Under 2 more corners):
- WIN = 0 or 1 more corners happened (original LOSS + REFUND)
- LOSS = 2+ more corners happened (original WIN)

This flips our terrible win rates into potentially profitable ones!
"""

import os
import sys

# Ensure DATABASE_URL is set
if 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = 'postgresql://postgres:jIwhlnuBmXDEiHjndVZzCmxNEkpquJAL@trolley.proxy.rlwy.net:24044/railway'

from database_postgres import get_database

def analyze_flipped_markets():
    """Analyze performance if we flip to Under 2 more corners"""
    
    db = get_database()
    
    print("=" * 80)
    print("\n🔄 FLIP THE SCRIPT: Betting UNDER 2 More Corners Instead")
    print("=" * 80)
    
    # Get corner performance with flipped logic
    corner_query = """
    SELECT 
        corners_at_alert,
        COUNT(*) as total,
        SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as original_wins,
        SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) as original_losses,
        SUM(CASE WHEN result = 'REFUND' THEN 1 ELSE 0 END) as original_refunds,
        -- FLIPPED LOGIC: Under 2 more corners
        SUM(CASE WHEN result IN ('LOSS', 'REFUND') THEN 1 ELSE 0 END) as flipped_wins,
        SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as flipped_losses,
        ROUND(SUM(CASE WHEN result IN ('LOSS', 'REFUND') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as flipped_win_rate,
        ROUND(SUM(CASE WHEN result IN ('LOSS', 'REFUND') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) - 
        ROUND(SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as flipped_profit
    FROM alerts 
    WHERE corners_at_alert IS NOT NULL
    GROUP BY corners_at_alert
    ORDER BY flipped_win_rate DESC
    """
    
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(corner_query)
                results = cursor.fetchall()
        
        if not results:
            print("❌ No data found")
            return
        
        print(f"\n🎯 BETTING 'UNDER 2 MORE CORNERS' PERFORMANCE:")
        print(f"{'Corner':<8} {'Total':<8} {'Wins':<6} {'Loss':<6} {'Win%':<8} {'Profit':<8} {'Quality':<12}")
        print("-" * 80)
        
        total_alerts = 0
        total_flipped_wins = 0
        total_flipped_losses = 0
        profitable_scenarios = []
        high_volume_winners = []
        
        for row in results:
            corner, total, orig_wins, orig_losses, orig_refunds, flipped_wins, flipped_losses, flipped_win_rate, flipped_profit = row
            
            total_alerts += total
            total_flipped_wins += flipped_wins
            total_flipped_losses += flipped_losses
            
            # Categorize performance
            if flipped_win_rate >= 70 and total >= 10:
                marker = "🚀"
                quality = "EXCELLENT"
                high_volume_winners.append((corner, total, flipped_win_rate, flipped_profit))
            elif flipped_win_rate >= 60 and total >= 15:
                marker = "⭐"
                quality = "VERY GOOD"
                high_volume_winners.append((corner, total, flipped_win_rate, flipped_profit))
            elif flipped_win_rate >= 55:
                marker = "📈"
                quality = "GOOD"
                if flipped_profit > 0:
                    profitable_scenarios.append((corner, total, flipped_win_rate, flipped_profit))
            elif flipped_win_rate >= 50:
                marker = "🔄"
                quality = "BREAK-EVEN"
            else:
                marker = "💔"
                quality = "STILL BAD"
            
            print(f"{marker} {corner:<6} {total:<8} {flipped_wins:<6} {flipped_losses:<6} {flipped_win_rate:<8}% {flipped_profit:<8.1f}% {quality:<12}")
        
        # Add totals row
        print("-" * 80)
        overall_flipped_win_rate = (total_flipped_wins / total_alerts * 100) if total_alerts > 0 else 0
        overall_flipped_profit = overall_flipped_win_rate - ((total_flipped_losses / total_alerts * 100) if total_alerts > 0 else 0)
        print(f"🔢 TOTAL  {total_alerts:<8} {total_flipped_wins:<6} {total_flipped_losses:<6} {overall_flipped_win_rate:<8.1f}% {overall_flipped_profit:<8.1f}% SYSTEM FLIP")
        print("=" * 80)
        
        # Analysis summary
        print(f"\n🎉 FLIPPED SYSTEM PERFORMANCE:")
        print(f"   Total Alerts: {total_alerts}")
        print(f"   Flipped Wins: {total_flipped_wins}")
        print(f"   Flipped Losses: {total_flipped_losses}")
        print(f"   Overall Win Rate: {overall_flipped_win_rate:.1f}%")
        print(f"   Overall Profit: {overall_flipped_profit:.1f}%")
        
        if overall_flipped_win_rate >= 60:
            print(f"   🚀 STATUS: PROFITABLE SYSTEM!")
        elif overall_flipped_win_rate >= 55:
            print(f"   📈 STATUS: Good potential")
        elif overall_flipped_win_rate >= 50:
            print(f"   🔄 STATUS: Break-even")
        else:
            print(f"   💔 STATUS: Still needs work")
        
        # High volume winners
        if high_volume_winners:
            print(f"\n🚀 HIGH-VOLUME WINNERS (Under 2 More Corners):")
            for corner, total, win_rate, profit in high_volume_winners:
                weekly_estimate = total / 20  # Assuming ~20 weeks of data
                print(f"   {corner} corners: {total} alerts, {win_rate}% win rate, {profit:.1f}% profit (~{weekly_estimate:.1f} alerts/week)")
        
        # Compare original vs flipped for top scenarios
        print(f"\n🔄 BEFORE vs AFTER COMPARISON (Top Volume Scenarios):")
        comparison_query = """
        SELECT 
            corners_at_alert,
            COUNT(*) as total,
            ROUND(SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as original_win_rate,
            ROUND(SUM(CASE WHEN result IN ('LOSS', 'REFUND') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as flipped_win_rate
        FROM alerts 
        WHERE corners_at_alert IS NOT NULL
        GROUP BY corners_at_alert
        HAVING COUNT(*) >= 25
        ORDER BY COUNT(*) DESC
        """
        
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(comparison_query)
                comparison_results = cursor.fetchall()
        
        if comparison_results:
            print(f"   {'Corner':<8} {'Alerts':<8} {'Original%':<12} {'Flipped%':<12} {'Improvement':<12}")
            print("-" * 60)
            for corner, total, orig_rate, flip_rate in comparison_results:
                improvement = flip_rate - orig_rate
                marker = "🚀" if improvement >= 30 else "📈" if improvement >= 20 else "🔄"
                print(f"   {marker} {corner:<6} {total:<8} {orig_rate:<12}% {flip_rate:<12}% +{improvement:<11.1f}%")
        
        # Strategy recommendation
        print(f"\n💡 STRATEGY RECOMMENDATION:")
        if overall_flipped_win_rate >= 65:
            print(f"   🎯 IMMEDIATELY switch to 'Under 2 More Corners' betting!")
            print(f"   🚀 This flip turns your losing system into a winning one!")
            print(f"   📊 Expected improvement: +{overall_flipped_win_rate - (100 - overall_flipped_win_rate):.1f}% win rate")
        elif overall_flipped_win_rate >= 55:
            print(f"   📈 Strong potential with 'Under 2 More Corners'")
            print(f"   🎯 Consider testing this approach on high-volume scenarios")
        else:
            print(f"   🤔 Flipping helps but may not be the complete solution")
            print(f"   🔍 Consider combining with other filters/improvements")
            
    except Exception as e:
        print(f"❌ Error in analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_flipped_markets()