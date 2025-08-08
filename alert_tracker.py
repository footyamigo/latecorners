#!/usr/bin/env python3
"""
Alert Tracker - Save Elite Alerts to Database
=============================================
Automatically saves elite corner alerts for result tracking.
"""

import logging
from datetime import datetime
from typing import Dict, Optional, List
import re
try:
    from database import get_database
except Exception:
    from latecorners.database_postgres import get_database

logger = logging.getLogger(__name__)

class AlertTracker:
    """Track and save alerts from the new systems (Late Momentum and Draw Odds)."""
    
    def __init__(self):
        self.db = get_database()
    
    def save_elite_alert(self, match_data: Dict, tier: str, score: float, conditions: list,
                        momentum_indicators: Dict = None, detected_patterns: List[Dict] = None) -> bool:
        """Save a new-system alert to the database for tracking.

        Compatible with legacy schema while adding new columns for tier/draw_odds/momentum.
        """
        
        try:
            logger.info(f"💾 SAVING {tier} ALERT: {match_data.get('home_team')} vs {match_data.get('away_team')}")
            
            # Extract betting line and odds from active_odds
            over_line, over_odds = self._extract_over_bet(match_data.get('active_odds', []))
            
            # Calculate high priority ratio based on tier
            high_priority_count = match_data.get('high_priority_count', 0)
            if tier == "ELITE" or tier.startswith("TIER_1"):
                priority_required = 3  # Updated for Tier 1 system
            elif tier == "PREMIUM":
                priority_required = 1
            else:
                priority_required = 1  # Default fallback
            
            high_priority_ratio = f"{high_priority_count}/{priority_required}"
            
            # Base alert data
            alert_data = {
                'fixture_id': match_data.get('fixture_id'),
                'teams': f"{match_data.get('home_team')} vs {match_data.get('away_team')}",
                'score_at_alert': f"{match_data.get('home_score')}-{match_data.get('away_score')}",
                'minute_sent': match_data.get('minute'),
                'corners_at_alert': match_data.get('total_corners', 0),
                'alert_type': tier,  # store the tier name as alert type
                'draw_odds': match_data.get('draw_odds') or (momentum_indicators or {}).get('draw_odds'),
                'combined_momentum10': match_data.get('total_probability', 0),
                'asian_odds_snapshot': match_data.get('active_odds', []),
                
                # New metrics from the enhanced system
                'total_probability': score,
                'momentum_indicators': momentum_indicators or {},
                'detected_patterns': detected_patterns or []
            }
            
            # Add momentum indicators if available
            if momentum_indicators:
                alert_data.update({
                    'attack_intensity': momentum_indicators.get('attack_intensity', 0),
                    'shot_efficiency': momentum_indicators.get('shot_efficiency', 0),
                    'attack_volume': momentum_indicators.get('attack_volume', 0),
                    'corner_momentum': momentum_indicators.get('corner_momentum', 0),
                    'score_context': momentum_indicators.get('score_context', 0)
                })
            
            success = self.db.save_alert(alert_data)
            
            if success:
                logger.info(f"✅ {tier} ALERT TRACKED: {alert_data['teams']}")
                logger.info(f"   📊 Score: {score} | Corners: {alert_data['corners_at_alert']}")
                if momentum_indicators:
                    logger.info(f"   🔄 Attack Intensity: {momentum_indicators.get('attack_intensity', 0):.1f}")
                    logger.info(f"   🎯 Shot Efficiency: {momentum_indicators.get('shot_efficiency', 0):.1f}")
                    logger.info(f"   ⚡ Corner Momentum: {momentum_indicators.get('corner_momentum', 0):.1f}")
                if detected_patterns:
                    logger.info(f"   🎯 Patterns: {', '.join(p['name'] for p in detected_patterns)}")
            else:
                logger.error(f"❌ Failed to save {tier} alert: {alert_data['teams']}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error tracking {tier} alert: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def _extract_over_bet(self, active_odds: list) -> tuple:
        """Extract the Over line and odds from active odds list"""
        
        # Look for Over bets in active odds
        # Format: ["Over 10.5 = 2.25", "Under 10.5 = 1.62"]
        
        for odds_str in active_odds:
            if "Over" in odds_str:
                try:
                    # Parse "Over 10.5 = 2.25" 
                    match = re.match(r"Over (\d+\.?\d*) = ([\d.]+)", odds_str)
                    if match:
                        line = match.group(1)  # "10.5"
                        odds = match.group(2)  # "2.25"
                        logger.info(f"📊 EXTRACTED BET: Over {line} @ {odds}")
                        return line, odds
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing odds string '{odds_str}': {e}")
        
        # Fallback if no Over odds found
        logger.warning(f"⚠️ No Over odds found in: {active_odds}")
        return "10.5", "2.00"  # Default assumption
    
    def get_recent_alerts(self, limit: int = 10) -> list:
        """Get recent alerts for quick review"""
        return self.db.get_all_alerts(limit)

    def reset_all_alerts(self) -> bool:
        """Dangerous: wipe the alerts table to start fresh."""
        try:
            return self.db.truncate_alerts()
        except Exception as e:
            logger.error(f"❌ Failed to reset alerts: {e}")
            return False
    
    def get_performance_summary(self) -> Dict:
        """Get current performance statistics"""
        stats = self.db.get_performance_stats()
        
        if stats:
            logger.info(f"📈 PERFORMANCE SUMMARY:")
            logger.info(f"   Total Alerts: {stats['total_alerts']}")
            logger.info(f"   Wins: {stats['wins']}")
            logger.info(f"   Losses: {stats['losses']}")
            logger.info(f"   Refunds: {stats['refunds']}")
            logger.info(f"   Pending: {stats['pending']}")
            logger.info(f"   Win Rate: {stats['win_rate']}%")
        
        return stats

# Global tracker instance
alert_tracker = AlertTracker()

def track_elite_alert(match_data: Dict, tier: str, score: float, conditions: list,
                     momentum_indicators: Dict = None, detected_patterns: List[Dict] = None) -> bool:
    """Global function to track elite alerts"""
    return alert_tracker.save_elite_alert(match_data, tier, score, conditions,
                                        momentum_indicators, detected_patterns)