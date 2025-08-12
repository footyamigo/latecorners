#!/usr/bin/env python3
"""
PANICKING FAVORITE CORNER SYSTEM
================================
Psychology-driven corner alerts targeting heavy favorites under pressure.

When a heavy favorite (1.20-1.40 odds) is drawing/losing in the final phase,
they enter PANIC MODE and abandon tactical discipline to force a result.
This creates predictable corner explosion patterns.
"""

import logging
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PsychologyProfile:
    """Psychological pressure profile for a match"""
    match_type: str  # HEAVY_FAVORITE, CLEAR_FAVORITE, BALANCED
    favorite_team: str  # 'home', 'away', or None
    favorite_odds: float
    underdog_odds: float
    pressure_multiplier: float
    confidence_level: str  # MAXIMUM, HIGH, MODERATE, LOW

class PanickingFavoriteSystem:
    """
    Revolutionary corner system exploiting heavy favorite psychology.
    
    Core Insight: Heavy favorites (1.20-1.40 odds) under pressure create
    predictable corner patterns due to psychological panic and tactical abandonment.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Psychology thresholds
        self.HEAVY_FAVORITE_THRESHOLD = 1.40
        self.MASSIVE_FAVORITE_THRESHOLD = 1.25
        self.CLEAR_FAVORITE_THRESHOLD = 1.80
        
        # STRICTER stats requirements - focus on corner storm potential
        self.MIN_MOMENTUM = 120  # INCREASED: Explosive momentum only (was 75)
        self.MIN_CORNERS = 6     # Some corner activity established
        self.MIN_SHOTS_TOTAL = 15  # INCREASED: High attacking volume (was 12)
        self.MIN_SHOTS_TARGET = 6   # INCREASED: Quality attempts showing desperation (was 4)
        self.MIN_MINUTE = 75     # Final phase only
        
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
    
    def analyze_psychology_profile(self, home_odds: float, away_odds: float) -> PsychologyProfile:
        """Analyze the psychological pressure setup based on prematch odds"""
        
        # Determine favorite and pressure levels
        if home_odds <= self.HEAVY_FAVORITE_THRESHOLD:
            # Home is heavy favorite
            pressure_multiplier = self._get_pressure_multiplier(home_odds)
            confidence = self._get_confidence_level(home_odds, away_odds)
            
            return PsychologyProfile(
                match_type="HEAVY_FAVORITE_HOME",
                favorite_team="home",
                favorite_odds=home_odds,
                underdog_odds=away_odds,
                pressure_multiplier=pressure_multiplier,
                confidence_level=confidence
            )
            
        elif away_odds <= self.HEAVY_FAVORITE_THRESHOLD:
            # Away is heavy favorite
            pressure_multiplier = self._get_pressure_multiplier(away_odds)
            confidence = self._get_confidence_level(away_odds, home_odds)
            
            return PsychologyProfile(
                match_type="HEAVY_FAVORITE_AWAY",
                favorite_team="away", 
                favorite_odds=away_odds,
                underdog_odds=home_odds,
                pressure_multiplier=pressure_multiplier,
                confidence_level=confidence
            )
            
        elif home_odds <= self.CLEAR_FAVORITE_THRESHOLD:
            # Home is clear favorite (but not heavy)
            return PsychologyProfile(
                match_type="CLEAR_FAVORITE_HOME",
                favorite_team="home",
                favorite_odds=home_odds,
                underdog_odds=away_odds,
                pressure_multiplier=1.5,
                confidence_level="MODERATE"
            )
            
        elif away_odds <= self.CLEAR_FAVORITE_THRESHOLD:
            # Away is clear favorite (but not heavy)
            return PsychologyProfile(
                match_type="CLEAR_FAVORITE_AWAY",
                favorite_team="away",
                favorite_odds=away_odds,
                underdog_odds=home_odds,
                pressure_multiplier=1.5,
                confidence_level="MODERATE"
            )
        else:
            # Balanced match - no psychological edge
            return PsychologyProfile(
                match_type="BALANCED_MATCH",
                favorite_team=None,
                favorite_odds=min(home_odds, away_odds),
                underdog_odds=max(home_odds, away_odds),
                pressure_multiplier=1.0,
                confidence_level="LOW"
            )
    
    def _get_pressure_multiplier(self, favorite_odds: float) -> float:
        """Calculate psychological pressure multiplier based on favorite odds"""
        if favorite_odds <= 1.20:
            return 3.5  # Massive pressure
        elif favorite_odds <= 1.25:
            return 3.0  # Very high pressure
        elif favorite_odds <= 1.30:
            return 2.5  # High pressure
        elif favorite_odds <= 1.35:
            return 2.0  # Moderate-high pressure
        else:
            return 1.5  # Some pressure
    
    def _get_confidence_level(self, favorite_odds: float, underdog_odds: float) -> str:
        """Determine confidence level based on odds gap"""
        odds_ratio = underdog_odds / favorite_odds
        
        if favorite_odds <= 1.25 and odds_ratio >= 8.0:
            return "MAXIMUM"  # Massive favorite vs massive underdog
        elif favorite_odds <= 1.30 and odds_ratio >= 5.0:
            return "HIGH"     # Heavy favorite vs heavy underdog
        elif favorite_odds <= 1.40 and odds_ratio >= 3.0:
            return "MODERATE" # Clear favorite vs clear underdog
        else:
            return "LOW"      # Not enough gap for strong psychology
    
    def check_panic_conditions(self, psychology: PsychologyProfile, match_data: Dict) -> Optional[Dict]:
        """Check if the favorite is in panic mode (not meeting expectations)"""
        
        if psychology.match_type not in ["HEAVY_FAVORITE_HOME", "HEAVY_FAVORITE_AWAY"]:
            # Only heavy favorites generate enough panic for our system
            return None
        
        minute = match_data.get('minute', 0)
        home_score = match_data.get('home_score', 0)
        away_score = match_data.get('away_score', 0)
        
        # Calculate goal difference from favorite's perspective
        if psychology.favorite_team == 'home':
            goal_difference = home_score - away_score
        else:
            goal_difference = away_score - home_score
        
        # Define panic scenarios based on favorite odds and performance
        panic_scenarios = []
        
        # MAXIMUM PANIC: Massive favorite (1.25 or less) not winning in final phase
        if psychology.favorite_odds <= self.MASSIVE_FAVORITE_THRESHOLD:
            if goal_difference <= 0 and minute >= 80:
                panic_scenarios.append({
                    'panic_level': 'MAXIMUM_PANIC',
                    'description': f"Massive favorite ({psychology.favorite_odds:.2f}) not winning at {minute}'",
                    'urgency_multiplier': 3.5
                })
            elif goal_difference <= 1 and minute >= 85:
                panic_scenarios.append({
                    'panic_level': 'HIGH_PANIC', 
                    'description': f"Massive favorite ({psychology.favorite_odds:.2f}) barely ahead at {minute}'",
                    'urgency_multiplier': 3.0
                })
        
        # HIGH PANIC: Heavy favorite (1.30 or less) struggling
        elif psychology.favorite_odds <= 1.30:
            if goal_difference <= 0 and minute >= 75:
                panic_scenarios.append({
                    'panic_level': 'HIGH_PANIC',
                    'description': f"Heavy favorite ({psychology.favorite_odds:.2f}) not winning at {minute}'",
                    'urgency_multiplier': 2.5
                })
            elif goal_difference <= 1 and minute >= 80:
                panic_scenarios.append({
                    'panic_level': 'BUILDING_PANIC',
                    'description': f"Heavy favorite ({psychology.favorite_odds:.2f}) only 1 goal up at {minute}'",
                    'urgency_multiplier': 2.0
                })
        
        # BUILDING PANIC: Clear heavy favorite (1.40 or less) underperforming
        elif psychology.favorite_odds <= self.HEAVY_FAVORITE_THRESHOLD:
            if goal_difference <= 0 and minute >= 75:
                panic_scenarios.append({
                    'panic_level': 'BUILDING_PANIC',
                    'description': f"Heavy favorite ({psychology.favorite_odds:.2f}) drawing/losing at {minute}'",
                    'urgency_multiplier': 1.8
                })
            elif goal_difference < 0 and minute >= 70:
                panic_scenarios.append({
                    'panic_level': 'HIGH_PANIC',
                    'description': f"Heavy favorite ({psychology.favorite_odds:.2f}) actually losing at {minute}'",
                    'urgency_multiplier': 2.5
                })
        
        # Return the highest panic scenario if any
        if panic_scenarios:
            # Sort by urgency multiplier (highest first)
            panic_scenarios.sort(key=lambda x: x['urgency_multiplier'], reverse=True)
            return panic_scenarios[0]
        
        return None
    
    def validate_live_stats(self, match_data: Dict, momentum_data: Dict, psychology: PsychologyProfile) -> bool:
        """Validate that live stats support the panic theory"""
        
        minute = match_data.get('minute', 0)
        total_corners = match_data.get('total_corners', 0)
        total_shots = match_data.get('total_shots', 0)
        shots_on_target = match_data.get('total_shots_on_target', 0)
        
        # Get favorite's momentum
        if psychology.favorite_team == 'home':
            favorite_momentum = momentum_data.get('home_momentum10', 0)
        elif psychology.favorite_team == 'away':
            favorite_momentum = momentum_data.get('away_momentum10', 0)
        else:
            return False
        
        # Combined momentum for overall match intensity
        combined_momentum = momentum_data.get('home_momentum10', 0) + momentum_data.get('away_momentum10', 0)
        
        # Apply psychology multiplier to momentum threshold
        adjusted_momentum_threshold = self.MIN_MOMENTUM / psychology.pressure_multiplier
        
        # Validation criteria
        validations = {
            'minute_ok': minute >= self.MIN_MINUTE,
            'corners_ok': total_corners >= self.MIN_CORNERS,
            'shots_ok': total_shots >= self.MIN_SHOTS_TOTAL,
            'shots_target_ok': shots_on_target >= self.MIN_SHOTS_TARGET,
            'momentum_ok': favorite_momentum >= adjusted_momentum_threshold,
            'intensity_ok': combined_momentum >= 150  # STRICTER: Very high overall intensity (was 100)
        }
        
        # Log validation details
        self.logger.info(f"   🧠 Psychology validation for {psychology.match_type}:")
        self.logger.info(f"      Minute: {minute} >= {self.MIN_MINUTE} = {validations['minute_ok']}")
        self.logger.info(f"      Corners: {total_corners} >= {self.MIN_CORNERS} = {validations['corners_ok']}")
        self.logger.info(f"      Shots: {total_shots} >= {self.MIN_SHOTS_TOTAL} = {validations['shots_ok']}")
        self.logger.info(f"      Shots on Target: {shots_on_target} >= {self.MIN_SHOTS_TARGET} = {validations['shots_target_ok']}")
        self.logger.info(f"      Favorite Momentum: {favorite_momentum:.1f} >= {adjusted_momentum_threshold:.1f} = {validations['momentum_ok']}")
        self.logger.info(f"      Combined Intensity: {combined_momentum:.1f} >= 150 = {validations['intensity_ok']}")
        
        # All criteria must pass
        return all(validations.values())
    
    def evaluate_panicking_favorite_alert(self, fixture_data: Dict, match_data: Dict, momentum_data: Dict) -> Optional[Dict]:
        """
        Main evaluation function for panicking favorite corner alerts.
        
        Returns alert data if conditions are met, None otherwise.
        """
        
        # Step 1: Extract 1X2 odds
        odds_data = self.get_1x2_odds_from_fixture(fixture_data)
        if not odds_data:
            self.logger.info("   🔍 No 1X2 odds available - cannot assess psychology")
            return None
        
        home_odds = odds_data['home_odds']
        away_odds = odds_data['away_odds']
        
        # Step 2: Analyze psychological pressure setup
        psychology = self.analyze_psychology_profile(home_odds, away_odds)
        
        self.logger.info(f"   🧠 Psychology Profile: {psychology.match_type}")
        self.logger.info(f"      Favorite: {psychology.favorite_team} ({psychology.favorite_odds:.2f})")
        self.logger.info(f"      Pressure Multiplier: {psychology.pressure_multiplier:.1f}x")
        self.logger.info(f"      Confidence: {psychology.confidence_level}")
        
        # Step 3: Check if we have a heavy favorite (our target)
        if psychology.match_type not in ["HEAVY_FAVORITE_HOME", "HEAVY_FAVORITE_AWAY"]:
            self.logger.info(f"   ⏭️ Not a heavy favorite scenario - skipping psychology system")
            return None
        
        # Step 4: Check panic conditions
        panic_data = self.check_panic_conditions(psychology, match_data)
        if not panic_data:
            self.logger.info(f"   😌 No panic conditions detected - favorite meeting expectations")
            return None
        
        self.logger.info(f"   🚨 PANIC DETECTED: {panic_data['panic_level']}")
        self.logger.info(f"      {panic_data['description']}")
        
        # Step 5: Validate with live stats
        if not self.validate_live_stats(match_data, momentum_data, psychology):
            self.logger.info(f"   📊 Live stats don't support panic theory - skipping alert")
            return None
        
        # Step 6: Calculate final psychology score
        base_momentum = momentum_data.get('home_momentum10', 0) + momentum_data.get('away_momentum10', 0)
        psychology_score = base_momentum * psychology.pressure_multiplier * panic_data['urgency_multiplier']
        
        # Step 7: Build alert data
        alert_data = {
            'alert_type': 'PANICKING_FAVORITE',
            'psychology_type': psychology.match_type,
            'favorite_team': psychology.favorite_team,
            'favorite_odds': psychology.favorite_odds,
            'underdog_odds': psychology.underdog_odds,
            'panic_level': panic_data['panic_level'],
            'panic_description': panic_data['description'],
            'pressure_multiplier': psychology.pressure_multiplier,
            'urgency_multiplier': panic_data['urgency_multiplier'],
            'psychology_score': psychology_score,
            'confidence_level': psychology.confidence_level,
            'reasoning': f"{panic_data['panic_level']}: {psychology.favorite_odds:.2f} favorite under maximum pressure"
        }
        
        self.logger.info(f"   🎯 PANICKING FAVORITE ALERT TRIGGERED!")
        self.logger.info(f"      Psychology Score: {psychology_score:.1f}")
        self.logger.info(f"      Reasoning: {alert_data['reasoning']}")
        
        return alert_data


def test_panicking_favorite_system():
    """Test the panicking favorite system with sample data"""
    system = PanickingFavoriteSystem()
    
    print("🧪 Testing Panicking Favorite System")
    print("=" * 50)
    
    # Test case 1: Man City (1.25) drawing 0-0 vs Luton at 85'
    print("\n📊 Test 1: Massive favorite panic scenario")
    
    fixture_data = {
        'odds': [{
            'bookmaker_id': 2,
            'markets': [{
                'market_id': 1,
                'name': '1X2',
                'selections': [
                    {'label': '1', 'odds': 1.25},  # Man City
                    {'label': 'X', 'odds': 6.50},  # Draw
                    {'label': '2', 'odds': 12.00}  # Luton
                ]
            }]
        }]
    }
    
    match_data = {
        'minute': 85,
        'home_score': 0,
        'away_score': 0,
        'total_corners': 8,
        'total_shots': 18,
        'total_shots_on_target': 6
    }
    
    momentum_data = {
        'home_momentum10': 85,  # City desperate
        'away_momentum10': 45   # Luton defending
    }
    
    result = system.evaluate_panicking_favorite_alert(fixture_data, match_data, momentum_data)
    if result:
        print(f"✅ ALERT: {result['alert_type']}")
        print(f"   Panic Level: {result['panic_level']}")
        print(f"   Psychology Score: {result['psychology_score']:.1f}")
    else:
        print("❌ No alert triggered")
    
    print("\n" + "=" * 50)
    print("🎯 Panicking Favorite System Test Complete!")


if __name__ == "__main__":
    test_panicking_favorite_system()