#!/usr/bin/env python3
"""
HALFTIME GIANT KILLER CORNER SYSTEM
===================================
Psychology-driven corner alerts targeting massive underdogs in "halftime giant-killing" mode.

When a heavy underdog (4.00+ odds) is defying expectations by staying close or ahead at 30th minute,
they enter "HALFTIME GIANT-KILLING" mode and attack relentlessly to maintain their shocking position into the break.
This creates predictable corner explosion patterns in the final 15 minutes of the first half.

SAME HIGH STANDARDS as late corner system - we maintain strict momentum requirements!
"""

import logging
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FirstHalfUnderdogPsychology:
    """First half underdog psychological pressure profile for a match"""
    match_type: str  # MASSIVE_UNDERDOG, HEAVY_UNDERDOG, MODERATE_UNDERDOG, BALANCED
    underdog_team: str  # 'home', 'away', or None
    underdog_odds: float
    favorite_odds: float
    giant_killing_multiplier: float
    desperation_level: str  # MAXIMUM, HIGH, MODERATE, LOW

class HalftimeGiantKillerSystem:
    """
    Revolutionary first half corner system exploiting underdog halftime psychology.
    
    Core Insight: Massive underdogs (4.00+ odds) defying expectations at 30th minute create
    predictable corner patterns due to "halftime giant-killing" mentality and desperation to maintain lead.
    
    SAME HIGH STANDARDS: We maintain strict momentum thresholds - pressure is pressure!
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Underdog psychology thresholds (identical to late system)
        self.MASSIVE_UNDERDOG_THRESHOLD = 6.00    # 6.00+ odds = massive underdog
        self.HEAVY_UNDERDOG_THRESHOLD = 4.00      # 4.00+ odds = heavy underdog
        self.MODERATE_UNDERDOG_THRESHOLD = 2.50   # 2.50+ odds = moderate underdog
        
        # SAME HIGH STANDARDS as late corner system - no lowered thresholds!
        # Fighting spirit is fighting spirit whether it's 30th minute or 85th minute!
        self.MIN_MOMENTUM = 100  # SAME: True fighting spirit momentum required
        self.MIN_CORNERS = 2     # Slightly lower (first half has fewer corners naturally)
        self.MIN_SHOTS_TOTAL = 13  # SAME: High desperation volume required
        self.MIN_SHOTS_TARGET = 5   # SAME: Quality attempts showing real threat
        self.MIN_MINUTE = 30     # First half timing: 30-35 minute window
        self.MAX_MINUTE = 35     # Strict halftime urgency window
        
    def get_1x2_odds_from_fixture(self, fixture_data: Dict) -> Optional[Dict]:
        """Extract 1X2 odds from fixture data (reuse from halftime panic favorite)"""
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
    
    def analyze_first_half_underdog_psychology(self, home_odds: float, away_odds: float) -> FirstHalfUnderdogPsychology:
        """Analyze the underdog psychological setup for first half scenarios"""
        
        # Determine underdog and calculate giant-killing potential
        if home_odds >= self.HEAVY_UNDERDOG_THRESHOLD:
            underdog_team = 'home'
            underdog_odds = home_odds
            favorite_odds = away_odds
        elif away_odds >= self.HEAVY_UNDERDOG_THRESHOLD:
            underdog_team = 'away'
            underdog_odds = away_odds
            favorite_odds = home_odds
        else:
            # No massive underdog - not our target
            return FirstHalfUnderdogPsychology(
                match_type="BALANCED",
                underdog_team=None,
                underdog_odds=max(home_odds, away_odds),
                favorite_odds=min(home_odds, away_odds),
                giant_killing_multiplier=1.0,
                desperation_level="LOW"
            )
        
        # Categorize underdog strength and calculate giant-killing multiplier
        if underdog_odds >= self.MASSIVE_UNDERDOG_THRESHOLD:
            match_type = f"MASSIVE_HALFTIME_UNDERDOG_{underdog_team.upper()}"
            giant_killing_multiplier = 2.5  # Maximum halftime giant-killing potential
            desperation_level = "MAXIMUM"
        elif underdog_odds >= self.HEAVY_UNDERDOG_THRESHOLD:
            match_type = f"HEAVY_HALFTIME_UNDERDOG_{underdog_team.upper()}"
            giant_killing_multiplier = 2.0  # High halftime giant-killing potential
            desperation_level = "HIGH"
        else:
            match_type = f"MODERATE_HALFTIME_UNDERDOG_{underdog_team.upper()}"
            giant_killing_multiplier = 1.5  # Moderate halftime giant-killing potential
            desperation_level = "MODERATE"
        
        return FirstHalfUnderdogPsychology(
            match_type=match_type,
            underdog_team=underdog_team,
            underdog_odds=underdog_odds,
            favorite_odds=favorite_odds,
            giant_killing_multiplier=giant_killing_multiplier,
            desperation_level=desperation_level
        )
    
    def check_halftime_giant_killing_conditions(self, psychology: FirstHalfUnderdogPsychology, match_data: Dict) -> Optional[Dict]:
        """Check if the massive underdog is in halftime giant-killing mode"""
        
        home_score = match_data.get('home_score', 0)
        away_score = match_data.get('away_score', 0)
        minute = match_data.get('minute', 0)
        
        giant_killing_scenarios = []
        
        if psychology.underdog_team == 'home':
            goal_difference = home_score - away_score  # Positive = underdog leading
        elif psychology.underdog_team == 'away':
            goal_difference = away_score - home_score  # Positive = underdog leading
        else:
            return None
        
        # Halftime giant-killing conditions - same standards as late game!
        if goal_difference > 0 and minute >= 30:  # Underdog actually leading - MAXIMUM giant-killing
            giant_killing_scenarios.append({
                'giant_killing_level': 'MAXIMUM_HALFTIME_GIANT_KILLING',
                'description': f"Massive underdog ({psychology.underdog_odds:.2f}) actually LEADING at {minute}' - halftime giant-killing mode!",
                'desperation_multiplier': 2.5
            })
        elif goal_difference == 0 and minute >= 30:  # Drawing - still giant-killing territory
            giant_killing_scenarios.append({
                'giant_killing_level': 'HALFTIME_GIANT_KILLING',
                'description': f"Massive underdog ({psychology.underdog_odds:.2f}) holding draw at {minute}' - halftime upset building!",
                'desperation_multiplier': 2.0
            })
        
        # Return the highest giant-killing scenario if any
        if giant_killing_scenarios:
            # Sort by desperation multiplier (highest first)
            giant_killing_scenarios.sort(key=lambda x: x['desperation_multiplier'], reverse=True)
            return giant_killing_scenarios[0]
        
        return None
    
    def validate_first_half_underdog_stats(self, match_data: Dict, momentum_data: Dict, psychology: FirstHalfUnderdogPsychology) -> bool:
        """Validate that live stats support the halftime giant-killing theory - SAME HIGH STANDARDS!"""
        
        minute = match_data.get('minute', 0)
        total_corners = match_data.get('total_corners', 0)
        total_shots = match_data.get('total_shots', 0)
        shots_on_target = match_data.get('total_shots_on_target', 0)
        
        # Get underdog's momentum
        if psychology.underdog_team == 'home':
            underdog_momentum = momentum_data.get('home_momentum', 0)
        elif psychology.underdog_team == 'away':
            underdog_momentum = momentum_data.get('away_momentum', 0)
        else:
            return False
        
        # Combined momentum for overall match intensity
        combined_momentum = momentum_data.get('home_momentum', 0) + momentum_data.get('away_momentum', 0)
        
        # Apply psychology multiplier to momentum threshold
        adjusted_momentum_threshold = self.MIN_MOMENTUM / psychology.giant_killing_multiplier
        
        # SAME HIGH STANDARDS - no watered down validation!
        validations = {
            'minute_ok': self.MIN_MINUTE <= minute <= self.MAX_MINUTE,
            'corners_ok': total_corners >= self.MIN_CORNERS,
            'shots_ok': total_shots >= self.MIN_SHOTS_TOTAL,
            'shots_target_ok': shots_on_target >= self.MIN_SHOTS_TARGET,
            'momentum_ok': underdog_momentum >= adjusted_momentum_threshold,
            'intensity_ok': combined_momentum >= 120  # SAME: High intensity required for underdogs
        }
        
        # Log validation details
        self.logger.info(f"   🥊 Halftime underdog validation for {psychology.match_type}:")
        self.logger.info(f"      Minute: {minute} in [{self.MIN_MINUTE}-{self.MAX_MINUTE}] = {validations['minute_ok']}")
        self.logger.info(f"      Corners: {total_corners} >= {self.MIN_CORNERS} = {validations['corners_ok']}")
        self.logger.info(f"      Shots: {total_shots} >= {self.MIN_SHOTS_TOTAL} = {validations['shots_ok']}")
        self.logger.info(f"      Shots on Target: {shots_on_target} >= {self.MIN_SHOTS_TARGET} = {validations['shots_target_ok']}")
        self.logger.info(f"      Underdog Momentum: {underdog_momentum:.1f} >= {adjusted_momentum_threshold:.1f} = {validations['momentum_ok']}")
        self.logger.info(f"      Combined Intensity: {combined_momentum:.1f} >= 120 = {validations['intensity_ok']}")
        
        # All criteria must pass - SAME HIGH STANDARDS!
        return all(validations.values())
    
    def evaluate_halftime_giant_killer_alert(self, fixture_data: Dict, match_data: Dict, momentum_data: Dict) -> Optional[Dict]:
        """
        Main evaluation function for halftime giant killer corner alerts.
        
        Returns alert data if conditions are met, None otherwise.
        MAINTAINS SAME HIGH STANDARDS as late corner system!
        """
        
        # Step 1: Extract 1X2 odds
        odds_data = self.get_1x2_odds_from_fixture(fixture_data)
        if not odds_data:
            self.logger.info("   🔍 No 1X2 odds available - cannot assess halftime underdog psychology")
            return None
        
        home_odds = odds_data['home_odds']
        away_odds = odds_data['away_odds']
        
        # Step 2: Analyze halftime underdog psychology setup
        psychology = self.analyze_first_half_underdog_psychology(home_odds, away_odds)
        
        self.logger.info(f"   🥊 Halftime Underdog Psychology Profile: {psychology.match_type}")
        self.logger.info(f"      Underdog: {psychology.underdog_team} ({psychology.underdog_odds:.2f})")
        self.logger.info(f"      Giant-Killing Multiplier: {psychology.giant_killing_multiplier:.1f}x")
        self.logger.info(f"      Desperation Level: {psychology.desperation_level}")
        
        # Step 3: Check if we have a massive underdog (our target)
        if psychology.match_type not in ["MASSIVE_HALFTIME_UNDERDOG_HOME", "MASSIVE_HALFTIME_UNDERDOG_AWAY", 
                                       "HEAVY_HALFTIME_UNDERDOG_HOME", "HEAVY_HALFTIME_UNDERDOG_AWAY"]:
            self.logger.info(f"   ⏭️ Not a massive halftime underdog scenario - skipping psychology system")
            return None
        
        # Step 4: Check halftime giant-killing conditions
        giant_killing_data = self.check_halftime_giant_killing_conditions(psychology, match_data)
        if not giant_killing_data:
            self.logger.info(f"   😞 No halftime giant-killing conditions detected - underdog not defying expectations")
            return None
        
        self.logger.info(f"   🚨 HALFTIME GIANT-KILLING DETECTED: {giant_killing_data['giant_killing_level']}")
        self.logger.info(f"      {giant_killing_data['description']}")
        
        # Step 5: Validate with live stats - SAME HIGH STANDARDS!
        if not self.validate_first_half_underdog_stats(match_data, momentum_data, psychology):
            self.logger.info(f"   📊 Live stats don't support halftime giant-killing theory - skipping alert")
            return None
        
        # Step 6: Build alert data
        combined_momentum = momentum_data.get('home_momentum', 0) + momentum_data.get('away_momentum', 0)
        
        alert_data = {
            'alert_type': 'HALFTIME_FIGHTING_UNDERDOG',
            'tier': 'HALFTIME_FIGHTING_UNDERDOG',
            'psychology_type': psychology.match_type,
            'underdog_team': psychology.underdog_team,
            'underdog_odds': psychology.underdog_odds,
            'giant_killing_level': giant_killing_data['giant_killing_level'],
            'giant_killing_description': giant_killing_data['description'],
            'combined_momentum': combined_momentum,
            'giant_killing_multiplier': psychology.giant_killing_multiplier,
            'desperation_level': psychology.desperation_level,
            'reasoning': f"Massive underdog ({psychology.underdog_odds:.2f}) in halftime giant-killing mode with {combined_momentum:.0f} momentum points"
        }
        
        self.logger.info(f"   ✅ HALFTIME GIANT KILLER ALERT TRIGGERED!")
        self.logger.info(f"      Alert Type: {alert_data['alert_type']}")
        self.logger.info(f"      Combined Momentum: {combined_momentum:.0f}")
        self.logger.info(f"      Reasoning: {alert_data['reasoning']}")
        
        return alert_data