#!/usr/bin/env python3
"""
Alert Tracker - Save Elite Alerts to Database
=============================================
Automatically saves elite corner alerts for result tracking.
"""

import logging
from datetime import datetime
from typing import Dict, Optional
import re
from database import get_database

logger = logging.getLogger(__name__)

class AlertTracker:
    """Track and save elite corner alerts"""
    
    def __init__(self):
        self.db = get_database()
    
    def save_elite_alert(self, match_data: Dict, tier: str, score: float, conditions: list) -> bool:
        """Save an elite alert to the database for tracking"""
        
        if tier != "ELITE":
            # Only track ELITE alerts for performance analysis
            logger.debug(f"⏭️ Skipping {tier} alert tracking (ELITE only)")
            return True
        
        try:
            logger.info(f"💾 SAVING ELITE ALERT: {match_data.get('home_team')} vs {match_data.get('away_team')}")
            
            # Extract betting line and odds from active_odds
            over_line, over_odds = self._extract_over_bet(match_data.get('active_odds', []))
            
            # Calculate high priority ratio based on tier
            high_priority_count = match_data.get('high_priority_count', 0)
            if tier == "ELITE":
                priority_required = 2
            elif tier == "PREMIUM":
                priority_required = 1
            else:
                priority_required = 1  # Default fallback
            
            high_priority_ratio = f"{high_priority_count}/{priority_required}"
            
            alert_data = {
                'timestamp': datetime.now().isoformat(),
                'fixture_id': match_data.get('fixture_id'),
                'teams': f"{match_data.get('home_team')} vs {match_data.get('away_team')}",
                'score_at_alert': f"{match_data.get('home_score')}-{match_data.get('away_score')}",
                'minute_sent': match_data.get('minute'),
                'corners_at_alert': match_data.get('total_corners', 0),
                'elite_score': score,
                'high_priority_count': high_priority_count,
                'high_priority_ratio': high_priority_ratio,
                'over_line': over_line,
                'over_odds': over_odds
            }
            
            success = self.db.save_alert(alert_data)
            
            if success:
                logger.info(f"✅ ELITE ALERT TRACKED: {alert_data['teams']} - {alert_data['corners_at_alert']} corners at 85' (High Priority: {high_priority_ratio}) (Over {over_line} @ {over_odds})")
            else:
                logger.error(f"❌ Failed to save elite alert: {alert_data['teams']}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error tracking elite alert: {e}")
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

def track_elite_alert(match_data: Dict, tier: str, score: float, conditions: list) -> bool:
    """Global function to track elite alerts"""
    return alert_tracker.save_elite_alert(match_data, tier, score, conditions) 