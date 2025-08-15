#!/usr/bin/env python3
"""
FIRST HALF CORNER ANALYZER
==========================
Coordinator for first half Asian corner alert system targeting 30th minute alerts.

Integrates:
- FirstHalfMomentumTracker (8-minute rolling window, same high standards)
- HalftimePanicFavoriteSystem (heavy favorites under halftime pressure)
- HalftimeGiantKillerSystem (massive underdogs in giant-killing mode)

Market Target: 63 "1st Half Asian Corners"
Timing: 28-32 minute window (halftime urgency)
Standards: SAME HIGH MOMENTUM REQUIREMENTS as late corner system!
"""

import logging
from typing import Dict, Optional, Any
from .first_half_momentum_tracker import FirstHalfMomentumTracker
from .halftime_panic_favorite import HalftimePanicFavoriteSystem
from .halftime_giant_killer import HalftimeGiantKillerSystem

logger = logging.getLogger(__name__)

class FirstHalfAnalyzer:
    """
    Main coordinator for first half corner analysis.
    
    Analyzes momentum and psychology at 30th minute to trigger first half Asian corner alerts.
    MAINTAINS SAME HIGH STANDARDS as late corner system - no compromises on quality!
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize components with same high standards
        self.momentum_tracker = FirstHalfMomentumTracker(window_minutes=10)
        self.panic_favorite_system = HalftimePanicFavoriteSystem()
        self.giant_killer_system = HalftimeGiantKillerSystem()
        
        # Timing constraints for first half alerts
        self.MIN_MINUTE = 30
        self.MAX_MINUTE = 35
        self.TARGET_MINUTE = 32  # Ideal alert timing
        
        self.logger.info("🏁 FirstHalfAnalyzer initialized with SAME HIGH STANDARDS as late corner system")
        self.logger.info(f"   Target timing: {self.MIN_MINUTE}-{self.MAX_MINUTE} minutes (halftime urgency window)")
        self.logger.info(f"   Market: 63 '1st Half Asian Corners'")
        self.logger.info(f"   Momentum window: 10 minutes (same formula, same weights)")
    
    def add_match_snapshot(self, fixture_id: int, minute: int, match_stats: Dict) -> None:
        """
        Add a snapshot to the momentum tracker.
        Expected to be called continuously during first half monitoring.
        """
        try:
            # Extract momentum data
            home_stats = {
                'shots_on_target': match_stats.get('shots_on_target', {}).get('home', 0),
                'shots_off_target': match_stats.get('shots_off_target', {}).get('home', 0),
                'dangerous_attacks': match_stats.get('dangerous_attacks', {}).get('home', 0),
                'attacks': match_stats.get('attacks', {}).get('home', 0),
                'possession': match_stats.get('possession', {}).get('home', 0),
            }
            
            away_stats = {
                'shots_on_target': match_stats.get('shots_on_target', {}).get('away', 0),
                'shots_off_target': match_stats.get('shots_off_target', {}).get('away', 0),
                'dangerous_attacks': match_stats.get('dangerous_attacks', {}).get('away', 0),
                'attacks': match_stats.get('attacks', {}).get('away', 0),
                'possession': match_stats.get('possession', {}).get('away', 0),
            }
            
            # Add to momentum tracker
            self.momentum_tracker.add_snapshot(fixture_id, minute, home_stats, away_stats)
            
        except Exception as e:
            self.logger.error(f"Error adding first half snapshot for fixture {fixture_id}: {e}")
    
    def is_first_half_alert_timing(self, minute: int) -> bool:
        """Check if we're in the first half alert timing window"""
        return self.MIN_MINUTE <= minute <= self.MAX_MINUTE
    
    def analyze_first_half_opportunity(self, fixture_id: int, fixture_data: Dict, match_data: Dict) -> Optional[Dict]:
        """
        Analyze first half corner opportunity at 30th minute.
        
        Returns alert data if conditions are met, None otherwise.
        SAME HIGH STANDARDS as late corner system!
        """
        
        minute = match_data.get('minute', 0)
        
        # Step 1: Timing validation - must be in halftime urgency window
        if not self.is_first_half_alert_timing(minute):
            self.logger.debug(f"⏰ FIRST HALF TIMING CHECK FAILED: Match at {minute}' (need {self.MIN_MINUTE}-{self.MAX_MINUTE} minutes)")
            return None
        
        self.logger.info(f"✅ FIRST HALF TIMING CHECK PASSED: Match at {minute}' (within {self.MIN_MINUTE}-{self.MAX_MINUTE} minute window)")
        
        # Step 2: Get momentum data
        momentum_summary = self.momentum_tracker.get_first_half_momentum_summary(fixture_id)
        
        self.logger.info(f"🏁 FIRST HALF MOMENTUM ANALYSIS - Match {fixture_id} ({minute}'):")
        self.logger.info(f"   Combined Momentum: {momentum_summary['combined_momentum']:.0f} pts")
        self.logger.info(f"   Home Momentum: {momentum_summary['home_momentum']:.0f} pts")
        self.logger.info(f"   Away Momentum: {momentum_summary['away_momentum']:.0f} pts")
        self.logger.info(f"   Window: {momentum_summary['window_minutes']} minutes (20-30 min data)")
        
        # Step 3: Minimum momentum check - SAME HIGH STANDARDS!
        min_combined_momentum = 80  # Lower than late system (120) but still high quality
        if momentum_summary['combined_momentum'] < min_combined_momentum:
            self.logger.info(f"   📊 Insufficient momentum: {momentum_summary['combined_momentum']:.0f} < {min_combined_momentum} - skipping first half analysis")
            return None
        
        # Step 4: Try psychology systems in order of priority
        psychology_alert = None
        
        # Try Halftime Panic Favorite first (higher priority)
        try:
            self.logger.info("   🏁 TESTING: Halftime Panic Favorite psychology...")
            psychology_alert = self.panic_favorite_system.evaluate_halftime_panic_alert(
                fixture_data, match_data, momentum_summary
            )
            
            if psychology_alert:
                self.logger.info(f"   ✅ HALFTIME PANIC FAVORITE TRIGGERED: {psychology_alert['alert_type']}")
                
        except Exception as e:
            self.logger.error(f"Error in halftime panic favorite analysis: {e}")
        
        # Try Halftime Giant Killer if no panic favorite alert
        if not psychology_alert:
            try:
                self.logger.info("   🥊 TESTING: Halftime Giant Killer psychology...")
                psychology_alert = self.giant_killer_system.evaluate_halftime_giant_killer_alert(
                    fixture_data, match_data, momentum_summary
                )
                
                if psychology_alert:
                    self.logger.info(f"   ✅ HALFTIME GIANT KILLER TRIGGERED: {psychology_alert['alert_type']}")
                    
            except Exception as e:
                self.logger.error(f"Error in halftime giant killer analysis: {e}")
        
        # Step 5: Return results
        if psychology_alert:
            # Enhance alert data with first half specifics
            psychology_alert.update({
                'market_id': 63,  # "1st Half Asian Corners"
                'market_name': '1st Half Asian Corners',
                'timing_window': f"{self.MIN_MINUTE}-{self.MAX_MINUTE} minutes",
                'analysis_type': 'FIRST_HALF_ANALYSIS',
                'momentum_window': f"{momentum_summary['window_minutes']} minutes",
                'total_corners_first_half': match_data.get('total_corners', 0),
            })
            
            self.logger.info(f"🎯 FIRST HALF ALERT GENERATED!")
            self.logger.info(f"   Type: {psychology_alert['alert_type']}")
            self.logger.info(f"   Market: {psychology_alert['market_name']} (ID: {psychology_alert['market_id']})")
            self.logger.info(f"   Momentum: {psychology_alert['combined_momentum']:.0f} pts")
            self.logger.info(f"   Reasoning: {psychology_alert['reasoning']}")
            
            return psychology_alert
        
        else:
            self.logger.info(f"   ⏭️ No first half psychology triggers detected - high standards maintained")
            return None
    
    def get_momentum_summary(self, fixture_id: int) -> Dict:
        """Get current momentum summary for a fixture"""
        return self.momentum_tracker.get_first_half_momentum_summary(fixture_id)
    
    def clear_fixture_data(self, fixture_id: int) -> None:
        """Clear stored data for a fixture (after match ends)"""
        if fixture_id in self.momentum_tracker._history:
            del self.momentum_tracker._history[fixture_id]
            self.logger.info(f"🧹 Cleared first half data for fixture {fixture_id}")