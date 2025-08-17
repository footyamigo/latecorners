#!/usr/bin/env python3
"""
SCORELINE PROFITABILITY ANALYSIS
================================

Simple analysis: For each corner count, which score lines bring the most wins
when betting "Under 2 more corners"
"""

import os
import sys

# Ensure DATABASE_URL is set
if 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = 'postgresql://postgres:jIwhlnuBmXDEiHjndVZzCmxNEkpquJAL@trolley.proxy.rlwy.net:24044/railway'

from database_postgres import get_database

def analyze_scoreline_profitability():
    """Analyze which score lines are most profitable for each corner count"""
    
    db = get_database()
    
    print("=" * 90)
    print("\n📊 SCORELINE PROFITABILITY ANALYSIS")
    print("(Betting 'Under 2 More Corners')")
    print("=" * 90)
    
    # Focus on high volume corner counts
    corner_counts = [6, 7, 8, 9, 10]  # Top volume scenarios
    
    for corner_count in corner_counts:
        print(f"\n🎯 {corner_count} CORNERS SCENARIO")
        print("-" * 60)
        
        # Get scoreline performance for this corner count
        scoreline_query = """
        SELECT 
            score_at_alert,
            COUNT(*) as total_alerts,
            SUM(CASE WHEN result IN ('LOSS', 'REFUND') THEN 1 ELSE 0 END) as flipped_wins,
            SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as flipped_losses,
            ROUND(SUM(CASE WHEN result IN ('LOSS', 'REFUND') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate
        FROM alerts 
        WHERE corners_at_alert = %s AND score_at_alert IS NOT NULL
        GROUP BY score_at_alert
        HAVING COUNT(*) >= 2  -- At least 2 alerts for meaningful data
        ORDER BY win_rate DESC, total_alerts DESC
        """
        
        try:
            with db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(scoreline_query, (corner_count,))
                    results = cursor.fetchall()
            
            if not results:
                print(f"❌ No significant data for {corner_count} corners")
                continue
            
            # Display results in simple table
            print(f"{'Score Line':<12} {'Alerts':<8} {'Wins':<6} {'Losses':<8} {'Win %':<8} {'Quality'}")
            print("-" * 60)
            
            best_performers = []
            
            for score, total, wins, losses, win_rate in results:
                # Quality rating
                if win_rate >= 80 and total >= 3:
                    quality = "🚀 EXCELLENT"
                    best_performers.append((score, total, win_rate))
                elif win_rate >= 70 and total >= 3:
                    quality = "⭐ VERY GOOD"
                    best_performers.append((score, total, win_rate))
                elif win_rate >= 60:
                    quality = "📈 GOOD"
                elif win_rate >= 50:
                    quality = "🔄 OK"
                else:
                    quality = "💔 BAD"
                
                print(f"{score:<12} {total:<8} {wins:<6} {losses:<8} {win_rate:<8}% {quality}")
            
            # Summary for this corner count
            if best_performers:
                print(f"\n💡 BEST SCORE LINES FOR {corner_count} CORNERS:")
                for score, total, win_rate in best_performers[:3]:
                    print(f"   🎯 {score}: {win_rate}% win rate ({total} alerts)")
            else:
                print(f"\n⚠️ No excellent performers for {corner_count} corners")
            
        except Exception as e:
            print(f"❌ Error analyzing {corner_count} corners: {e}")
    
    # Overall best score lines across all corner counts
    print(f"\n🏆 OVERALL BEST SCORE LINES (All Corner Counts)")
    print("-" * 70)
    
    overall_query = """
    SELECT 
        score_at_alert,
        COUNT(*) as total_alerts,
        SUM(CASE WHEN result IN ('LOSS', 'REFUND') THEN 1 ELSE 0 END) as flipped_wins,
        ROUND(SUM(CASE WHEN result IN ('LOSS', 'REFUND') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate,
        string_agg(DISTINCT corners_at_alert::text, ', ' ORDER BY corners_at_alert::text) as corner_counts
    FROM alerts 
    WHERE corners_at_alert IN (6, 7, 8, 9, 10) AND score_at_alert IS NOT NULL
    GROUP BY score_at_alert
    HAVING COUNT(*) >= 5  -- At least 5 alerts for meaningful data
    ORDER BY win_rate DESC, total_alerts DESC
    """
    
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(overall_query)
                overall_results = cursor.fetchall()
        
        if overall_results:
            print(f"{'Score Line':<12} {'Total':<8} {'Wins':<6} {'Win %':<8} {'Corner Counts':<15} {'Quality'}")
            print("-" * 70)
            
            for score, total, wins, win_rate, corner_counts in overall_results[:10]:
                if win_rate >= 75:
                    quality = "🚀 CHAMPION"
                elif win_rate >= 65:
                    quality = "⭐ EXCELLENT"
                elif win_rate >= 55:
                    quality = "📈 GOOD"
                else:
                    quality = "🔄 OK"
                
                print(f"{score:<12} {total:<8} {wins:<6} {win_rate:<8}% {corner_counts:<15} {quality}")
        
        print(f"\n💡 STRATEGY RECOMMENDATIONS:")
        print(f"   🎯 Focus on score lines with 70%+ win rates and 5+ alerts")
        print(f"   🚀 Prioritize 'CHAMPION' and 'EXCELLENT' score lines")
        print(f"   ❌ Avoid score lines with <60% win rates")
        
    except Exception as e:
        print(f"❌ Error in overall analysis: {e}")

if __name__ == "__main__":
    analyze_scoreline_profitability()