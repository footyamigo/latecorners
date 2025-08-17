#!/usr/bin/env python3
"""
OPTIMIZE 1-0 SCORELINE ANALYSIS
==============================

Deep dive into 1-0 score line matches (32 alerts, 68.8% win rate)
to find what makes the winners different from the losers.

Goal: Find filters to push 68.8% win rate even higher.
"""

import os
import sys

# Ensure DATABASE_URL is set
if 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = 'postgresql://postgres:jIwhlnuBmXDEiHjndVZzCmxNEkpquJAL@trolley.proxy.rlwy.net:24044/railway'

from database_postgres import get_database

def analyze_1_0_scoreline():
    """Analyze 1-0 score line matches to find optimization opportunities"""
    
    db = get_database()
    
    print("=" * 80)
    print("\n🔍 OPTIMIZING 1-0 SCORE LINE PERFORMANCE")
    print("Current: 32 alerts, 68.8% win rate when betting 'Under 2 more corners'")
    print("Goal: Find filters to increase win rate above 75%+")
    print("=" * 80)
    
    # Get detailed data for 1-0 score line matches
    detailed_query = """
    SELECT 
        fixture_id,
        teams,
        result,
        corners_at_alert,
        final_corners,
        minute_sent,
        combined_momentum10,
        momentum_home_total,
        draw_odds,
        timestamp::date as alert_date,
        (final_corners - corners_at_alert) as corners_added
    FROM alerts 
    WHERE score_at_alert = '1-0'
    ORDER BY result, corners_at_alert, combined_momentum10 DESC NULLS LAST
    """
    
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(detailed_query)
                results = cursor.fetchall()
        
        if not results:
            print("❌ No 1-0 score line data found")
            return
        
        # Separate into flipped wins and losses
        flipped_wins = [r for r in results if r[2] in ['LOSS', 'REFUND']]  # Original losses/refunds = flipped wins
        flipped_losses = [r for r in results if r[2] == 'WIN']  # Original wins = flipped losses
        
        total_alerts = len(results)
        win_count = len(flipped_wins)
        loss_count = len(flipped_losses)
        win_rate = (win_count / total_alerts * 100) if total_alerts > 0 else 0
        
        print(f"📊 1-0 SCORE LINE OVERVIEW:")
        print(f"   Total: {total_alerts} alerts")
        print(f"   Flipped Wins: {win_count} ({win_rate:.1f}%)")
        print(f"   Flipped Losses: {loss_count}")
        
        # ANALYSIS 1: Corner Count Patterns
        print(f"\n🎯 ANALYSIS 1: CORNER COUNT PATTERNS")
        print("-" * 50)
        
        # Group by corner count
        corner_analysis = {}
        for match in results:
            corner_count = match[3]  # corners_at_alert
            result = match[2]        # result
            flipped_result = 'WIN' if result in ['LOSS', 'REFUND'] else 'LOSS'
            
            if corner_count not in corner_analysis:
                corner_analysis[corner_count] = {'total': 0, 'wins': 0, 'losses': 0}
            
            corner_analysis[corner_count]['total'] += 1
            if flipped_result == 'WIN':
                corner_analysis[corner_count]['wins'] += 1
            else:
                corner_analysis[corner_count]['losses'] += 1
        
        print(f"{'Corner Count':<12} {'Total':<8} {'Wins':<6} {'Losses':<8} {'Win %':<8} {'Quality'}")
        print("-" * 50)
        
        best_corner_counts = []
        for corner_count in sorted(corner_analysis.keys()):
            data = corner_analysis[corner_count]
            win_rate_corner = (data['wins'] / data['total'] * 100) if data['total'] > 0 else 0
            
            if win_rate_corner >= 80 and data['total'] >= 3:
                quality = "🚀 EXCELLENT"
                best_corner_counts.append((corner_count, data['total'], win_rate_corner))
            elif win_rate_corner >= 70:
                quality = "⭐ VERY GOOD"
                best_corner_counts.append((corner_count, data['total'], win_rate_corner))
            elif win_rate_corner >= 60:
                quality = "📈 GOOD"
            else:
                quality = "💔 BAD"
            
            print(f"{corner_count:<12} {data['total']:<8} {data['wins']:<6} {data['losses']:<8} {win_rate_corner:<8.1f}% {quality}")
        
        # ANALYSIS 2: Momentum Patterns
        print(f"\n🎯 ANALYSIS 2: MOMENTUM PATTERNS")
        print("-" * 50)
        
        # Compare momentum between winners and losers
        winner_momentum = [m[6] for m in flipped_wins if m[6] is not None]  # combined_momentum10
        loser_momentum = [m[6] for m in flipped_losses if m[6] is not None]
        
        if winner_momentum and loser_momentum:
            avg_winner_momentum = sum(winner_momentum) / len(winner_momentum)
            avg_loser_momentum = sum(loser_momentum) / len(loser_momentum)
            
            print(f"Average Winner Momentum: {avg_winner_momentum:.1f}")
            print(f"Average Loser Momentum: {avg_loser_momentum:.1f}")
            print(f"Difference: {avg_winner_momentum - avg_loser_momentum:.1f}")
            
            # Find optimal momentum threshold
            momentum_thresholds = [200, 220, 240, 260, 280, 300]
            print(f"\nMomentum Threshold Analysis:")
            print(f"{'Threshold':<12} {'Alerts':<8} {'Wins':<6} {'Win %':<8} {'Quality'}")
            print("-" * 45)
            
            best_momentum_threshold = None
            for threshold in momentum_thresholds:
                filtered_matches = [m for m in results if m[6] is not None and m[6] >= threshold]
                if not filtered_matches:
                    continue
                    
                filtered_wins = sum(1 for m in filtered_matches if m[2] in ['LOSS', 'REFUND'])
                filtered_total = len(filtered_matches)
                filtered_win_rate = (filtered_wins / filtered_total * 100) if filtered_total > 0 else 0
                
                if filtered_win_rate >= 75 and filtered_total >= 5:
                    quality = "🚀 EXCELLENT"
                    best_momentum_threshold = threshold
                elif filtered_win_rate >= 70:
                    quality = "⭐ VERY GOOD"
                elif filtered_win_rate >= 65:
                    quality = "📈 GOOD"
                else:
                    quality = "🔄 OK"
                
                print(f">= {threshold:<9} {filtered_total:<8} {filtered_wins:<6} {filtered_win_rate:<8.1f}% {quality}")
        
        # ANALYSIS 3: Timing Patterns
        print(f"\n🎯 ANALYSIS 3: TIMING PATTERNS")
        print("-" * 50)
        
        winner_minutes = [m[5] for m in flipped_wins if m[5] is not None]
        loser_minutes = [m[5] for m in flipped_losses if m[5] is not None]
        
        if winner_minutes and loser_minutes:
            avg_winner_minute = sum(winner_minutes) / len(winner_minutes)
            avg_loser_minute = sum(loser_minutes) / len(loser_minutes)
            
            print(f"Average Winner Minute: {avg_winner_minute:.1f}'")
            print(f"Average Loser Minute: {avg_loser_minute:.1f}'")
            
            # Timing analysis
            timing_ranges = [(85, 86), (87, 88), (89, 89)]
            print(f"\nTiming Analysis:")
            print(f"{'Minute Range':<12} {'Alerts':<8} {'Wins':<6} {'Win %':<8} {'Quality'}")
            print("-" * 45)
            
            for min_minute, max_minute in timing_ranges:
                filtered_matches = [m for m in results if m[5] is not None and min_minute <= m[5] <= max_minute]
                if not filtered_matches:
                    continue
                    
                filtered_wins = sum(1 for m in filtered_matches if m[2] in ['LOSS', 'REFUND'])
                filtered_total = len(filtered_matches)
                filtered_win_rate = (filtered_wins / filtered_total * 100) if filtered_total > 0 else 0
                
                quality = "🚀 EXCELLENT" if filtered_win_rate >= 75 else "⭐ VERY GOOD" if filtered_win_rate >= 70 else "📈 GOOD"
                
                print(f"{min_minute}'-{max_minute}'       {filtered_total:<8} {filtered_wins:<6} {filtered_win_rate:<8.1f}% {quality}")
        
        # ANALYSIS 4: Combination Filters
        print(f"\n🎯 ANALYSIS 4: COMBINATION FILTERS")
        print("-" * 50)
        
        print("Testing combinations to maximize win rate...")
        
        combinations = [
            ("Best corners + momentum", lambda m: m[3] in [c[0] for c in best_corner_counts] and m[6] is not None and m[6] >= 250),
            ("Best corners + timing", lambda m: m[3] in [c[0] for c in best_corner_counts] and m[5] is not None and 85 <= m[5] <= 87),
            ("High momentum + early timing", lambda m: m[6] is not None and m[6] >= 260 and m[5] is not None and m[5] <= 86),
            ("Ultra-strict filter", lambda m: m[3] in [c[0] for c in best_corner_counts[:2]] and m[6] is not None and m[6] >= 270),
        ]
        
        print(f"{'Filter':<25} {'Alerts':<8} {'Wins':<6} {'Win %':<8} {'Quality'}")
        print("-" * 55)
        
        best_combination = None
        best_combination_win_rate = 0
        
        for filter_name, filter_func in combinations:
            try:
                filtered_matches = [m for m in results if filter_func(m)]
                if not filtered_matches:
                    continue
                    
                filtered_wins = sum(1 for m in filtered_matches if m[2] in ['LOSS', 'REFUND'])
                filtered_total = len(filtered_matches)
                filtered_win_rate = (filtered_wins / filtered_total * 100) if filtered_total > 0 else 0
                
                if filtered_win_rate >= 80 and filtered_total >= 3:
                    quality = "🚀 CHAMPION"
                    if filtered_win_rate > best_combination_win_rate:
                        best_combination = (filter_name, filtered_total, filtered_win_rate)
                        best_combination_win_rate = filtered_win_rate
                elif filtered_win_rate >= 75:
                    quality = "⭐ EXCELLENT"
                elif filtered_win_rate >= 70:
                    quality = "📈 VERY GOOD"
                else:
                    quality = "🔄 OK"
                
                print(f"{filter_name:<25} {filtered_total:<8} {filtered_wins:<6} {filtered_win_rate:<8.1f}% {quality}")
            except Exception as e:
                print(f"{filter_name:<25} ERROR: {e}")
        
        # RECOMMENDATIONS
        print(f"\n💡 OPTIMIZATION RECOMMENDATIONS FOR 1-0 SCORE LINE:")
        print("-" * 60)
        
        if best_corner_counts:
            print(f"🎯 CORNER COUNT FILTER:")
            for corner_count, total, win_rate in best_corner_counts[:3]:
                print(f"   Focus on {corner_count} corners: {win_rate:.1f}% win rate ({total} alerts)")
        
        if best_momentum_threshold:
            print(f"📈 MOMENTUM FILTER:")
            print(f"   Require momentum >= {best_momentum_threshold}")
        
        if best_combination:
            print(f"🚀 BEST COMBINATION:")
            filter_name, total, win_rate = best_combination
            print(f"   {filter_name}: {win_rate:.1f}% win rate ({total} alerts)")
            improvement = win_rate - 68.8
            print(f"   Improvement: +{improvement:.1f}% vs current 68.8%")
        
        print(f"\n🎯 SUMMARY:")
        print(f"   Current 1-0 performance: 68.8% (32 alerts)")
        if best_combination:
            filter_name, total, win_rate = best_combination
            print(f"   Optimized performance: {win_rate:.1f}% ({total} alerts)")
            print(f"   Trade-off: Higher quality, lower volume")
        else:
            print(f"   Consider combining top corner counts with momentum thresholds")
        
    except Exception as e:
        print(f"❌ Error in analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_1_0_scoreline()