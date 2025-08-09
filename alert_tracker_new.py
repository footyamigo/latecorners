#!/usr/bin/env python3
"""Track and save alerts from the new Late Momentum and Draw Odds systems."""

import logging
import re
from typing import Dict, List
from latecorners.database_postgres import get_database

logger = logging.getLogger(__name__)

class AlertTracker:
    """Track and save alerts from the new systems (Late Momentum and Draw Odds)."""
    
    def __init__(self):
        self.db = get_database()
    
    def save_elite_alert(self, match_data: Dict, tier: str, score: float, conditions: list,
                        momentum_indicators: Dict = None, detected_patterns: List[Dict] = None) -> bool:
        """Save a new-system alert to the database for tracking.

        Only stores essential data for Late Momentum and Late Corner Draw alerts.
        """
        
        try:
            logger.info(f"💾 SAVING {tier} ALERT: {match_data.get('home_team')} vs {match_data.get('away_team')}")
            
            # Extract only Over odds from active_odds for asian_odds_snapshot
            over_odds_text = self._extract_over_odds_only(match_data.get('active_odds', []))
            
            # Base alert data - only essential columns
            alert_data = {
                'fixture_id': match_data.get('fixture_id'),
                'teams': f"{match_data.get('home_team')} vs {match_data.get('away_team')}",
                'score_at_alert': f"{match_data.get('home_score')}-{match_data.get('away_score')}",
                'minute_sent': match_data.get('minute'),
                'corners_at_alert': match_data.get('total_corners', 0),
                'alert_type': tier,
                'draw_odds': match_data.get('draw_odds') or (momentum_indicators or {}).get('draw_odds'),
                'combined_momentum10': (momentum_indicators or {}).get('combined_momentum10', 0),
                'momentum_home_total': (momentum_indicators or {}).get('momentum_home_total', 0),
                'momentum_away_total': (momentum_indicators or {}).get('momentum_away_total', 0),
                'asian_odds_snapshot': over_odds_text,
            }
            
            success = self.db.save_alert(alert_data)
            
            if success:
                logger.info(f"✅ {tier} ALERT TRACKED: {alert_data['teams']}")
                logger.info(f"   📊 Score: {score} | Corners: {alert_data['corners_at_alert']}")
                if momentum_indicators:
                    logger.info(f"   🔄 Combined Momentum: {momentum_indicators.get('combined_momentum10', 0):.1f}")
                    logger.info(f"   🏠 Home Momentum: {momentum_indicators.get('momentum_home_total', 0):.1f}")
                    logger.info(f"   🏃 Away Momentum: {momentum_indicators.get('momentum_away_total', 0):.1f}")
                if match_data.get('draw_odds'):
                    logger.info(f"   📈 Draw Odds: {match_data.get('draw_odds')}")
            else:
                logger.error(f"❌ Failed to save {tier} alert: {alert_data['teams']}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error saving elite alert: {e}")
            return False
    
    def _extract_over_odds_only(self, active_odds: List[str]) -> str:
        """Extract only the Over odds from active_odds list.
        
        Args:
            active_odds: List of odds strings like ["Over 11 = 2.1", "Under 11 = 1.8"]
            
        Returns:
            String with only Over odds, e.g., "Over 11 = 2.1"
        """
        for odds_str in active_odds:
            if "Over" in odds_str:
                try:
                    # Return the Over odds string as-is
                    logger.info(f"📊 EXTRACTED OVER ODDS: {odds_str}")
                    return odds_str
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing odds string '{odds_str}': {e}")
        
        # Fallback if no Over odds found
        logger.warning(f"⚠️ No Over odds found in: {active_odds}")
        return "Over 10.5 = 2.00"  # Default assumption
    
    def get_recent_alerts(self, limit: int = 10) -> list:
        """Get recent alerts for quick review"""
        return self.db.get_all_alerts(limit)

    def reset_all_alerts(self) -> bool:
        """Dangerous: wipe the alerts table to start fresh."""
        try:
            return self.db.truncate_alerts()
        except Exception as e:
            logger.error(f"Failed to reset alerts: {e}")
            return False

# Global instance for easy importing
alert_tracker = AlertTracker()

def track_elite_alert(match_data: Dict, tier: str, score: float, conditions: list,
                     momentum_indicators: Dict = None, detected_patterns: List[Dict] = None) -> bool:
    """Global function to track elite alerts"""
    return alert_tracker.save_elite_alert(match_data, tier, score, conditions,
                                        momentum_indicators, detected_patterns)