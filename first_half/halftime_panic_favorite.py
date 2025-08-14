#!/usr/bin/env python3
"""
HALFTIME PANIC FAVORITE CORNER SYSTEM
====================================
Psychology-driven corner alerts targeting heavy favorites under pressure approaching HALFTIME.

When a heavy favorite (1.20-1.40 odds) is drawing/losing at the 30th minute,
they enter HALFTIME PANIC MODE and abandon tactical discipline to force a result before the break.
This creates predictable corner explosion patterns in the final 15 minutes of the first half.

SAME HIGH STANDARDS as late corner system - we maintain strict momentum requirements!
"""

import logging
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FirstHalfPsychologyProfile:
    """First half psychological pressure profile for a match"""
    match_type: str  # HEAVY_FAVORITE, CLEAR_FAVORITE, BALANCED
    favorite_team: str  # 'home', 'away', or None
    favorite_odds: float
    underdog_odds: float
    pressure_multiplier: float
    confidence_level: str  # MAXIMUM, HIGH, MODERATE, LOW

class HalftimePanicFavoriteSystem:
    """
    Revolutionary first half corner system exploiting heavy favorite halftime psychology.
    
    Core Insight: Heavy favorites (1.20-1.40 odds) under pressure at 30th minute create
    predictable corner patterns due to halftime panic and desperation to lead at the break.
    
    SAME HIGH STANDARDS: We maintain strict momentum thresholds - pressure is pressure!
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Psychology thresholds (identical to late system)
        self.HEAVY_FAVORITE_THRESHOLD = 1.40
        self.MASSIVE_FAVORITE_THRESHOLD = 1.25
        self.CLEAR_FAVORITE_THRESHOLD = 1.80
        
        # SAME HIGH STANDARDS as late corner system - no lowered thresholds!
        # Momentum is momentum whether it's 30th minute or 85th minute!
        self.MIN_MOMENTUM = 120  # SAME: Explosive momentum only
        self.MIN_CORNERS = 3     # Slightly lower (first half has fewer corners naturally)
        self.MIN_SHOTS_TOTAL = 15  # SAME: High attacking volume required
        self.MIN_SHOTS_TARGET = 6   # SAME: Quality attempts showing desperation
        self.MIN_MINUTE = 30     # First half timing: 30-35 minute window  
        self.MAX_MINUTE = 35     # Strict halftime urgency window
        
    def get_1x2_odds_from_fixture(self, fixture_data: Dict) -> Optional[Dict]:
        """Extract 1X2 odds from fixture data (prematch or live)"""
        try:
            # Look for odds in fixture data
            odds_data = fixture_data.get('odds', [])
            
            for bookmaker in odds_data:
                if bookmaker.get('bookmaker_id') == 2:  # bet365
                    markets = bookmaker.get('markets', [])
                    
                    for market in markets:
                        # Look for 1X2 / Match Winner / Full Time Result
                        market_name = market.get('name', '').lower()
                        market_id = market.get('market_id')
                        
                        if (market_id == 1 or  # Standard 1X2 market ID
                            any(keyword in market_name for keyword in [
                                '1x2', 'match winner', 'full time result', 
                                'fulltime result', 'match result'
                            ])):
                            
                            selections = market.get('selections', [])
                            home_odds = away_odds = draw_odds = None
                            
                            for selection in selections:
                                label = selection.get('label', '').lower()
                                odds = selection.get('odds') or selection.get('value')
                                
                                if odds:
                                    odds = float(odds)
                                    
                                    if label in ['1', 'home', 'home win']:
                                        home_odds = odds
                                    elif label in ['2', 'away', 'away win']:
                                        away_odds = odds
                                    elif label in ['x', 'draw', 'tie']:
                                        draw_odds = odds
                            
                            if home_odds and away_odds:
                                return {
                                    'home_odds': home_odds,
                                    'away_odds': away_odds,
                                    'draw_odds': draw_odds
                                }
            
            self.logger.warning("No 1X2 odds found in fixture data")
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting 1X2 odds: {e}")
            return None
    
    def analyze_first_half_psychology_profile(self, home_odds: float, away_odds: float) -> FirstHalfPsychologyProfile:
        """Analyze the psychological pressure setup for first half scenarios"""
        
        # Determine favorite and calculate pressure
        if home_odds <= self.HEAVY_FAVORITE_THRESHOLD:
            favorite_team = 'home'
            favorite_odds = home_odds
            underdog_odds = away_odds
        elif away_odds <= self.HEAVY_FAVORITE_THRESHOLD:
            favorite_team = 'away'
            favorite_odds = away_odds
            underdog_odds = home_odds
        else:
            # No heavy favorite - not our target
            return FirstHalfPsychologyProfile(
                match_type="BALANCED",
                favorite_team=None,
                favorite_odds=min(home_odds, away_odds),
                underdog_odds=max(home_odds, away_odds),
                pressure_multiplier=1.0,
                confidence_level="LOW"
            )
        
        # Categorize favorite strength and calculate pressure multiplier
        if favorite_odds <= self.MASSIVE_FAVORITE_THRESHOLD:
            match_type = f"MASSIVE_HALFTIME_FAVORITE_{favorite_team.upper()}"
            pressure_multiplier = 2.5  # Massive pressure at halftime
            confidence_level = "MAXIMUM"
        elif favorite_odds <= self.HEAVY_FAVORITE_THRESHOLD:
            match_type = f"HEAVY_HALFTIME_FAVORITE_{favorite_team.upper()}"
            pressure_multiplier = 2.0  # High halftime pressure
            confidence_level = "HIGH"
        else:
            match_type = f"CLEAR_HALFTIME_FAVORITE_{favorite_team.upper()}"
            pressure_multiplier = 1.5  # Moderate halftime pressure
            confidence_level = "MODERATE"
        
        return FirstHalfPsychologyProfile(
            match_type=match_type,
            favorite_team=favorite_team,
            favorite_odds=favorite_odds,
            underdog_odds=underdog_odds,
            pressure_multiplier=pressure_multiplier,
            confidence_level=confidence_level
        )
    
    def check_halftime_panic_conditions(self, psychology: FirstHalfPsychologyProfile, match_data: Dict) -> Optional[Dict]:
        """Check if the heavy favorite is in halftime panic mode"""
        
        home_score = match_data.get('home_score', 0)
        away_score = match_data.get('away_score', 0)
        minute = match_data.get('minute', 0)
        
        panic_scenarios = []
        
        if psychology.favorite_team == 'home':
            goal_difference = home_score - away_score
        elif psychology.favorite_team == 'away':
            goal_difference = away_score - home_score
        else:
            return None
        
        # Halftime panic conditions - same standards as late game!
        if goal_difference == 0 and minute >= 30:  # Drawing at halftime approach
            panic_scenarios.append({
                'panic_level': 'HALFTIME_PANIC',
                'description': f"Heavy favorite ({psychology.favorite_odds:.2f}) still drawing at {minute}' - halftime pressure building!",
                'urgency_multiplier': 2.0
            })
        elif goal_difference < 0 and minute >= 25:  # Actually losing - MAXIMUM panic
            panic_scenarios.append({
                'panic_level': 'MAXIMUM_HALFTIME_PANIC',
                'description': f"Heavy favorite ({psychology.favorite_odds:.2f}) actually losing at {minute}' - halftime desperation mode!",
                'urgency_multiplier': 2.5
            })
        
        # Return the highest panic scenario if any
        if panic_scenarios:
            # Sort by urgency multiplier (highest first)
            panic_scenarios.sort(key=lambda x: x['urgency_multiplier'], reverse=True)
            return panic_scenarios[0]
        
        return None
    
    def validate_first_half_stats(self, match_data: Dict, momentum_data: Dict, psychology: FirstHalfPsychologyProfile) -> bool:
        """Validate that live stats support the halftime panic theory - SAME HIGH STANDARDS!"""
        
        minute = match_data.get('minute', 0)
        total_corners = match_data.get('total_corners', 0)
        total_shots = match_data.get('total_shots', 0)
        shots_on_target = match_data.get('total_shots_on_target', 0)
        
        # Get favorite's momentum
        if psychology.favorite_team == 'home':
            favorite_momentum = momentum_data.get('home_momentum', 0)
        elif psychology.favorite_team == 'away':
            favorite_momentum = momentum_data.get('away_momentum', 0)
        else:
            return False
        
        # Combined momentum for overall match intensity
        combined_momentum = momentum_data.get('home_momentum', 0) + momentum_data.get('away_momentum', 0)
        
        # Apply psychology multiplier to momentum threshold
        adjusted_momentum_threshold = self.MIN_MOMENTUM / psychology.pressure_multiplier
        
        # SAME HIGH STANDARDS - no watered down validation!
        validations = {
            'minute_ok': self.MIN_MINUTE <= minute <= self.MAX_MINUTE,
            'corners_ok': total_corners >= self.MIN_CORNERS,
            'shots_ok': total_shots >= self.MIN_SHOTS_TOTAL,
            'shots_target_ok': shots_on_target >= self.MIN_SHOTS_TARGET,
            'momentum_ok': favorite_momentum >= adjusted_momentum_threshold,
            'intensity_ok': combined_momentum >= 150  # SAME: Very high overall intensity required
        }
        
        # Log validation details
        self.logger.info(f"   🏁 Halftime psychology validation for {psychology.match_type}:")
        self.logger.info(f"      Minute: {minute} in [{self.MIN_MINUTE}-{self.MAX_MINUTE}] = {validations['minute_ok']}")
        self.logger.info(f"      Corners: {total_corners} >= {self.MIN_CORNERS} = {validations['corners_ok']}")
        self.logger.info(f"      Shots: {total_shots} >= {self.MIN_SHOTS_TOTAL} = {validations['shots_ok']}")
        self.logger.info(f"      Shots on Target: {shots_on_target} >= {self.MIN_SHOTS_TARGET} = {validations['shots_target_ok']}")
        self.logger.info(f"      Favorite Momentum: {favorite_momentum:.1f} >= {adjusted_momentum_threshold:.1f} = {validations['momentum_ok']}")
        self.logger.info(f"      Combined Intensity: {combined_momentum:.1f} >= 150 = {validations['intensity_ok']}")
        
        # All criteria must pass - SAME HIGH STANDARDS!
        return all(validations.values())
    
    def evaluate_halftime_panic_alert(self, fixture_data: Dict, match_data: Dict, momentum_data: Dict) -> Optional[Dict]:
        """
        Main evaluation function for halftime panic favorite corner alerts.
        
        Returns alert data if conditions are met, None otherwise.
        MAINTAINS SAME HIGH STANDARDS as late corner system!
        """
        
        # Step 1: Extract 1X2 odds
        odds_data = self.get_1x2_odds_from_fixture(fixture_data)
        if not odds_data:
            self.logger.info("   🔍 No 1X2 odds available - cannot assess halftime psychology")
            return None
        
        home_odds = odds_data['home_odds']
        away_odds = odds_data['away_odds']
        
        # Step 2: Analyze halftime psychological pressure setup
        psychology = self.analyze_first_half_psychology_profile(home_odds, away_odds)
        
        self.logger.info(f"   🏁 Halftime Psychology Profile: {psychology.match_type}")
        self.logger.info(f"      Favorite: {psychology.favorite_team} ({psychology.favorite_odds:.2f})")
        self.logger.info(f"      Pressure Multiplier: {psychology.pressure_multiplier:.1f}x")
        self.logger.info(f"      Confidence: {psychology.confidence_level}")
        
        # Step 3: Check if we have a heavy favorite (our target)
        if psychology.match_type not in ["MASSIVE_HALFTIME_FAVORITE_HOME", "MASSIVE_HALFTIME_FAVORITE_AWAY", 
                                       "HEAVY_HALFTIME_FAVORITE_HOME", "HEAVY_HALFTIME_FAVORITE_AWAY"]:
            self.logger.info(f"   ⏭️ Not a heavy halftime favorite scenario - skipping psychology system")
            return None
        
        # Step 4: Check halftime panic conditions
        panic_data = self.check_halftime_panic_conditions(psychology, match_data)
        if not panic_data:
            self.logger.info(f"   😌 No halftime panic conditions detected - favorite meeting expectations")
            return None
        
        self.logger.info(f"   🚨 HALFTIME PANIC DETECTED: {panic_data['panic_level']}")
        self.logger.info(f"      {panic_data['description']}")
        
        # Step 5: Validate with live stats - SAME HIGH STANDARDS!
        if not self.validate_first_half_stats(match_data, momentum_data, psychology):
            self.logger.info(f"   📊 Live stats don't support halftime panic theory - skipping alert")
            return None
        
        # Step 6: Build alert data
        combined_momentum = momentum_data.get('home_momentum', 0) + momentum_data.get('away_momentum', 0)
        
        alert_data = {
            'alert_type': 'HALFTIME_PANICKING_FAVORITE',
            'tier': 'HALFTIME_PANICKING_FAVORITE',
            'psychology_type': psychology.match_type,
            'favorite_team': psychology.favorite_team,
            'favorite_odds': psychology.favorite_odds,
            'panic_level': panic_data['panic_level'],
            'panic_description': panic_data['description'],
            'combined_momentum': combined_momentum,
            'pressure_multiplier': psychology.pressure_multiplier,
            'confidence_level': psychology.confidence_level,
            'reasoning': f"Heavy favorite ({psychology.favorite_odds:.2f}) in halftime panic mode with {combined_momentum:.0f} momentum points"
        }
        
        self.logger.info(f"   ✅ HALFTIME PANIC FAVORITE ALERT TRIGGERED!")
        self.logger.info(f"      Alert Type: {alert_data['alert_type']}")
        self.logger.info(f"      Combined Momentum: {combined_momentum:.0f}")
        self.logger.info(f"      Reasoning: {alert_data['reasoning']}")
        
        return alert_data