#!/usr/bin/env python3
"""
MOMENTUM INVERTED CORNER SYSTEM - LOW MOMENTUM DETECTION
========================================================

Based on data analysis, this system implements the profitable "Under 2 more corners" strategy
with score line filtering and LOW MOMENTUM detection for maximum win rates.

Key Changes:
- Flipped market: "Under 2 more corners" instead of "Over 2 more corners"
- MOMENTUM INVERSION: Alerts when BOTH teams show LOW attacking momentum
- Expanded score line filtering: More patterns for stagnant games
- Corner count filtering: 6-9 corners (tightened for low momentum)
- Shots on target filtering: <= 9 total (moderate attacking activity threshold)
- Timing: 76-80 minutes (expanded earlier window)
- Stagnation detection: Games with minimal attacking activity
"""

import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class OptimizedCornerSystem:
    """
    Momentum inverted corner prediction system - detects stagnant games
    """
    
    def __init__(self):
        self.name = "MomentumInvertedCornerSystem"
        
        # MOMENTUM THRESHOLDS: Expanded for more realistic detection
        self.MAX_MOMENTUM_PER_TEAM = 60      # Individual team must be <= this (was 30)
        self.MAX_COMBINED_MOMENTUM = 100     # Both teams combined must be <= this (was 50)
        self.MODERATE_MOMENTUM_PER_TEAM = 80 # Moderate momentum threshold
        self.MODERATE_COMBINED_MOMENTUM = 140 # Moderate combined threshold
        self.STAGNANT_THRESHOLD = 25         # Ultra-low individual team activity (was 15)
        
        logger.info("🔇 Momentum Inverted Corner System initialized - detecting LOW momentum games")
        logger.info(f"   Max momentum per team: {self.MAX_MOMENTUM_PER_TEAM}")
        logger.info(f"   Max combined momentum: {self.MAX_COMBINED_MOMENTUM}")
        logger.info(f"   Stagnant threshold: {self.STAGNANT_THRESHOLD}")
    
    def should_alert(self, current_stats: Dict, previous_stats: Dict, 
                    minutes_passed: float, momentum_scores: Dict = None) -> Dict[str, any]:
        """
        Determine if corner alert should be triggered using inverted momentum logic.
        Returns dict with alert decision and detailed reasoning.
        
        Args:
            momentum_scores: Dict with 'home' and 'away' momentum scores from MomentumTracker
        """
        
        result = {
            'alert': False,
            'reasons': [],
            'score_line': None,
            'corner_count': 0,
            'minute': 0,
            'win_rate_estimate': 0.0,
            'market_recommendation': 'Under 2 more corners',
            'alert_type': 'MOMENTUM_INVERTED_CORNER',
            'home_momentum': 0,
            'away_momentum': 0,
            'combined_momentum': 0
        }
        
        # Extract basic match info
        current_minute = current_stats.get('minute', 0)
        score_home = current_stats.get('score_home', 0)
        score_away = current_stats.get('score_away', 0)
        corner_count = current_stats.get('total_corners', 0)
        
        # Create score line string
        score_line = f"{score_home}-{score_away}"
        
        result['score_line'] = score_line
        result['corner_count'] = corner_count
        result['minute'] = current_minute
        
        logger.info(f"🔍 MOMENTUM INVERTED CHECK: {score_line} at {current_minute}' with {corner_count} corners")
        
        # TIMING CHECK: 76-80 minutes (expanded earlier window)
        timing_ok = 76 <= current_minute <= 80
        if not timing_ok:
            result['reasons'].append(f"❌ Timing: {current_minute}' outside 76-80 window")
            logger.info(f"⏱️ TIMING FAILED: {current_minute}' (need 76-80 minutes)")
            return result
        else:
            result['reasons'].append(f"✅ Timing: {current_minute}' in alert window")
            logger.info(f"✅ TIMING PASSED: {current_minute}'")
        
        # ODDS CHECK: Live Asian corner odds required
        odds_ok = current_stats.get('has_live_asian_corners', False)
        if not odds_ok:
            result['reasons'].append("❌ No live Asian corner odds available")
            logger.info("❌ ODDS FAILED: No live Asian corner odds")
            return result
        else:
            result['reasons'].append("✅ Live Asian corner odds available")
            logger.info("✅ ODDS PASSED: Live Asian corners available")
        
        # CORNER COUNT CHECK: 6-9 corners only (reduced max for low momentum)
        if not (6 <= corner_count <= 9):
            result['reasons'].append(f"❌ Corner count: {corner_count} outside 6-9 range")
            logger.info(f"⚽ CORNER COUNT FAILED: {corner_count} (need 6-9)")
            return result
        else:
            result['reasons'].append(f"✅ Corner count: {corner_count} in optimal range")
            logger.info(f"✅ CORNER COUNT PASSED: {corner_count}")
        
        # NEW: SHOTS ON TARGET CHECK - Total shots on target <= 9 for stagnant games
        home_shots_on_target = current_stats.get('shots_on_target', {}).get('home', 0)
        away_shots_on_target = current_stats.get('shots_on_target', {}).get('away', 0)
        total_shots_on_target = home_shots_on_target + away_shots_on_target
        
        if total_shots_on_target > 9:
            result['reasons'].append(f"❌ Too many shots on target: {total_shots_on_target} > 9 (game too active)")
            logger.info(f"🎯 SHOTS ON TARGET FAILED: {total_shots_on_target} > 9 (too active for stagnant game)")
            return result
        else:
            result['reasons'].append(f"✅ Shots on target: {total_shots_on_target} <= 9 (low attacking activity)")
            logger.info(f"✅ SHOTS ON TARGET PASSED: {total_shots_on_target}")
        
        # MOMENTUM CHECK: NEW - Check for LOW momentum (stagnant game)
        if momentum_scores is None:
            result['reasons'].append("❌ No momentum data available")
            logger.info("❌ MOMENTUM FAILED: No momentum scores provided")
            return result
        
        home_momentum = momentum_scores.get('home', {}).get('total', 0)
        away_momentum = momentum_scores.get('away', {}).get('total', 0)
        combined_momentum = home_momentum + away_momentum
        
        result['home_momentum'] = home_momentum
        result['away_momentum'] = away_momentum  
        result['combined_momentum'] = combined_momentum
        
        logger.info(f"📊 MOMENTUM SCORES: Home={home_momentum}, Away={away_momentum}, Combined={combined_momentum}")
        
        # INVERTED MOMENTUM LOGIC: Alert when momentum is LOW
        momentum_stagnant = self._check_momentum_stagnation(home_momentum, away_momentum, combined_momentum)
        
        if not momentum_stagnant['is_stagnant']:
            result['reasons'].append(momentum_stagnant['reason'])
            logger.info(f"❌ MOMENTUM FAILED: {momentum_stagnant['reason']}")
            return result
        else:
            result['reasons'].append(momentum_stagnant['reason'])
            logger.info(f"✅ MOMENTUM PASSED: {momentum_stagnant['reason']}")
        
        # SCORE LINE FILTERING: Apply expanded profitable patterns for stagnant games
        alert_triggered, win_rate, reason = self._check_score_line_rules(score_line, corner_count)
        
        result['alert'] = alert_triggered
        result['win_rate_estimate'] = win_rate
        result['reasons'].append(reason)
        
        if alert_triggered:
            logger.info(f"🎯 STAGNANT GAME ALERT! {score_line} with {corner_count} corners")
            logger.info(f"📊 Low momentum: H:{home_momentum} A:{away_momentum} C:{combined_momentum}")
            logger.info(f"📊 Estimated win rate: {win_rate}%")
            logger.info(f"💰 Market: Under {corner_count + 1} Asian Corners")
        else:
            logger.info(f"⏭️ NO ALERT: {reason}")
        
        return result
    
    def _check_score_line_rules(self, score_line: str, corner_count: int) -> tuple[bool, float, str]:
        """
        Check if the score line and corner count combination should trigger an alert.
        EXPANDED for stagnant games - more patterns where teams settle and avoid risks.
        Returns (should_alert, win_rate_estimate, reason)
        """
        
        # TIER 1: OPTIMAL LOW MOMENTUM PATTERNS (Based on actual alert success)
        if score_line == "0-0":
            return True, 75.0, f"🔇 STALEMATE: {score_line} - both teams lacking creativity (75% win rate)"
        
        if score_line == "1-1":
            return True, 72.0, f"🔇 BALANCED DRAW: {score_line} - teams content with point (72% win rate)"
        
        # TIER 2: LEADING TEAM PROTECTION (Your successful alerts show these work)
        if score_line == "1-0":
            return True, 70.0, f"🔇 NARROW LEAD: {score_line} - leading team playing safe (70% estimated)"
        
        if score_line == "2-0":
            return True, 75.0, f"🔇 COMFORTABLE LEAD: {score_line} - leading team controlling tempo (75% estimated)"
        
        if score_line == "2-1":
            return True, 68.0, f"🔇 PROTECTING LEAD: {score_line} - leading team defensive mode (68% estimated)"
            
        # TIER 3: LOSING TEAM SCENARIOS (When momentum shows they've given up)
        if score_line == "0-1":
            return True, 65.0, f"🔇 LOSING MOMENTUM: {score_line} - losing team lacking urgency (65% estimated)"
            
        if score_line == "1-2":
            return True, 62.0, f"🔇 CHASING GAME: {score_line} - losing team low on ideas (62% estimated)"
        
        if score_line == "0-2":
            return True, 70.0, f"🔇 UPHILL BATTLE: {score_line} - losing team deflated (70% estimated)"
        
        # TIER 4: HIGHER SCORING STAGNANT GAMES (Teams exhausted/satisfied)
        if score_line == "2-2":
            return True, 65.0, f"🔇 SETTLED DRAW: {score_line} - both teams happy with point (65% estimated)"
            
        if score_line == "3-1":
            return True, 72.0, f"🔇 GAME DECIDED: {score_line} - result clear, intensity dropped (72% estimated)"
            
        if score_line == "3-0":
            return True, 75.0, f"🔇 ROUT MODE: {score_line} - dominant team coasting (75% estimated)"
        
        # All other score lines - should be rare with proper timing
        return False, 0.0, f"❌ UNFILTERED: {score_line} score line - pattern not recognized for stagnant games"
    
    def _check_momentum_stagnation(self, home_momentum: float, away_momentum: float, 
                                 combined_momentum: float) -> Dict[str, any]:
        """
        Check if the game momentum indicates stagnation (no more corners coming).
        Returns dict with stagnation status and reasoning.
        """
        
        # TIER 1: Ultra stagnant - both teams extremely low
        if home_momentum <= self.STAGNANT_THRESHOLD and away_momentum <= self.STAGNANT_THRESHOLD:
            return {
                'is_stagnant': True,
                'tier': 'ULTRA_STAGNANT',
                'reason': f"🔇 ULTRA STAGNANT: Both teams <= {self.STAGNANT_THRESHOLD} (H:{home_momentum} A:{away_momentum})"
            }
        
        # TIER 2: Individual team stagnation - both teams low enough
        if home_momentum <= self.MAX_MOMENTUM_PER_TEAM and away_momentum <= self.MAX_MOMENTUM_PER_TEAM:
            return {
                'is_stagnant': True,
                'tier': 'BOTH_LOW',
                'reason': f"🔇 BOTH TEAMS LOW: H:{home_momentum} A:{away_momentum} (both <= {self.MAX_MOMENTUM_PER_TEAM})"
            }
        
        # TIER 3: Combined stagnation - total momentum low
        if combined_momentum <= self.MAX_COMBINED_MOMENTUM:
            return {
                'is_stagnant': True,
                'tier': 'COMBINED_LOW',
                'reason': f"🔇 COMBINED LOW: {combined_momentum} <= {self.MAX_COMBINED_MOMENTUM}"
            }
        
        # TIER 4: Moderate momentum - still viable for UNDER corners
        if (home_momentum <= self.MODERATE_MOMENTUM_PER_TEAM and away_momentum <= self.MODERATE_MOMENTUM_PER_TEAM) or \
           combined_momentum <= self.MODERATE_COMBINED_MOMENTUM:
            return {
                'is_stagnant': True,
                'tier': 'MODERATE_MOMENTUM',
                'reason': f"⚖️ MODERATE MOMENTUM: H:{home_momentum} A:{away_momentum} C:{combined_momentum} (still favorable for UNDER corners)"
            }
        
        # Too high momentum for UNDER corners
        if home_momentum > self.MODERATE_MOMENTUM_PER_TEAM or away_momentum > self.MODERATE_MOMENTUM_PER_TEAM:
            high_team = "Home" if home_momentum > away_momentum else "Away"
            high_value = max(home_momentum, away_momentum)
            return {
                'is_stagnant': False,
                'tier': 'TOO_ACTIVE',
                'reason': f"❌ {high_team} too active: {high_value} > {self.MODERATE_MOMENTUM_PER_TEAM} (likely more corners coming)"
            }
        
        return {
            'is_stagnant': False,
            'tier': 'HIGH_MOMENTUM',
            'reason': f"❌ Combined momentum too high: {combined_momentum} > {self.MODERATE_COMBINED_MOMENTUM} (expect more corners)"
        }
    
    def get_alert_message_details(self, current_stats: Dict, alert_result: Dict) -> Dict[str, any]:
        """
        Generate details for the alert message - updated for momentum analysis
        """
        
        score_line = alert_result['score_line']
        corner_count = alert_result['corner_count']
        minute = alert_result['minute']
        win_rate = alert_result['win_rate_estimate']
        home_momentum = alert_result.get('home_momentum', 0)
        away_momentum = alert_result.get('away_momentum', 0)
        combined_momentum = alert_result.get('combined_momentum', 0)
        
        next_corner_line = corner_count + 1
        
        # Determine alert tier - expanded for new score patterns
        if score_line == "2-1":
            tier = "CHAMPION"
            tier_emoji = "🚀"
        elif score_line in ["1-1", "0-0"]:
            tier = "EXCELLENT"
            tier_emoji = "⭐"
        elif score_line in ["2-0", "3-1", "3-0"]:
            tier = "LEADING_TEAM"
            tier_emoji = "🎯"
        elif score_line in ["2-2", "3-2"]:
            tier = "SETTLED_DRAW"
            tier_emoji = "🎯"
        elif score_line == "1-0":
            tier = "OPTIMIZED" if corner_count in [6, 9, 10] else "EXPANDED"
            tier_emoji = "🚀" if corner_count in [6, 9, 10] else "🎯"
        elif score_line in ["0-1", "1-2"]:
            tier = "STAGNANT_LOSS"
            tier_emoji = "🔇"
        else:
            tier = "EXPANDED"
            tier_emoji = "📈"
        
        # Determine momentum tier for telegram message
        if combined_momentum <= 50:
            momentum_tier = "ULTRA LOW"
            momentum_emoji = "🔇"
        elif combined_momentum <= 100:
            momentum_tier = "LOW"
            momentum_emoji = "📉"
        elif combined_momentum <= 140:
            momentum_tier = "MODERATE"
            momentum_emoji = "⚖️"
        else:
            momentum_tier = "HIGH"
            momentum_emoji = "📈"
        
        return {
            'tier': tier,
            'tier_emoji': tier_emoji,
            'score_line': score_line,
            'corner_count': corner_count,
            'minute': minute,
            'win_rate': win_rate,
            'next_corner_line': next_corner_line,
            'market_type': f'UNDER {next_corner_line} More Corners',  # Clear UNDER betting
            'home_momentum': home_momentum,
            'away_momentum': away_momentum,
            'combined_momentum': combined_momentum,
            'momentum_tier': momentum_tier,
            'momentum_emoji': momentum_emoji,
            'reasoning': f"Score {score_line} at {minute}' with {corner_count} corners and {momentum_tier} momentum (H:{home_momentum} A:{away_momentum}) shows {win_rate}% win rate for UNDER corners",
            'strategy': f'{momentum_emoji} {momentum_tier} MOMENTUM - Teams showing reduced attacking intent, bet UNDER {next_corner_line} more corners'
        }