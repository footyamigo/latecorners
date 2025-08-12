#!/usr/bin/env python3
"""
FIGHTING UNDERDOG CORNER SYSTEM
===============================
Psychology-driven corner alerts targeting massive underdogs in "giant-killing" mode.

When a heavy underdog (4.00+ odds) is defying expectations by staying close or ahead,
they enter "NOTHING TO LOSE" mode and attack relentlessly for the upset of a lifetime.
This creates predictable corner explosion patterns.
"""

import logging
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class UnderdogPsychology:
    """Underdog psychological pressure profile for a match"""
    match_type: str  # MASSIVE_UNDERDOG, HEAVY_UNDERDOG, MODERATE_UNDERDOG, BALANCED
    underdog_team: str  # 'home', 'away', or None
    underdog_odds: float
    favorite_odds: float
    giant_killing_multiplier: float
    desperation_level: str  # MAXIMUM, HIGH, MODERATE, LOW

class FightingUnderdogSystem:
    """
    Revolutionary corner system exploiting underdog psychology.
    
    Core Insight: Massive underdogs (4.00+ odds) defying expectations create
    predictable corner patterns due to "nothing to lose" mentality and giant-killing aggression.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Underdog psychology thresholds
        self.MASSIVE_UNDERDOG_THRESHOLD = 6.00    # 6.00+ odds = massive underdog
        self.HEAVY_UNDERDOG_THRESHOLD = 4.00      # 4.00+ odds = heavy underdog
        self.MODERATE_UNDERDOG_THRESHOLD = 2.50   # 2.50+ odds = moderate underdog
        
        # STRICTER stats requirements - focus on true underdog explosions
        self.MIN_MOMENTUM = 100  # INCREASED: True fighting spirit momentum (was 60)
        self.MIN_CORNERS = 5     # Lower requirement - chaos creates corners
        self.MIN_SHOTS_TOTAL = 13  # INCREASED: High desperation volume (was 10)
        self.MIN_SHOTS_TARGET = 5   # INCREASED: Quality attempts showing real threat (was 3)
        self.MIN_MINUTE = 70     # Earlier than favorites - desperation builds sooner
        
    def get_1x2_odds_from_fixture(self, fixture_data: Dict) -> Optional[Dict]:
        """Extract 1X2 odds from fixture data (reuse from panicking favorite)"""
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
    
    def analyze_underdog_psychology(self, home_odds: float, away_odds: float) -> UnderdogPsychology:
        """Analyze the underdog psychology setup based on prematch odds"""
        
        # Determine underdog and giant-killing potential
        if away_odds >= self.MASSIVE_UNDERDOG_THRESHOLD:
            # Away is massive underdog
            giant_killing_multiplier = self._get_giant_killing_multiplier(away_odds)
            desperation = self._get_desperation_level(away_odds, home_odds)
            
            return UnderdogPsychology(
                match_type="MASSIVE_UNDERDOG_AWAY",
                underdog_team="away",
                underdog_odds=away_odds,
                favorite_odds=home_odds,
                giant_killing_multiplier=giant_killing_multiplier,
                desperation_level=desperation
            )
            
        elif home_odds >= self.MASSIVE_UNDERDOG_THRESHOLD:
            # Home is massive underdog
            giant_killing_multiplier = self._get_giant_killing_multiplier(home_odds)
            desperation = self._get_desperation_level(home_odds, away_odds)
            
            return UnderdogPsychology(
                match_type="MASSIVE_UNDERDOG_HOME",
                underdog_team="home",
                underdog_odds=home_odds,
                favorite_odds=away_odds,
                giant_killing_multiplier=giant_killing_multiplier,
                desperation_level=desperation
            )
            
        elif away_odds >= self.HEAVY_UNDERDOG_THRESHOLD:
            # Away is heavy underdog
            return UnderdogPsychology(
                match_type="HEAVY_UNDERDOG_AWAY",
                underdog_team="away",
                underdog_odds=away_odds,
                favorite_odds=home_odds,
                giant_killing_multiplier=2.0,
                desperation_level="MODERATE"
            )
            
        elif home_odds >= self.HEAVY_UNDERDOG_THRESHOLD:
            # Home is heavy underdog
            return UnderdogPsychology(
                match_type="HEAVY_UNDERDOG_HOME",
                underdog_team="home",
                underdog_odds=home_odds,
                favorite_odds=away_odds,
                giant_killing_multiplier=2.0,
                desperation_level="MODERATE"
            )
            
        elif away_odds >= self.MODERATE_UNDERDOG_THRESHOLD:
            # Away is moderate underdog
            return UnderdogPsychology(
                match_type="MODERATE_UNDERDOG_AWAY",
                underdog_team="away",
                underdog_odds=away_odds,
                favorite_odds=home_odds,
                giant_killing_multiplier=1.5,
                desperation_level="LOW"
            )
            
        elif home_odds >= self.MODERATE_UNDERDOG_THRESHOLD:
            # Home is moderate underdog
            return UnderdogPsychology(
                match_type="MODERATE_UNDERDOG_HOME",
                underdog_team="home",
                underdog_odds=home_odds,
                favorite_odds=away_odds,
                giant_killing_multiplier=1.5,
                desperation_level="LOW"
            )
        else:
            # Balanced match - no underdog psychology
            return UnderdogPsychology(
                match_type="BALANCED_MATCH",
                underdog_team=None,
                underdog_odds=max(home_odds, away_odds),
                favorite_odds=min(home_odds, away_odds),
                giant_killing_multiplier=1.0,
                desperation_level="LOW"
            )
    
    def _get_giant_killing_multiplier(self, underdog_odds: float) -> float:
        """Calculate giant-killing multiplier based on underdog odds"""
        if underdog_odds >= 10.0:
            return 4.0  # Massive giant-killing potential
        elif underdog_odds >= 8.0:
            return 3.5  # Very high giant-killing potential
        elif underdog_odds >= 6.0:
            return 3.0  # High giant-killing potential
        elif underdog_odds >= 4.5:
            return 2.5  # Moderate-high giant-killing potential
        else:
            return 2.0  # Some giant-killing potential
    
    def _get_desperation_level(self, underdog_odds: float, favorite_odds: float) -> str:
        """Determine desperation level based on odds gap"""
        odds_ratio = underdog_odds / favorite_odds
        
        if underdog_odds >= 8.0 and odds_ratio >= 6.0:
            return "MAXIMUM"  # David vs Goliath scenario
        elif underdog_odds >= 6.0 and odds_ratio >= 4.0:
            return "HIGH"     # Major upset potential
        elif underdog_odds >= 4.0 and odds_ratio >= 2.5:
            return "MODERATE" # Significant underdog
        else:
            return "LOW"      # Minor underdog
    
    def check_giant_killing_conditions(self, psychology: UnderdogPsychology, match_data: Dict) -> Optional[Dict]:
        """Check if the underdog is in giant-killing mode"""
        
        if psychology.match_type not in ["MASSIVE_UNDERDOG_HOME", "MASSIVE_UNDERDOG_AWAY", 
                                         "HEAVY_UNDERDOG_HOME", "HEAVY_UNDERDOG_AWAY"]:
            # Only significant underdogs generate giant-killing psychology
            return None
        
        minute = match_data.get('minute', 0)
        home_score = match_data.get('home_score', 0)
        away_score = match_data.get('away_score', 0)
        
        # Calculate goal difference from underdog's perspective
        if psychology.underdog_team == 'home':
            goal_difference = home_score - away_score  # Positive if underdog ahead
        else:
            goal_difference = away_score - home_score
        
        # Define giant-killing scenarios based on underdog odds and performance
        giant_killing_scenarios = []
        
        # MAXIMUM GIANT-KILLING: Massive underdog (6.0+ odds) ahead or level
        if psychology.underdog_odds >= self.MASSIVE_UNDERDOG_THRESHOLD:
            if goal_difference >= 0 and minute >= 70:
                giant_killing_scenarios.append({
                    'giant_killing_level': 'MAXIMUM_GIANT_KILLING',
                    'description': f"Massive underdog ({psychology.underdog_odds:.2f}) defying all odds at {minute}'",
                    'desperation_multiplier': 4.0
                })
            elif goal_difference == -1 and minute >= 75:
                giant_killing_scenarios.append({
                    'giant_killing_level': 'HIGH_DESPERATION',
                    'description': f"Massive underdog ({psychology.underdog_odds:.2f}) one goal from miracle at {minute}'",
                    'desperation_multiplier': 3.5
                })
        
        # HIGH GIANT-KILLING: Heavy underdog (4.0+ odds) in striking distance
        elif psychology.underdog_odds >= self.HEAVY_UNDERDOG_THRESHOLD:
            if goal_difference >= 0 and minute >= 70:
                giant_killing_scenarios.append({
                    'giant_killing_level': 'HIGH_GIANT_KILLING',
                    'description': f"Heavy underdog ({psychology.underdog_odds:.2f}) smelling upset at {minute}'",
                    'desperation_multiplier': 3.0
                })
            elif goal_difference == -1 and minute >= 80:
                giant_killing_scenarios.append({
                    'giant_killing_level': 'NOTHING_TO_LOSE',
                    'description': f"Heavy underdog ({psychology.underdog_odds:.2f}) throwing everything forward at {minute}'",
                    'desperation_multiplier': 2.5
                })
        
        # MODERATE GIANT-KILLING: Any significant underdog in final phase
        if psychology.underdog_odds >= 4.0:
            if goal_difference >= -1 and minute >= 85:
                giant_killing_scenarios.append({
                    'giant_killing_level': 'FINAL_DESPERATION',
                    'description': f"Underdog ({psychology.underdog_odds:.2f}) final assault - nothing to lose at {minute}'",
                    'desperation_multiplier': 2.0
                })
        
        # Return the highest intensity scenario if any
        if giant_killing_scenarios:
            # Sort by desperation multiplier (highest first)
            giant_killing_scenarios.sort(key=lambda x: x['desperation_multiplier'], reverse=True)
            return giant_killing_scenarios[0]
        
        return None
    
    def validate_underdog_stats(self, match_data: Dict, momentum_data: Dict, psychology: UnderdogPsychology) -> bool:
        """Validate that live stats support the giant-killing theory"""
        
        minute = match_data.get('minute', 0)
        total_corners = match_data.get('total_corners', 0)
        total_shots = match_data.get('total_shots', 0)
        shots_on_target = match_data.get('total_shots_on_target', 0)
        
        # Get underdog's momentum
        if psychology.underdog_team == 'home':
            underdog_momentum = momentum_data.get('home_momentum10', 0)
        elif psychology.underdog_team == 'away':
            underdog_momentum = momentum_data.get('away_momentum10', 0)
        else:
            return False
        
        # Combined momentum for overall match intensity
        combined_momentum = momentum_data.get('home_momentum10', 0) + momentum_data.get('away_momentum10', 0)
        
        # Apply psychology multiplier to momentum threshold (underdogs need less)
        adjusted_momentum_threshold = self.MIN_MOMENTUM / psychology.giant_killing_multiplier
        
        # Validation criteria (more lenient than favorites - underdogs fight with heart)
        validations = {
            'minute_ok': minute >= self.MIN_MINUTE,
            'corners_ok': total_corners >= self.MIN_CORNERS,
            'shots_ok': total_shots >= self.MIN_SHOTS_TOTAL,
            'shots_target_ok': shots_on_target >= self.MIN_SHOTS_TARGET,
            'momentum_ok': underdog_momentum >= adjusted_momentum_threshold,
            'intensity_ok': combined_momentum >= 120  # STRICTER: High intensity required (was 80)
        }
        
        # Log validation details
        self.logger.info(f"   🥊 Underdog validation for {psychology.match_type}:")
        self.logger.info(f"      Minute: {minute} >= {self.MIN_MINUTE} = {validations['minute_ok']}")
        self.logger.info(f"      Corners: {total_corners} >= {self.MIN_CORNERS} = {validations['corners_ok']}")
        self.logger.info(f"      Shots: {total_shots} >= {self.MIN_SHOTS_TOTAL} = {validations['shots_ok']}")
        self.logger.info(f"      Shots on Target: {shots_on_target} >= {self.MIN_SHOTS_TARGET} = {validations['shots_target_ok']}")
        self.logger.info(f"      Underdog Momentum: {underdog_momentum:.1f} >= {adjusted_momentum_threshold:.1f} = {validations['momentum_ok']}")
        self.logger.info(f"      Combined Intensity: {combined_momentum:.1f} >= 120 = {validations['intensity_ok']}")
        
        # All criteria must pass
        return all(validations.values())
    
    def evaluate_fighting_underdog_alert(self, fixture_data: Dict, match_data: Dict, momentum_data: Dict) -> Optional[Dict]:
        """
        Main evaluation function for fighting underdog corner alerts.
        
        Returns alert data if conditions are met, None otherwise.
        """
        
        # Step 1: Extract 1X2 odds
        odds_data = self.get_1x2_odds_from_fixture(fixture_data)
        if not odds_data:
            self.logger.info("   🔍 No 1X2 odds available - cannot assess underdog psychology")
            return None
        
        home_odds = odds_data['home_odds']
        away_odds = odds_data['away_odds']
        
        # Step 2: Analyze underdog psychological setup
        psychology = self.analyze_underdog_psychology(home_odds, away_odds)
        
        self.logger.info(f"   🥊 Underdog Psychology Profile: {psychology.match_type}")
        self.logger.info(f"      Underdog: {psychology.underdog_team} ({psychology.underdog_odds:.2f})")
        self.logger.info(f"      Giant-Killing Multiplier: {psychology.giant_killing_multiplier:.1f}x")
        self.logger.info(f"      Desperation Level: {psychology.desperation_level}")
        
        # Step 3: Check if we have a significant underdog (our target)
        if psychology.match_type not in ["MASSIVE_UNDERDOG_HOME", "MASSIVE_UNDERDOG_AWAY",
                                         "HEAVY_UNDERDOG_HOME", "HEAVY_UNDERDOG_AWAY"]:
            self.logger.info(f"   ⏭️ Not a significant underdog scenario - skipping fighting underdog system")
            return None
        
        # Step 4: Check giant-killing conditions
        giant_killing_data = self.check_giant_killing_conditions(psychology, match_data)
        if not giant_killing_data:
            self.logger.info(f"   😐 No giant-killing conditions detected - underdog not in fighting mode")
            return None
        
        self.logger.info(f"   🥊 GIANT-KILLING DETECTED: {giant_killing_data['giant_killing_level']}")
        self.logger.info(f"      {giant_killing_data['description']}")
        
        # Step 5: Validate with live stats
        if not self.validate_underdog_stats(match_data, momentum_data, psychology):
            self.logger.info(f"   📊 Live stats don't support giant-killing theory - skipping alert")
            return None
        
        # Step 6: Calculate final giant-killing score
        base_momentum = momentum_data.get('home_momentum10', 0) + momentum_data.get('away_momentum10', 0)
        giant_killing_score = base_momentum * psychology.giant_killing_multiplier * giant_killing_data['desperation_multiplier']
        
        # Step 7: Build alert data
        alert_data = {
            'alert_type': 'FIGHTING_UNDERDOG',
            'psychology_type': psychology.match_type,
            'underdog_team': psychology.underdog_team,
            'underdog_odds': psychology.underdog_odds,
            'favorite_odds': psychology.favorite_odds,
            'giant_killing_level': giant_killing_data['giant_killing_level'],
            'giant_killing_description': giant_killing_data['description'],
            'giant_killing_multiplier': psychology.giant_killing_multiplier,
            'desperation_multiplier': giant_killing_data['desperation_multiplier'],
            'giant_killing_score': giant_killing_score,
            'desperation_level': psychology.desperation_level,
            'reasoning': f"{giant_killing_data['giant_killing_level']}: {psychology.underdog_odds:.2f} underdog in giant-killing mode"
        }
        
        self.logger.info(f"   🥊 FIGHTING UNDERDOG ALERT TRIGGERED!")
        self.logger.info(f"      Giant-Killing Score: {giant_killing_score:.1f}")
        self.logger.info(f"      Reasoning: {alert_data['reasoning']}")
        
        return alert_data


def test_fighting_underdog_system():
    """Test the fighting underdog system with sample data"""
    system = FightingUnderdogSystem()
    
    print("🧪 Testing Fighting Underdog System")
    print("=" * 50)
    
    # Test case 1: Luton (8.00) level 1-1 vs Man City (1.25) at 80'
    print("\n📊 Test 1: Giant-killing scenario - Luton holding City")
    
    fixture_data = {
        'odds': [{
            'bookmaker_id': 2,
            'markets': [{
                'market_id': 1,
                'name': '1X2',
                'selections': [
                    {'label': '1', 'odds': 1.25},  # Man City
                    {'label': 'X', 'odds': 6.50},  # Draw
                    {'label': '2', 'odds': 8.00}   # Luton (massive underdog)
                ]
            }]
        }]
    }
    
    match_data = {
        'minute': 80,
        'home_score': 1,  # City 
        'away_score': 1,  # Luton level!
        'total_corners': 7,
        'total_shots': 14,
        'total_shots_on_target': 4
    }
    
    momentum_data = {
        'home_momentum10': 55,  # City frustrated
        'away_momentum10': 75   # Luton fighting for their lives
    }
    
    result = system.evaluate_fighting_underdog_alert(fixture_data, match_data, momentum_data)
    if result:
        print(f"✅ ALERT: {result['alert_type']}")
        print(f"   Giant-Killing Level: {result['giant_killing_level']}")
        print(f"   Giant-Killing Score: {result['giant_killing_score']:.1f}")
    else:
        print("❌ No alert triggered")
    
    print("\n" + "=" * 50)
    print("🥊 Fighting Underdog System Test Complete!")


if __name__ == "__main__":
    test_fighting_underdog_system()