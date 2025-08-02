#!/usr/bin/env python3
"""
Performance Analyzer - View Alert Results & Patterns
===================================================
Analyze elite corner alert performance and identify winning patterns.
"""

import logging
from datetime import datetime
from typing import Dict, List
from collections import defaultdict
from database import get_database

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PerformanceAnalyzer:
    """Analyze elite corner alert performance"""
    
    def __init__(self):
        self.db = get_database()
    
    def show_full_report(self):
        """Show comprehensive performance report"""
        
        print("\n" + "="*60)
        print("🏆 ELITE CORNER ALERTS - PERFORMANCE REPORT")
        print("="*60)
        
        # Overall statistics
        self._show_overall_stats()
        
        # Recent alerts
        self._show_recent_alerts()
        
        # Pattern analysis
        self._show_pattern_analysis()
        
        # Recommendations
        self._show_recommendations()
    
    def _show_overall_stats(self):
        """Show overall performance statistics"""
        
        stats = self.db.get_performance_stats()
        
        if not stats or stats['total_alerts'] == 0:
            print("\n📊 OVERALL PERFORMANCE:")
            print("   No alerts tracked yet")
            return
        
        print(f"\n📊 OVERALL PERFORMANCE:")
        print(f"   📈 Total Alerts: {stats['total_alerts']}")
        print(f"   ✅ Wins: {stats['wins']} ({(stats['wins']/max(stats['total_alerts']-stats['pending'], 1)*100):.1f}%)")
        print(f"   ❌ Losses: {stats['losses']} ({(stats['losses']/max(stats['total_alerts']-stats['pending'], 1)*100):.1f}%)")
        print(f"   🔄 Refunds: {stats['refunds']} ({(stats['refunds']/max(stats['total_alerts']-stats['pending'], 1)*100):.1f}%)")
        print(f"   ⏳ Pending: {stats['pending']}")
        print(f"   🎯 Win Rate: {stats['win_rate']}%")
        
        # ROI calculation (assuming -1 for loss, +odds for win, 0 for refund)
        alerts = self.db.get_all_alerts()
        total_roi = 0
        bet_count = 0
        
        for alert in alerts:
            if alert['result'] in ['WIN', 'LOSS', 'REFUND']:
                bet_count += 1
                if alert['result'] == 'WIN':
                    try:
                        odds = float(alert['over_odds'])
                        total_roi += (odds - 1)  # Profit = odds - stake
                    except:
                        total_roi += 1  # Default profit
                elif alert['result'] == 'LOSS':
                    total_roi -= 1  # Lost stake
                # Refund = 0
        
        if bet_count > 0:
            roi_percentage = (total_roi / bet_count) * 100
            print(f"   💰 ROI: {roi_percentage:.1f}% ({total_roi:+.2f} units over {bet_count} bets)")
    
    def _show_recent_alerts(self, limit: int = 5):
        """Show recent alerts"""
        
        alerts = self.db.get_all_alerts(limit)
        
        if not alerts:
            print(f"\n📋 RECENT ALERTS: None")
            return
        
        print(f"\n📋 RECENT ALERTS (Last {len(alerts)}):")
        
        for alert in alerts:
            status = alert['result'] if alert['result'] else 'PENDING'
            status_emoji = {'WIN': '✅', 'LOSS': '❌', 'REFUND': '🔄', 'PENDING': '⏳'}.get(status, '❓')
            
            timestamp = datetime.fromisoformat(alert['timestamp']).strftime('%m/%d %H:%M')
            
            print(f"   {status_emoji} {timestamp} | {alert['teams']}")
            
            # Show high priority count if available
            priority_str = ""
            if alert.get('high_priority_count') is not None:
                priority_str = f" (Priority: {alert['high_priority_count']})"
            
            print(f"      📊 {alert['corners_at_alert']} corners @ 85'{priority_str} → Over {alert['over_line']} @ {alert['over_odds']}")
            
            if alert['final_corners'] is not None:
                print(f"      🏁 Final: {alert['final_corners']} corners → {status}")
            else:
                print(f"      ⏳ Result pending...")
            print()
    
    def _show_pattern_analysis(self):
        """Analyze patterns in winning vs losing alerts"""
        
        alerts = self.db.get_all_alerts()
        finished_alerts = [a for a in alerts if a['result'] in ['WIN', 'LOSS', 'REFUND']]
        
        if len(finished_alerts) < 3:
            print(f"\n🔍 PATTERN ANALYSIS: Need more finished alerts (have {len(finished_alerts)})")
            return
        
        print(f"\n🔍 PATTERN ANALYSIS ({len(finished_alerts)} finished alerts):")
        
        # Group by result
        wins = [a for a in finished_alerts if a['result'] == 'WIN']
        losses = [a for a in finished_alerts if a['result'] == 'LOSS']
        
        # Analyze elite score patterns
        if wins and losses:
            avg_win_score = sum(a['elite_score'] for a in wins) / len(wins)
            avg_loss_score = sum(a['elite_score'] for a in losses) / len(losses)
            
            print(f"   📈 Elite Score Patterns:")
            print(f"      ✅ Wins avg: {avg_win_score:.1f} ({len(wins)} alerts)")
            print(f"      ❌ Losses avg: {avg_loss_score:.1f} ({len(losses)} alerts)")
        
        # Analyze corner patterns
        if wins and losses:
            avg_win_corners = sum(a['corners_at_alert'] for a in wins) / len(wins)
            avg_loss_corners = sum(a['corners_at_alert'] for a in losses) / len(losses)
            
            print(f"   ⚽ Corner Patterns:")
            print(f"      ✅ Wins avg: {avg_win_corners:.1f} corners")
            print(f"      ❌ Losses avg: {avg_loss_corners:.1f} corners")
        
        # Analyze high priority patterns
        if wins and losses:
            # Filter alerts that have high_priority_count data (newer alerts)
            wins_with_priority = [a for a in wins if a.get('high_priority_count') is not None]
            losses_with_priority = [a for a in losses if a.get('high_priority_count') is not None]
            
            if wins_with_priority and losses_with_priority:
                avg_win_priority = sum(a['high_priority_count'] for a in wins_with_priority) / len(wins_with_priority)
                avg_loss_priority = sum(a['high_priority_count'] for a in losses_with_priority) / len(losses_with_priority)
                
                print(f"   ⭐ High Priority Patterns:")
                print(f"      ✅ Wins avg: {avg_win_priority:.1f} indicators ({len(wins_with_priority)} alerts)")
                print(f"      ❌ Losses avg: {avg_loss_priority:.1f} indicators ({len(losses_with_priority)} alerts)")
        
        # Analyze over line patterns
        line_performance = defaultdict(lambda: {'wins': 0, 'total': 0})
        for alert in finished_alerts:
            if alert['result'] != 'REFUND':  # Exclude refunds
                line = alert['over_line']
                line_performance[line]['total'] += 1
                if alert['result'] == 'WIN':
                    line_performance[line]['wins'] += 1
        
        if line_performance:
            print(f"   🎯 Line Performance:")
            for line, stats in sorted(line_performance.items()):
                win_rate = (stats['wins'] / stats['total']) * 100 if stats['total'] > 0 else 0
                print(f"      Over {line}: {stats['wins']}/{stats['total']} ({win_rate:.1f}% win rate)")
    
    def _show_recommendations(self):
        """Show recommendations based on current data"""
        
        alerts = self.db.get_all_alerts()
        finished_alerts = [a for a in alerts if a['result'] in ['WIN', 'LOSS', 'REFUND']]
        
        print(f"\n💡 RECOMMENDATIONS:")
        
        if len(finished_alerts) < 10:
            print(f"   📊 Collect more data: Need {10 - len(finished_alerts)} more finished alerts")
            print(f"   ⏰ Keep running: System learning patterns")
            return
        
        # Calculate win rate for high score alerts
        high_score_alerts = [a for a in finished_alerts if a['elite_score'] >= 10.0]
        if high_score_alerts:
            high_score_wins = len([a for a in high_score_alerts if a['result'] == 'WIN'])
            high_score_rate = (high_score_wins / len(high_score_alerts)) * 100
            print(f"   🎯 Elite Score 10+: {high_score_rate:.1f}% win rate ({high_score_wins}/{len(high_score_alerts)})")
        
        # Calculate win rate for different corner counts
        corner_patterns = defaultdict(lambda: {'wins': 0, 'total': 0})
        for alert in finished_alerts:
            if alert['result'] != 'REFUND':
                corners = alert['corners_at_alert']
                corner_patterns[corners]['total'] += 1
                if alert['result'] == 'WIN':
                    corner_patterns[corners]['wins'] += 1
        
        best_corners = None
        best_rate = 0
        for corners, stats in corner_patterns.items():
            if stats['total'] >= 2:  # At least 2 samples
                rate = (stats['wins'] / stats['total']) * 100
                if rate > best_rate:
                    best_rate = rate
                    best_corners = corners
        
        if best_corners:
            print(f"   ⚽ Best corner count: {best_corners} corners ({best_rate:.1f}% win rate)")
        
        print(f"   🚀 Continue monitoring: Every alert improves the model")

def main():
    """Main analyzer function"""
    
    analyzer = PerformanceAnalyzer()
    analyzer.show_full_report()
    
    print("\n" + "="*60)
    print("💾 Data stored in: alerts.db")
    print("🔄 Results checked hourly automatically")
    print("📊 Run this script anytime for updated analysis")
    print("="*60 + "\n")

if __name__ == "__main__":
    main() 