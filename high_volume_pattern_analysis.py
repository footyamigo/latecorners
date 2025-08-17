#!/usr/bin/env python3
"""
HIGH VOLUME PATTERN ANALYSIS
============================

Analyze the patterns within high-volume corner scenarios to find what makes them win/lose.
Focus on 8 corners (34 alerts), 6 corners (31 alerts), 7 corners (29 alerts), 9 corners (29 alerts).

Look at:
- Score lines at alert time
- Momentum indicators
- Time patterns
- Team performance
- Any other distinguishing factors
"""

import os
import sys

# Ensure DATABASE_URL is set
if 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = 'postgresql://postgres:jIwhlnuBmXDEiHjndVZzCmxNEkpquJAL@trolley.proxy.rlwy.net:24044/railway'

from database_postgres import get_database

def analyze_high_volume_patterns():
    """Analyze patterns in high-volume corner scenarios"""
    
    db = get_database()
    
    print("=" * 90)
    print("\n🔍 HIGH VOLUME PATTERN ANALYSIS")
    print("=" * 90)
    
    # Focus on top volume scenarios
    high_volume_corners = [8, 6, 7, 9]  # 34, 31, 29, 29 alerts respectively
    
    for corner_count in high_volume_corners:
        print(f"\n🎯 ANALYZING {corner_count} CORNERS SCENARIO")
        print("-" * 70)
        
        # Get detailed data for this corner scenario
        detailed_query = """
        SELECT 
            fixture_id,
            teams,
            result,
            score_at_alert,
            minute_sent,
            corners_at_alert,
            final_corners,
            combined_momentum10,
            momentum_home_total,
            draw_odds,
            timestamp::date as alert_date
        FROM alerts 
        WHERE corners_at_alert = %s
        ORDER BY result DESC, combined_momentum10 DESC NULLS LAST
        """
        
        try:
            with db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(detailed_query, (corner_count,))
                    results = cursor.fetchall()
            
            if not results:
                print(f"❌ No data found for {corner_count} corners")
                continue
            
            # Separate into flipped wins and losses
            flipped_wins = [r for r in results if r[2] in ['LOSS', 'REFUND']]  # Original losses/refunds = flipped wins
            flipped_losses = [r for r in results if r[2] == 'WIN']  # Original wins = flipped losses
            
            total_alerts = len(results)
            win_count = len(flipped_wins)
            loss_count = len(flipped_losses)
            win_rate = (win_count / total_alerts * 100) if total_alerts > 0 else 0
            
            print(f"📊 OVERVIEW: {total_alerts} alerts, {win_count} flipped wins, {loss_count} flipped losses ({win_rate:.1f}% win rate)")
            
            # Analyze score patterns for winners
            if flipped_wins:
                print(f"\n🏆 FLIPPED WINNERS ANALYSIS ({len(flipped_wins)} alerts):")
                
                # Score line patterns
                score_patterns = {}
                for alert in flipped_wins:
                    score = alert[3] or "Unknown"  # score_at_alert is index 3
                    score_patterns[score] = score_patterns.get(score, 0) + 1
                
                print(f"   📈 Score Line Patterns (Top Winners):")
                sorted_scores = sorted(score_patterns.items(), key=lambda x: x[1], reverse=True)
                for score, count in sorted_scores[:5]:
                    percentage = (count / len(flipped_wins)) * 100
                    print(f"     {score}: {count} alerts ({percentage:.1f}%)")
                
                # Momentum patterns
                momentum_data = [alert for alert in flipped_wins if alert[7] is not None]  # combined_momentum10
                home_momentum_data = [alert for alert in flipped_wins if alert[8] is not None]  # momentum_home_total
                draw_odds_data = [alert for alert in flipped_wins if alert[9] is not None]  # draw_odds
                
                if momentum_data:
                    avg_combined_momentum = sum(alert[7] for alert in momentum_data) / len(momentum_data)
                    print(f"   🎯 Average Momentum Metrics:")
                    print(f"     Combined Momentum 10min: {avg_combined_momentum:.1f}")
                
                if home_momentum_data:
                    avg_home_momentum = sum(alert[8] for alert in home_momentum_data) / len(home_momentum_data)
                    print(f"     Home Momentum Total: {avg_home_momentum:.1f}")
                
                if draw_odds_data:
                    avg_draw_odds = sum(alert[9] for alert in draw_odds_data) / len(draw_odds_data)
                    print(f"     Average Draw Odds: {avg_draw_odds:.2f}")
                
                # Minute patterns
                minute_data = [alert[4] for alert in flipped_wins if alert[4] is not None]  # minute_sent is index 4
                if minute_data:
                    avg_minute = sum(minute_data) / len(minute_data)
                    min_minute = min(minute_data)
                    max_minute = max(minute_data)
                    print(f"   ⏰ Timing Patterns:")
                    print(f"     Average minute: {avg_minute:.1f}', Range: {min_minute}'-{max_minute}'")
                
                # Corner difference analysis
                corner_diff_data = []
                for alert in flipped_wins:
                    corners_at_alert = alert[5]  # corners_at_alert
                    final_corners = alert[6]     # final_corners
                    if corners_at_alert is not None and final_corners is not None:
                        diff = final_corners - corners_at_alert
                        corner_diff_data.append(diff)
                
                if corner_diff_data:
                    avg_corner_diff = sum(corner_diff_data) / len(corner_diff_data)
                    min_diff = min(corner_diff_data)
                    max_diff = max(corner_diff_data)
                    print(f"   ⚽ Corner Progression:")
                    print(f"     Average corners added: {avg_corner_diff:.1f}, Range: {min_diff} to {max_diff}")
                    
                    # Count how many had 0, 1, 2+ more corners
                    zero_corners = sum(1 for d in corner_diff_data if d == 0)
                    one_corner = sum(1 for d in corner_diff_data if d == 1)
                    two_plus = sum(1 for d in corner_diff_data if d >= 2)
                    print(f"     0 more: {zero_corners}, 1 more: {one_corner}, 2+ more: {two_plus}")
            
            # Analyze what makes the losers lose (for improvement)
            if flipped_losses:
                print(f"\n💔 FLIPPED LOSERS ANALYSIS ({len(flipped_losses)} alerts) - What to Avoid:")
                
                # Score line patterns for losers
                loser_score_patterns = {}
                for alert in flipped_losses:
                    score = alert[3] or "Unknown"  # score_at_alert is index 3
                    loser_score_patterns[score] = loser_score_patterns.get(score, 0) + 1
                
                print(f"   ❌ Score Lines That Led to Losses:")
                sorted_loser_scores = sorted(loser_score_patterns.items(), key=lambda x: x[1], reverse=True)
                for score, count in sorted_loser_scores[:3]:
                    percentage = (count / len(flipped_losses)) * 100
                    print(f"     {score}: {count} alerts ({percentage:.1f}%) - AVOID")
                
                # Momentum comparison
                loser_momentum_data = [alert for alert in flipped_losses if alert[7] is not None]
                if loser_momentum_data and momentum_data:
                    loser_avg_momentum = sum(alert[7] for alert in loser_momentum_data) / len(loser_momentum_data)
                    winner_avg_momentum = sum(alert[7] for alert in momentum_data) / len(momentum_data)
                    print(f"   📉 Momentum Comparison: Losers {loser_avg_momentum:.1f} vs Winners {winner_avg_momentum:.1f}")
            
            # Recommendations for this corner scenario
            print(f"\n💡 OPTIMIZATION RECOMMENDATIONS FOR {corner_count} CORNERS:")
            
            if flipped_wins and sorted_scores:
                best_score = sorted_scores[0][0]
                best_score_count = sorted_scores[0][1]
                print(f"   🎯 Focus on score line: {best_score} ({best_score_count}/{len(flipped_wins)} wins)")
            
            if momentum_data:
                avg_momentum = sum(alert[7] for alert in momentum_data) / len(momentum_data)
                if avg_momentum >= 80:
                    print(f"   📈 Keep high momentum threshold (current avg: {avg_momentum:.1f})")
                else:
                    print(f"   📈 Consider raising momentum threshold above {avg_momentum:.1f}")
            
            if minute_data:
                if avg_minute >= 87:
                    print(f"   ⏰ Later alerts perform better (avg: {avg_minute:.1f} min)")
                elif avg_minute <= 85:
                    print(f"   ⏰ Earlier alerts perform better (avg: {avg_minute:.1f} min)")
            
        except Exception as e:
            print(f"❌ Error analyzing {corner_count} corners: {e}")
            import traceback
            traceback.print_exc()
    
    # Cross-scenario comparison
    print(f"\n🔄 CROSS-SCENARIO COMPARISON")
    print("-" * 70)
    
    comparison_query = """
    SELECT 
        corners_at_alert,
        COUNT(*) as total,
        AVG(CASE WHEN combined_momentum10 IS NOT NULL THEN combined_momentum10 ELSE 0 END) as avg_momentum,
        string_agg(DISTINCT score_at_alert, ', ') as common_scores,
        AVG(minute_sent) as avg_minute
    FROM alerts 
    WHERE corners_at_alert IN (6, 7, 8, 9) AND result IN ('LOSS', 'REFUND')  -- Focus on flipped winners
    GROUP BY corners_at_alert
    ORDER BY corners_at_alert
    """
    
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(comparison_query)
                comparison_results = cursor.fetchall()
        
        if comparison_results:
            print(f"{'Corner':<8} {'Total':<8} {'Avg Momentum':<12} {'Avg Min':<10} {'Common Scores':<20}")
            print("-" * 70)
            for corner, total, avg_momentum, avg_min, scores in comparison_results:
                print(f"{corner:<8} {total:<8} {avg_momentum:<12.1f} {avg_min:<10.1f}' {scores[:20]:<20}")
        
        print(f"\n🎯 UNIVERSAL PATTERNS:")
        print(f"   Look for scenarios where multiple corner counts show similar winning patterns")
        print(f"   Focus on optimizing the metrics that consistently predict flipped wins")
        
    except Exception as e:
        print(f"❌ Error in cross-scenario comparison: {e}")

if __name__ == "__main__":
    analyze_high_volume_patterns()