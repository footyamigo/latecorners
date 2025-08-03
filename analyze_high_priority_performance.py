#!/usr/bin/env python3
"""
Analyze high priority alert performance to find correlations
between high priority patterns and winning results.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def analyze_alert_performance():
    """Analyze current alerts for high priority patterns and correlations"""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        return False
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("🔍 ANALYZING HIGH PRIORITY ALERT PERFORMANCE...")
        print("="*70)
        
        # Get all current alerts with results
        cursor.execute("""
            SELECT *
            FROM alerts 
            WHERE high_priority_count > 0
            ORDER BY created_at DESC
        """)
        
        alerts = cursor.fetchall()
        
        if not alerts:
            print("❌ No alerts with high_priority_count found!")
            return False
        
        print(f"📊 TOTAL ALERTS ANALYZED: {len(alerts)}")
        print()
        
        # Categorize by results
        wins = [a for a in alerts if a.get('match_finished') and a.get('result') == 'WIN']
        losses = [a for a in alerts if a.get('match_finished') and a.get('result') == 'LOSS']
        refunds = [a for a in alerts if a.get('match_finished') and a.get('result') == 'REFUND']
        pending = [a for a in alerts if not a.get('match_finished')]
        
        print(f"🎯 RESULTS BREAKDOWN:")
        print(f"   • WINS: {len(wins)}")
        print(f"   • LOSSES: {len(losses)}")
        print(f"   • REFUNDS: {len(refunds)}")
        print(f"   • PENDING: {len(pending)}")
        
        if len(wins) + len(losses) + len(refunds) > 0:
            total_finished = len(wins) + len(losses) + len(refunds)
            win_rate = (len(wins) / total_finished) * 100
            refund_rate = (len(refunds) / total_finished) * 100
            print(f"   • WIN RATE: {win_rate:.1f}%")
            print(f"   • REFUND RATE: {refund_rate:.1f}%")
        
        print("\n" + "="*70)
        
        # Analyze high priority patterns
        if wins or losses or refunds:
            print("🏆 HIGH PRIORITY PATTERN ANALYSIS:")
            
            # Group by high_priority_count
            priority_performance = defaultdict(lambda: {'wins': 0, 'losses': 0, 'refunds': 0, 'total': 0})
            
            for alert in wins + losses + refunds:
                priority = alert['high_priority_count']
                priority_performance[priority]['total'] += 1
                if alert.get('result') == 'WIN':
                    priority_performance[priority]['wins'] += 1
                elif alert.get('result') == 'LOSS':
                    priority_performance[priority]['losses'] += 1
                elif alert.get('result') == 'REFUND':
                    priority_performance[priority]['refunds'] += 1
            
            print("\n📈 PERFORMANCE BY HIGH PRIORITY COUNT:")
            for priority in sorted(priority_performance.keys()):
                data = priority_performance[priority]
                if data['total'] > 0:
                    win_rate = (data['wins'] / data['total']) * 100
                    refund_rate = (data['refunds'] / data['total']) * 100
                    print(f"   Priority {priority}: {data['wins']}W-{data['losses']}L-{data['refunds']}R ({win_rate:.1f}% wins, {refund_rate:.1f}% refunds)")
        
        # Analyze corner patterns
        if wins or losses or refunds:
            print("\n⚽ CORNER COUNT ANALYSIS:")
            
            corner_performance = defaultdict(lambda: {'wins': 0, 'losses': 0, 'refunds': 0, 'total': 0})
            
            for alert in wins + losses + refunds:
                corners = alert.get('corners_at_alert', 0)
                corner_performance[corners]['total'] += 1
                if alert.get('result') == 'WIN':
                    corner_performance[corners]['wins'] += 1
                elif alert.get('result') == 'LOSS':
                    corner_performance[corners]['losses'] += 1
                elif alert.get('result') == 'REFUND':
                    corner_performance[corners]['refunds'] += 1
            
            print("\n📊 PERFORMANCE BY CORNER COUNT:")
            for corners in sorted(corner_performance.keys()):
                data = corner_performance[corners]
                if data['total'] > 0:
                    win_rate = (data['wins'] / data['total']) * 100
                    refund_rate = (data['refunds'] / data['total']) * 100
                    print(f"   {corners} corners: {data['wins']}W-{data['losses']}L-{data['refunds']}R ({win_rate:.1f}% wins, {refund_rate:.1f}% refunds)")
        
        # Analyze shots on target patterns
        if wins or losses or refunds:
            print("\n🎯 SHOTS ON TARGET ANALYSIS:")
            
            sot_performance = defaultdict(lambda: {'wins': 0, 'losses': 0, 'refunds': 0, 'total': 0})
            
            for alert in wins + losses + refunds:
                total_sot = alert.get('total_shots_on_target', 0)
                if total_sot > 0:  # Only analyze alerts that have SOT data
                    sot_performance[total_sot]['total'] += 1
                    if alert.get('result') == 'WIN':
                        sot_performance[total_sot]['wins'] += 1
                    elif alert.get('result') == 'LOSS':
                        sot_performance[total_sot]['losses'] += 1
                    elif alert.get('result') == 'REFUND':
                        sot_performance[total_sot]['refunds'] += 1
            
            if sot_performance:
                print("\n📈 PERFORMANCE BY TOTAL SHOTS ON TARGET:")
                for sot in sorted(sot_performance.keys()):
                    data = sot_performance[sot]
                    if data['total'] > 0:
                        win_rate = (data['wins'] / data['total']) * 100
                        refund_rate = (data['refunds'] / data['total']) * 100
                        print(f"   {sot} SOT: {data['wins']}W-{data['losses']}L-{data['refunds']}R ({win_rate:.1f}% wins, {refund_rate:.1f}% refunds)")
                
                # SOT rule validation
                high_sot_alerts = [a for a in wins + losses + refunds if a.get('total_shots_on_target', 0) >= 8]
                if high_sot_alerts:
                    high_sot_wins = len([a for a in high_sot_alerts if a.get('result') == 'WIN'])
                    high_sot_total = len(high_sot_alerts)
                    high_sot_win_rate = (high_sot_wins / high_sot_total) * 100
                    print(f"\n🔍 8+ SOT RULE VALIDATION: {high_sot_wins}/{high_sot_total} alerts won ({high_sot_win_rate:.1f}% win rate)")
            else:
                print("\n⚠️  No SOT data available in alerts yet (new feature)")
                print("     Future alerts will include this analysis")
        
        # Show individual alert details
        print("\n" + "="*70)
        print("📋 DETAILED ALERT BREAKDOWN:")
        
        if wins:
            print(f"\n🏆 WINNING ALERTS ({len(wins)}):")
            for alert in wins:
                priority_ratio = alert.get('high_priority_ratio', 'N/A')
                corners = alert.get('corners_at_alert', 'N/A')
                odds = alert.get('over_odds', 'N/A')
                line = alert.get('over_line', 'N/A')
                total_sot = alert.get('total_shots_on_target', 'N/A')
                home_sot = alert.get('home_shots_on_target', 'N/A')
                away_sot = alert.get('away_shots_on_target', 'N/A')
                print(f"   ✅ {alert['teams']} | {corners} corners | SOT: {total_sot} ({home_sot}-{away_sot}) | Priority: {priority_ratio} | Over {line} @ {odds}")
        
        if refunds:
            print(f"\n🔄 REFUND ALERTS ({len(refunds)}):")
            for alert in refunds:
                priority_ratio = alert.get('high_priority_ratio', 'N/A')
                corners = alert.get('corners_at_alert', 'N/A')
                odds = alert.get('over_odds', 'N/A')
                line = alert.get('over_line', 'N/A')
                total_sot = alert.get('total_shots_on_target', 'N/A')
                home_sot = alert.get('home_shots_on_target', 'N/A')
                away_sot = alert.get('away_shots_on_target', 'N/A')
                print(f"   🔄 {alert['teams']} | {corners} corners | SOT: {total_sot} ({home_sot}-{away_sot}) | Priority: {priority_ratio} | Over {line} @ {odds}")
        
        if losses:
            print(f"\n❌ LOSING ALERTS ({len(losses)}):")
            for alert in losses:
                priority_ratio = alert.get('high_priority_ratio', 'N/A')
                corners = alert.get('corners_at_alert', 'N/A')
                odds = alert.get('over_odds', 'N/A')
                line = alert.get('over_line', 'N/A')
                total_sot = alert.get('total_shots_on_target', 'N/A')
                home_sot = alert.get('home_shots_on_target', 'N/A')
                away_sot = alert.get('away_shots_on_target', 'N/A')
                print(f"   ❌ {alert['teams']} | {corners} corners | SOT: {total_sot} ({home_sot}-{away_sot}) | Priority: {priority_ratio} | Over {line} @ {odds}")
        
        if pending:
            print(f"\n⏳ PENDING ALERTS ({len(pending)}):")
            for alert in pending:
                priority_ratio = alert.get('high_priority_ratio', 'N/A')
                corners = alert.get('corners_at_alert', 'N/A')
                odds = alert.get('over_odds', 'N/A')
                line = alert.get('over_line', 'N/A')
                total_sot = alert.get('total_shots_on_target', 'N/A')
                home_sot = alert.get('home_shots_on_target', 'N/A')
                away_sot = alert.get('away_shots_on_target', 'N/A')
                print(f"   ⏳ {alert['teams']} | {corners} corners | SOT: {total_sot} ({home_sot}-{away_sot}) | Priority: {priority_ratio} | Over {line} @ {odds}")
        
        # Key insights
        print("\n" + "="*70)
        print("💡 KEY INSIGHTS & CORRELATIONS:")
        
        if len(wins) + len(losses) + len(refunds) > 0:
            # Find best performing priority levels
            best_priority = None
            best_win_rate = 0
            for priority, data in priority_performance.items():
                if data['total'] >= 2:  # Only consider priorities with 2+ alerts
                    win_rate = (data['wins'] / data['total']) * 100
                    if win_rate > best_win_rate:
                        best_win_rate = win_rate
                        best_priority = priority
            
            if best_priority:
                print(f"   🎯 Best performing priority level: {best_priority} ({best_win_rate:.1f}% win rate)")
            
            # Find best performing corner counts
            best_corners = None
            best_corner_win_rate = 0
            for corners, data in corner_performance.items():
                if data['total'] >= 2:  # Only consider corner counts with 2+ alerts
                    win_rate = (data['wins'] / data['total']) * 100
                    if win_rate > best_corner_win_rate:
                        best_corner_win_rate = win_rate
                        best_corners = corners
            
            if best_corners:
                print(f"   ⚽ Best performing corner count: {best_corners} corners ({best_corner_win_rate:.1f}% win rate)")
            
            # Overall system performance
            total_finished = len(wins) + len(losses) + len(refunds)
            profitable = len(wins) + len(refunds)  # Assuming refunds don't lose money
            profitability = (profitable / total_finished) * 100
            print(f"   💰 Overall profitability: {profitability:.1f}% (wins + refunds)")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = analyze_alert_performance()
    sys.exit(0 if success else 1) 