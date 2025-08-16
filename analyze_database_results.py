#!/usr/bin/env python3
"""
DATABASE RESULTS ANALYZER
=========================
Comprehensive analysis of PostgreSQL database to identify:
- Which corner counts have highest win rates
- Which stats combinations bring most wins/refunds vs losses
- Performance patterns for different alert types
- Optimal thresholds and conditions

This will help optimize the alert system for maximum profitability.
"""

import os
import psycopg2
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict

# Ensure DATABASE_URL is set
if 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = 'postgresql://postgres:jIwhlnuBmXDEiHjndVZzCmxNEkpquJAL@trolley.proxy.rlwy.net:24044/railway'

class DatabaseAnalyzer:
    """Analyze alert performance patterns from PostgreSQL database"""
    
    def __init__(self):
        self.db_url = os.environ['DATABASE_URL']
        self.conn = None
        self.results = {}
        
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(self.db_url)
            print("✅ Connected to PostgreSQL database")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def get_all_alerts(self):
        """Get all alerts with their results"""
        query = """
        SELECT 
            id, fixture_id, match_name, corners_at_alert, actual_result,
            created_at, elite_score, over_line, alert_type,
            attack_intensity, shot_efficiency, corner_momentum, score_context,
            total_probability, detected_patterns,
            home_shots_on_target, away_shots_on_target, total_shots_on_target,
            corners_last_15, dangerous_attacks_last_5, attacks_last_5
        FROM alerts 
        ORDER BY created_at DESC
        """
        
        try:
            df = pd.read_sql_query(query, self.conn)
            print(f"📊 Loaded {len(df)} alerts from database")
            return df
        except Exception as e:
            print(f"❌ Error loading alerts: {e}")
            return pd.DataFrame()
    
    def analyze_corner_count_performance(self, df):
        """Analyze performance by corner count at time of alert"""
        print("\n🎯 CORNER COUNT PERFORMANCE ANALYSIS")
        print("=" * 50)
        
        corner_analysis = df.groupby('corners_at_alert').agg({
            'actual_result': ['count', lambda x: (x == 'WIN').sum(), lambda x: (x == 'LOSS').sum(), lambda x: (x == 'REFUND').sum()],
            'elite_score': 'mean'
        }).round(2)
        
        corner_analysis.columns = ['Total_Alerts', 'Wins', 'Losses', 'Refunds', 'Avg_Elite_Score']
        corner_analysis['Win_Rate'] = (corner_analysis['Wins'] / corner_analysis['Total_Alerts'] * 100).round(1)
        corner_analysis['Loss_Rate'] = (corner_analysis['Losses'] / corner_analysis['Total_Alerts'] * 100).round(1)
        corner_analysis['Profit_Rate'] = corner_analysis['Win_Rate'] - corner_analysis['Loss_Rate']
        
        # Sort by profit rate (wins - losses)
        corner_analysis = corner_analysis.sort_values('Profit_Rate', ascending=False)
        
        print(corner_analysis)
        
        # Find best and worst performers
        best_corner = corner_analysis.index[0]
        worst_corner = corner_analysis.index[-1]
        
        print(f"\n🏆 BEST PERFORMING CORNER COUNT: {best_corner}")
        print(f"   Win Rate: {corner_analysis.loc[best_corner, 'Win_Rate']}%")
        print(f"   Profit Rate: {corner_analysis.loc[best_corner, 'Profit_Rate']}%")
        
        print(f"\n💔 WORST PERFORMING CORNER COUNT: {worst_corner}")
        print(f"   Win Rate: {corner_analysis.loc[worst_corner, 'Win_Rate']}%")
        print(f"   Profit Rate: {corner_analysis.loc[worst_corner, 'Profit_Rate']}%")
        
        self.results['corner_analysis'] = corner_analysis
        return corner_analysis
    
    def analyze_elite_score_ranges(self, df):
        """Analyze performance by elite score ranges"""
        print("\n🎖️ ELITE SCORE PERFORMANCE ANALYSIS")
        print("=" * 50)
        
        # Create score ranges
        df['score_range'] = pd.cut(df['elite_score'], 
                                 bins=[0, 15, 20, 25, 30, 100], 
                                 labels=['0-15', '15-20', '20-25', '25-30', '30+'])
        
        score_analysis = df.groupby('score_range').agg({
            'actual_result': ['count', lambda x: (x == 'WIN').sum(), lambda x: (x == 'LOSS').sum()],
        })
        
        score_analysis.columns = ['Total', 'Wins', 'Losses']
        score_analysis['Win_Rate'] = (score_analysis['Wins'] / score_analysis['Total'] * 100).round(1)
        score_analysis['Profit_Rate'] = score_analysis['Win_Rate'] - (score_analysis['Losses'] / score_analysis['Total'] * 100)
        
        print(score_analysis)
        self.results['score_analysis'] = score_analysis
        return score_analysis
    
    def analyze_stats_combinations(self, df):
        """Analyze which stat combinations perform best"""
        print("\n📈 STATS COMBINATIONS ANALYSIS")
        print("=" * 50)
        
        # Filter out rows with null values for key stats
        stats_df = df.dropna(subset=['attack_intensity', 'shot_efficiency', 'corner_momentum', 'total_probability'])
        
        if len(stats_df) == 0:
            print("⚠️ No alerts with complete stats data found")
            return None
        
        # Create performance categories
        high_attack = stats_df['attack_intensity'] >= 70
        high_shots = stats_df['shot_efficiency'] >= 70  
        high_momentum = stats_df['corner_momentum'] >= 70
        high_probability = stats_df['total_probability'] >= 80
        
        # Analyze combinations
        combinations = {
            'High Attack + High Shots': high_attack & high_shots,
            'High Momentum + High Probability': high_momentum & high_probability,
            'All High (70%+ each)': high_attack & high_shots & high_momentum,
            'Super High Probability (90%+)': stats_df['total_probability'] >= 90,
            'Balanced High (all 60%+)': (stats_df['attack_intensity'] >= 60) & 
                                      (stats_df['shot_efficiency'] >= 60) & 
                                      (stats_df['corner_momentum'] >= 60)
        }
        
        combo_results = {}
        for combo_name, mask in combinations.items():
            subset = stats_df[mask]
            if len(subset) > 0:
                wins = (subset['actual_result'] == 'WIN').sum()
                losses = (subset['actual_result'] == 'LOSS').sum()
                total = len(subset)
                win_rate = (wins / total * 100).round(1)
                
                combo_results[combo_name] = {
                    'Total': total,
                    'Wins': wins,
                    'Losses': losses,
                    'Win_Rate': win_rate,
                    'Profit_Rate': win_rate - (losses / total * 100)
                }
        
        combo_df = pd.DataFrame(combo_results).T
        combo_df = combo_df.sort_values('Profit_Rate', ascending=False)
        
        print(combo_df)
        self.results['combo_analysis'] = combo_df
        return combo_df
    
    def analyze_alert_types(self, df):
        """Analyze performance by alert type (first half vs late game)"""
        print("\n⏰ ALERT TYPE PERFORMANCE ANALYSIS")
        print("=" * 50)
        
        type_analysis = df.groupby('alert_type').agg({
            'actual_result': ['count', lambda x: (x == 'WIN').sum(), lambda x: (x == 'LOSS').sum()],
            'elite_score': 'mean'
        })
        
        type_analysis.columns = ['Total', 'Wins', 'Losses', 'Avg_Score']
        type_analysis['Win_Rate'] = (type_analysis['Wins'] / type_analysis['Total'] * 100).round(1)
        type_analysis['Profit_Rate'] = type_analysis['Win_Rate'] - (type_analysis['Losses'] / type_analysis['Total'] * 100)
        
        print(type_analysis)
        self.results['type_analysis'] = type_analysis
        return type_analysis
    
    def analyze_recent_trends(self, df):
        """Analyze recent performance trends"""
        print("\n📅 RECENT TRENDS ANALYSIS (Last 7 Days)")
        print("=" * 50)
        
        # Recent alerts (last 7 days)
        recent_cutoff = datetime.now() - timedelta(days=7)
        recent_df = df[df['created_at'] >= recent_cutoff]
        
        if len(recent_df) == 0:
            print("⚠️ No alerts in the last 7 days")
            return None
        
        print(f"Recent alerts: {len(recent_df)}")
        
        recent_summary = recent_df['actual_result'].value_counts()
        recent_win_rate = (recent_summary.get('WIN', 0) / len(recent_df) * 100).round(1)
        
        print(f"Recent win rate: {recent_win_rate}%")
        print("Recent results breakdown:")
        print(recent_summary)
        
        self.results['recent_analysis'] = {
            'total': len(recent_df),
            'win_rate': recent_win_rate,
            'breakdown': recent_summary.to_dict()
        }
        
        return recent_summary
    
    def find_optimal_thresholds(self, df):
        """Find optimal thresholds for various metrics"""
        print("\n🎯 OPTIMAL THRESHOLDS ANALYSIS")
        print("=" * 50)
        
        stats_df = df.dropna(subset=['total_probability', 'elite_score'])
        
        if len(stats_df) == 0:
            print("⚠️ No data available for threshold analysis")
            return None
        
        thresholds_to_test = {
            'total_probability': [70, 75, 80, 85, 90, 95],
            'elite_score': [15, 16, 18, 20, 22, 25]
        }
        
        threshold_results = {}
        
        for metric, thresholds in thresholds_to_test.items():
            threshold_results[metric] = {}
            
            for threshold in thresholds:
                subset = stats_df[stats_df[metric] >= threshold]
                if len(subset) > 5:  # Minimum sample size
                    wins = (subset['actual_result'] == 'WIN').sum()
                    total = len(subset)
                    win_rate = (wins / total * 100).round(1)
                    
                    threshold_results[metric][threshold] = {
                        'alerts': total,
                        'win_rate': win_rate
                    }
        
        # Display results
        for metric, results in threshold_results.items():
            print(f"\n{metric.upper()} Thresholds:")
            for threshold, data in results.items():
                print(f"  >={threshold}: {data['alerts']} alerts, {data['win_rate']}% win rate")
        
        self.results['threshold_analysis'] = threshold_results
        return threshold_results
    
    def generate_summary_report(self):
        """Generate overall summary and recommendations"""
        print("\n" + "="*60)
        print("🏆 SUMMARY REPORT & RECOMMENDATIONS")
        print("="*60)
        
        if 'corner_analysis' in self.results:
            best_corners = self.results['corner_analysis'].head(3)
            print(f"\n🎯 TOP 3 CORNER COUNTS:")
            for corner, data in best_corners.iterrows():
                print(f"   {corner} corners: {data['Win_Rate']}% win rate ({data['Total_Alerts']} alerts)")
        
        if 'combo_analysis' in self.results:
            best_combos = self.results['combo_analysis'].head(3)
            print(f"\n📈 TOP 3 STAT COMBINATIONS:")
            for combo, data in best_combos.iterrows():
                print(f"   {combo}: {data['Win_Rate']}% win rate ({data['Total']} alerts)")
        
        if 'type_analysis' in self.results:
            print(f"\n⏰ ALERT TYPE PERFORMANCE:")
            for alert_type, data in self.results['type_analysis'].iterrows():
                print(f"   {alert_type}: {data['Win_Rate']}% win rate ({data['Total']} alerts)")
        
        print(f"\n💡 RECOMMENDATIONS:")
        
        # Corner count recommendations
        if 'corner_analysis' in self.results:
            profitable_corners = self.results['corner_analysis'][self.results['corner_analysis']['Profit_Rate'] > 0]
            if len(profitable_corners) > 0:
                print(f"   ✅ Focus on corner counts: {list(profitable_corners.index)}")
            
            unprofitable_corners = self.results['corner_analysis'][self.results['corner_analysis']['Profit_Rate'] < -10]
            if len(unprofitable_corners) > 0:
                print(f"   ❌ Avoid corner counts: {list(unprofitable_corners.index)}")
        
        # Threshold recommendations
        if 'threshold_analysis' in self.results:
            prob_thresholds = self.results['threshold_analysis'].get('total_probability', {})
            best_prob_threshold = None
            best_prob_rate = 0
            
            for threshold, data in prob_thresholds.items():
                if data['win_rate'] > best_prob_rate and data['alerts'] >= 10:
                    best_prob_rate = data['win_rate']
                    best_prob_threshold = threshold
            
            if best_prob_threshold:
                print(f"   📊 Optimal probability threshold: >={best_prob_threshold}% ({best_prob_rate}% win rate)")
    
    def run_full_analysis(self):
        """Run complete database analysis"""
        print("🔍 STARTING COMPREHENSIVE DATABASE ANALYSIS")
        print("="*60)
        
        if not self.connect():
            return False
        
        try:
            # Load all alerts
            df = self.get_all_alerts()
            if df.empty:
                print("❌ No alerts found in database")
                return False
            
            # Run all analyses
            self.analyze_corner_count_performance(df)
            self.analyze_elite_score_ranges(df)
            self.analyze_stats_combinations(df)
            self.analyze_alert_types(df)
            self.analyze_recent_trends(df)
            self.find_optimal_thresholds(df)
            
            # Generate summary
            self.generate_summary_report()
            
            print(f"\n✅ Analysis complete! Analyzed {len(df)} total alerts.")
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return False
        
        finally:
            if self.conn:
                self.conn.close()
        
        return True

if __name__ == "__main__":
    analyzer = DatabaseAnalyzer()
    analyzer.run_full_analysis()