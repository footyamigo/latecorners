#!/usr/bin/env python3
"""
ENHANCED FIRST HALF CORNER PSYCHOLOGY SYSTEM
============================================
Complete first-half system with 4 psychology types and proper 10-minute momentum window.

Psychology Types:
1. PANICKING_FH_FAVORITE - Heavy favorites struggling at 30min
2. FIGHTING_FH_UNDERDOG - Massive underdogs proving doubters wrong  
3. DESPERATE_SCORER - Any team trailing at 30min
4. BREAKTHROUGH_SEEKER - 0-0 deadlocks needing breakthrough

Target: 30-35 minute alerts for Asian first-half corner markets
Momentum: 10-minute window (20-30 minutes) - SAME as late game
Thresholds: SAME strict standards as late-game system
"""

import logging
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class EnhancedFirstHalfPsychology:
    """Complete psychological profile for first-half situations"""
    psychology_type: str  # PANICKING_FH_FAVORITE, FIGHTING_FH_UNDERDOG, DESPERATE_SCORER, BREAKTHROUGH_SEEKER
    target_team: str      # 'home', 'away', or 'both'
    pressure_level: str   # MAXIMUM, HIGH, MODERATE
    urgency_multiplier: float
    predicted_fh_corners: float
    confidence_level: str  # HIGH, MODERATE, LOW
    home_odds: Optional[float] = None
    away_odds: Optional[float] = None
    reasoning: str = ""

class EnhancedFirstHalfSystem:
    """
    Complete first-half corner system with all 4 psychology types.
    
    Uses same 10-minute momentum window and strict thresholds as late-game system.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # First-half timing (30-35 minute window)
        self.MIN_MINUTE = 30
        self.MAX_MINUTE = 35
        
        # Odds thresholds (same as late game)
        self.HEAVY_FAVORITE_THRESHOLD = 1.40
        self.MASSIVE_FAVORITE_THRESHOLD = 1.25
        self.HEAVY_UNDERDOG_THRESHOLD = 4.00
        self.MASSIVE_UNDERDOG_THRESHOLD = 6.00
        
        # Corner requirements
        self.MIN_CORNERS_FH = 2
        self.MAX_CORNERS_FH = 7
        
        # SAME STRICT MOMENTUM THRESHOLDS AS LATE GAME
        self.MIN_MOMENTUM_FAVORITE = 120      # Same as panicking favorite
        self.MIN_MOMENTUM_UNDERDOG = 100      # Same as fighting underdog
        self.MIN_MOMENTUM_GENERAL = 100       # For desperate/breakthrough
        self.MIN_SHOTS_TOTAL_FH = 10
        self.MIN_SHOTS_TARGET_FH = 4
        
        # SAME STRICT INTENSITY THRESHOLDS
        self.MIN_COMBINED_INTENSITY_FAVORITE = 150  # Same as late favorite
        self.MIN_COMBINED_INTENSITY_UNDERDOG = 120  # Same as late underdog
        self.MIN_COMBINED_INTENSITY_GENERAL = 120
    
    def get_1x2_odds(self, fixture_data: Dict) -> Optional[Dict]:
        """Extract 1X2 odds for psychology analysis"""
        try:
            odds_data = fixture_data.get('odds', [])
            
            for bookmaker in odds_data:
                if bookmaker.get('bookmaker_id') == 2:  # bet365
                    markets = bookmaker.get('markets', [])
                    
                    for market in markets:
                        market_name = market.get('name', '').lower()
                        market_id = market.get('market_id')
                        
                        if ('fulltime result' in market_name or 
                            'match winner' in market_name or 
                            '1x2' in market_name or 
                            market_id == 1):
                            
                            selections = market.get('selections', [])
                            if len(selections) >= 3:
                                home_odds = float(selections[0].get('odds', 0))
                                away_odds = float(selections[2].get('odds', 0))
                                
                                if home_odds > 0 and away_odds > 0:
                                    return {
                                        'home_odds': home_odds,
                                        'away_odds': away_odds
                                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error extracting odds: {e}")
            return None
    
    def analyze_first_half_psychology(self, fixture_data: Dict, match_data: Dict) -> Optional[EnhancedFirstHalfPsychology]:
        """
        Analyze all 4 first-half psychology types at 30-35 minute mark.
        """
        
        minute = match_data.get('minute', 0)
        home_score = match_data.get('home_score', 0)
        away_score = match_data.get('away_score', 0)
        total_corners = match_data.get('total_corners', 0)
        
        # Only analyze in the 30-35 minute window
        if not (self.MIN_MINUTE <= minute <= self.MAX_MINUTE):
            return None
            
        # Only analyze with reasonable corner activity
        if not (self.MIN_CORNERS_FH <= total_corners <= self.MAX_CORNERS_FH):
            self.logger.info(f"   FH: Corner count {total_corners} outside {self.MIN_CORNERS_FH}-{self.MAX_CORNERS_FH} range")
            return None
        
        self.logger.info(f"   🕐 ENHANCED FH ANALYSIS at {minute}min:")
        self.logger.info(f"      Score: {home_score}-{away_score}, Corners: {total_corners}")
        
        # Get odds for favorite/underdog analysis
        odds_data = self.get_1x2_odds(fixture_data)
        
        # Priority 1: PANICKING_FH_FAVORITE - Heavy favorite struggling
        if odds_data:
            home_odds = odds_data['home_odds']
            away_odds = odds_data['away_odds']
            
            # Check for panicking favorite
            if home_odds <= self.HEAVY_FAVORITE_THRESHOLD:
                # Home is heavy favorite
                if home_score <= away_score:  # Favorite not winning
                    pressure_level = "MAXIMUM" if home_odds <= self.MASSIVE_FAVORITE_THRESHOLD else "HIGH"
                    urgency = 2.2 if pressure_level == "MAXIMUM" else 1.8
                    
                    self.logger.info(f"      🔥 PANICKING_FH_FAVORITE detected: Home ({home_odds:.2f}) struggling!")
                    
                    return EnhancedFirstHalfPsychology(
                        psychology_type="PANICKING_FH_FAVORITE",
                        target_team="home",
                        pressure_level=pressure_level,
                        urgency_multiplier=urgency,
                        predicted_fh_corners=self._predict_fh_corners(total_corners, urgency),
                        confidence_level="HIGH",
                        home_odds=home_odds,
                        away_odds=away_odds,
                        reasoning=f"Heavy favorite ({home_odds:.2f}) struggling at {minute}min - panic mode!"
                    )
            
            elif away_odds <= self.HEAVY_FAVORITE_THRESHOLD:
                # Away is heavy favorite  
                if away_score <= home_score:  # Favorite not winning
                    pressure_level = "MAXIMUM" if away_odds <= self.MASSIVE_FAVORITE_THRESHOLD else "HIGH"
                    urgency = 2.2 if pressure_level == "MAXIMUM" else 1.8
                    
                    self.logger.info(f"      🔥 PANICKING_FH_FAVORITE detected: Away ({away_odds:.2f}) struggling!")
                    
                    return EnhancedFirstHalfPsychology(
                        psychology_type="PANICKING_FH_FAVORITE",
                        target_team="away",
                        pressure_level=pressure_level,
                        urgency_multiplier=urgency,
                        predicted_fh_corners=self._predict_fh_corners(total_corners, urgency),
                        confidence_level="HIGH",
                        home_odds=home_odds,
                        away_odds=away_odds,
                        reasoning=f"Heavy favorite ({away_odds:.2f}) struggling at {minute}min - panic mode!"
                    )
            
            # Priority 2: FIGHTING_FH_UNDERDOG - Massive underdog exceeding expectations
            if home_odds >= self.HEAVY_UNDERDOG_THRESHOLD:
                # Home is heavy underdog
                if home_score >= away_score:  # Underdog level or ahead
                    confidence_level = "MAXIMUM" if home_odds >= self.MASSIVE_UNDERDOG_THRESHOLD else "HIGH"
                    urgency = 2.0 if confidence_level == "MAXIMUM" else 1.6
                    
                    self.logger.info(f"      🥊 FIGHTING_FH_UNDERDOG detected: Home ({home_odds:.2f}) exceeding expectations!")
                    
                    return EnhancedFirstHalfPsychology(
                        psychology_type="FIGHTING_FH_UNDERDOG",
                        target_team="home",
                        pressure_level=confidence_level,
                        urgency_multiplier=urgency,
                        predicted_fh_corners=self._predict_fh_corners(total_corners, urgency),
                        confidence_level="HIGH",
                        home_odds=home_odds,
                        away_odds=away_odds,
                        reasoning=f"Massive underdog ({home_odds:.2f}) proving doubters wrong!"
                    )
            
            elif away_odds >= self.HEAVY_UNDERDOG_THRESHOLD:
                # Away is heavy underdog
                if away_score >= home_score:  # Underdog level or ahead
                    confidence_level = "MAXIMUM" if away_odds >= self.MASSIVE_UNDERDOG_THRESHOLD else "HIGH"
                    urgency = 2.0 if confidence_level == "MAXIMUM" else 1.6
                    
                    self.logger.info(f"      🥊 FIGHTING_FH_UNDERDOG detected: Away ({away_odds:.2f}) exceeding expectations!")
                    
                    return EnhancedFirstHalfPsychology(
                        psychology_type="FIGHTING_FH_UNDERDOG",
                        target_team="away",
                        pressure_level=confidence_level,
                        urgency_multiplier=urgency,
                        predicted_fh_corners=self._predict_fh_corners(total_corners, urgency),
                        confidence_level="HIGH",
                        home_odds=home_odds,
                        away_odds=away_odds,
                        reasoning=f"Massive underdog ({away_odds:.2f}) proving doubters wrong!"
                    )
        
        # Priority 3: DESPERATE_SCORER - Any team trailing (regardless of odds)
        if home_score < away_score:
            # Home trailing
            urgency = 1.6 + ((away_score - home_score) * 0.2)  # More urgent with bigger deficit
            
            self.logger.info(f"      ⚠️ DESPERATE_SCORER detected: Home trailing {home_score}-{away_score}")
            
            return EnhancedFirstHalfPsychology(
                psychology_type="DESPERATE_SCORER",
                target_team="home",
                pressure_level="HIGH",
                urgency_multiplier=urgency,
                predicted_fh_corners=self._predict_fh_corners(total_corners, urgency),
                confidence_level="MODERATE",
                home_odds=odds_data.get('home_odds') if odds_data else None,
                away_odds=odds_data.get('away_odds') if odds_data else None,
                reasoning=f"Home trailing {home_score}-{away_score} - desperate for equalizer before HT!"
            )
        
        elif away_score < home_score:
            # Away trailing
            urgency = 1.6 + ((home_score - away_score) * 0.2)
            
            self.logger.info(f"      ⚠️ DESPERATE_SCORER detected: Away trailing {away_score}-{home_score}")
            
            return EnhancedFirstHalfPsychology(
                psychology_type="DESPERATE_SCORER",
                target_team="away",
                pressure_level="HIGH",
                urgency_multiplier=urgency,
                predicted_fh_corners=self._predict_fh_corners(total_corners, urgency),
                confidence_level="MODERATE",
                home_odds=odds_data.get('home_odds') if odds_data else None,
                away_odds=odds_data.get('away_odds') if odds_data else None,
                reasoning=f"Away trailing {away_score}-{home_score} - desperate for equalizer before HT!"
            )
        
        # Priority 4: BREAKTHROUGH_SEEKER - 0-0 or tied, both teams need breakthrough
        else:
            # 0-0 or tied
            if minute >= 32:  # Only after 32min for ties
                urgency = 1.4
                
                self.logger.info(f"      🎯 BREAKTHROUGH_SEEKER detected: {home_score}-{away_score} deadlock")
                
                return EnhancedFirstHalfPsychology(
                    psychology_type="BREAKTHROUGH_SEEKER",
                    target_team="both",
                    pressure_level="MODERATE",
                    urgency_multiplier=urgency,
                    predicted_fh_corners=self._predict_fh_corners(total_corners, urgency),
                    confidence_level="MODERATE",
                    home_odds=odds_data.get('home_odds') if odds_data else None,
                    away_odds=odds_data.get('away_odds') if odds_data else None,
                    reasoning=f"Deadlock at {minute}min - both teams need breakthrough before HT!"
                )
        
        return None
    
    def _predict_fh_corners(self, current_corners: int, urgency: float) -> float:
        """Predict total first-half corners based on psychology"""
        minutes_left = 45 - 30  # 15 minutes left
        current_rate = current_corners / 30  # corners per minute so far
        psychological_boost = urgency * current_rate * minutes_left
        return current_corners + psychological_boost
    
    def validate_first_half_momentum(self, match_data: Dict, momentum_data: Dict, psychology: EnhancedFirstHalfPsychology) -> bool:
        """
        Validate momentum using SAME strict standards as late-game system.
        
        Uses 10-minute momentum window (20-30 minutes).
        """
        
        minute = match_data.get('minute', 0)
        total_corners = match_data.get('total_corners', 0)
        total_shots = sum([
            match_data.get('shots_on_target', {}).get('home', 0),
            match_data.get('shots_on_target', {}).get('away', 0),
            match_data.get('shots_off_target', {}).get('home', 0),
            match_data.get('shots_off_target', {}).get('away', 0)
        ])
        shots_on_target = sum([
            match_data.get('shots_on_target', {}).get('home', 0),
            match_data.get('shots_on_target', {}).get('away', 0)
        ])
        
        # Get 10-minute momentum (20-30min window)
        home_momentum = momentum_data.get('home_momentum_fh', 0)
        away_momentum = momentum_data.get('away_momentum_fh', 0)
        combined_momentum = home_momentum + away_momentum
        
        # Get target team momentum
        if psychology.target_team == 'home':
            target_momentum = home_momentum
        elif psychology.target_team == 'away':
            target_momentum = away_momentum
        else:
            target_momentum = max(home_momentum, away_momentum)
        
        # Select appropriate thresholds based on psychology type
        if psychology.psychology_type == "PANICKING_FH_FAVORITE":
            min_momentum = self.MIN_MOMENTUM_FAVORITE
            min_intensity = self.MIN_COMBINED_INTENSITY_FAVORITE
        elif psychology.psychology_type == "FIGHTING_FH_UNDERDOG":
            min_momentum = self.MIN_MOMENTUM_UNDERDOG
            min_intensity = self.MIN_COMBINED_INTENSITY_UNDERDOG
        else:
            min_momentum = self.MIN_MOMENTUM_GENERAL
            min_intensity = self.MIN_COMBINED_INTENSITY_GENERAL
        
        # Validation criteria (SAME as late game)
        validations = {
            'minute_ok': self.MIN_MINUTE <= minute <= self.MAX_MINUTE,
            'corners_ok': self.MIN_CORNERS_FH <= total_corners <= self.MAX_CORNERS_FH,
            'shots_ok': total_shots >= self.MIN_SHOTS_TOTAL_FH,
            'shots_target_ok': shots_on_target >= self.MIN_SHOTS_TARGET_FH,
            'momentum_ok': target_momentum >= min_momentum,
            'intensity_ok': combined_momentum >= min_intensity
        }
        
        # Log validation details
        self.logger.info(f"   🔍 Enhanced FH validation for {psychology.psychology_type}:")
        self.logger.info(f"      Minute: {minute} in {self.MIN_MINUTE}-{self.MAX_MINUTE} = {validations['minute_ok']}")
        self.logger.info(f"      Corners: {total_corners} in {self.MIN_CORNERS_FH}-{self.MAX_CORNERS_FH} = {validations['corners_ok']}")
        self.logger.info(f"      Shots: {total_shots} >= {self.MIN_SHOTS_TOTAL_FH} = {validations['shots_ok']}")
        self.logger.info(f"      Shots on Target: {shots_on_target} >= {self.MIN_SHOTS_TARGET_FH} = {validations['shots_target_ok']}")
        self.logger.info(f"      Target Momentum: {target_momentum:.1f} >= {min_momentum} = {validations['momentum_ok']}")
        self.logger.info(f"      Combined Intensity: {combined_momentum:.1f} >= {min_intensity} = {validations['intensity_ok']}")
        
        return all(validations.values())
    
    def get_first_half_asian_odds(self, fixture_data: Dict, current_corners: int) -> Optional[Dict]:
        """
        Check for available first-half Asian corner markets using SportMonks API format.
        
        EXACTLY SAME logic as late-game system but looking for first-half market IDs.
        Late-game uses Market ID 61 (Asian Total Corners). First-half uses different market ID.
        """
        try:
            odds_data = fixture_data.get('odds', [])
            compatible_odds = []
            
            # Check if we have nested format (from odds endpoint) or flat format (from inplay endpoint)
            if odds_data and isinstance(odds_data[0], dict) and 'markets' in odds_data[0]:
                # NESTED FORMAT (from odds endpoint)
                for bookmaker in odds_data:
                    if bookmaker.get('bookmaker_id') == 2:  # bet365
                        markets = bookmaker.get('markets', [])
                        
                        for market in markets:
                            market_id = market.get('market_id')
                            market_name = market.get('name', '').lower()
                            
                            # Look for first-half Asian corner markets
                            # CONFIRMED Market IDs: 63 (1st Half Asian Corners), 70 (1st Half Corners)
                            if market_id in [63, 70]:  # First-half corner markets
                                selections = market.get('selections', [])
                                for selection in selections:
                                    try:
                                        line = float(selection.get('line', 0))
                                        odds_value = float(selection.get('odds', 0))
                                        
                                        # SAME filtering as late-game: whole number or current+0.5
                                        if (line > 0 and odds_value > 0 and
                                            (line.is_integer() or line == current_corners + 0.5)):
                                            
                                            compatible_odds.append({
                                                'line': line,
                                                'odds': odds_value,
                                                'selection': selection.get('name', ''),
                                                'market': market_name,
                                                'market_id': market_id
                                            })
                                            
                                    except (ValueError, TypeError):
                                        continue
            else:
                # FLAT FORMAT (from inplay endpoint) - same as late-game fallback
                for odds in odds_data:
                    market_id = odds.get('market_id')
                    bookmaker_id = odds.get('bookmaker_id')
                    
                    # Look for first-half Asian corner markets from bet365
                    if market_id in [63, 70] and bookmaker_id == 2:  # First-half corners from bet365
                        try:
                            total = float(odds.get('total', 0))
                            value = float(odds.get('value', 0))
                            
                            # SAME filtering as late-game: whole number or current+0.5
                            if (total > 0 and value > 0 and
                                (total.is_integer() or total == current_corners + 0.5)):
                                
                                compatible_odds.append({
                                    'line': total,
                                    'odds': value,
                                    'selection': f"{odds.get('label', 'Unknown')} {total}",
                                    'market': f"Market {market_id} - 1st Half Asian Corners",
                                    'market_id': market_id
                                })
                                
                        except (ValueError, TypeError):
                            continue
            
            if compatible_odds:
                self.logger.info(f"   🎯 FH Asian odds available: {len(compatible_odds)} lines")
                for odd in compatible_odds[:3]:  # Show first 3
                    self.logger.info(f"      {odd['selection']}: {odd['odds']:.2f} (Market {odd.get('market_id', 'Unknown')})")
                return {'odds': compatible_odds}
            else:
                self.logger.info(f"   ❌ No compatible FH corner odds found (Markets 63/70 from bet365)")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error checking FH Asian odds: {e}")
            return None

    def evaluate_first_half_alert(self, fixture_data: Dict, match_data: Dict, momentum_data: Dict) -> Optional[Dict]:
        """
        Main evaluation function for enhanced first-half corner alerts.
        REQUIRES Asian corner odds to be available before triggering alert.
        """
        
        # Step 1: Check for first-half Asian corner odds availability
        current_corners = match_data.get('total_corners', 0)
        asian_odds = self.get_first_half_asian_odds(fixture_data, current_corners)
        if not asian_odds:
            self.logger.info(f"   📊 No FH Asian corner odds available - skipping alert")
            return None
        
        # Step 2: Analyze first-half psychology
        psychology = self.analyze_first_half_psychology(fixture_data, match_data)
        if not psychology:
            return None
        
        self.logger.info(f"   🧠 FH Psychology: {psychology.psychology_type}")
        self.logger.info(f"      Target team: {psychology.target_team}")
        self.logger.info(f"      Pressure: {psychology.pressure_level}")
        self.logger.info(f"      Urgency: {psychology.urgency_multiplier:.1f}x")
        self.logger.info(f"      Predicted FH corners: {psychology.predicted_fh_corners:.1f}")
        
        # Step 2: Validate with strict momentum standards
        if not self.validate_first_half_momentum(match_data, momentum_data, psychology):
            self.logger.info(f"   📊 FH momentum doesn't meet strict standards - skipping alert")
            return None
        
        # Step 3: Calculate psychology score
        base_momentum = momentum_data.get('home_momentum_fh', 0) + momentum_data.get('away_momentum_fh', 0)
        fh_psychology_score = base_momentum * psychology.urgency_multiplier
        
        # Step 4: Build alert data
        alert_data = {
            'alert_type': 'FIRST_HALF_CORNER',
            'psychology_type': psychology.psychology_type,
            'target_team': psychology.target_team,
            'pressure_level': psychology.pressure_level,
            'urgency_multiplier': psychology.urgency_multiplier,
            'predicted_fh_corners': psychology.predicted_fh_corners,
            'psychology_score': fh_psychology_score,
            'confidence_level': psychology.confidence_level,
            'reasoning': psychology.reasoning,
            'home_odds': psychology.home_odds,
            'away_odds': psychology.away_odds,
            'available_asian_odds': asian_odds['odds']  # Include available FH Asian corner lines
        }
        
        self.logger.info(f"   🚨 ENHANCED FIRST HALF ALERT TRIGGERED!")
        self.logger.info(f"      Type: {psychology.psychology_type}")
        self.logger.info(f"      Psychology Score: {fh_psychology_score:.1f}")
        self.logger.info(f"      Predicted Corners: {psychology.predicted_fh_corners:.1f}")
        
        return alert_data

def test_enhanced_first_half_system():
    """Test all 4 psychology types"""
    print("🚀 TESTING ENHANCED FIRST-HALF SYSTEM")
    print("=" * 60)
    
    system = EnhancedFirstHalfSystem()
    
    # Test PANICKING_FH_FAVORITE
    print("\n🧪 TEST 1: PANICKING_FH_FAVORITE")
    test_fixture = {
        'odds': [{
            'bookmaker_id': 2,
            'markets': [{
                'name': 'Fulltime Result',
                'selections': [
                    {'odds': 1.30},  # Home heavy favorite
                    {'odds': 5.00},  # Draw
                    {'odds': 8.00}   # Away
                ]
            }]
        }]
    }
    
    test_match = {
        'minute': 32,
        'home_score': 0,  # Favorite struggling
        'away_score': 0,
        'total_corners': 4,
        'shots_on_target': {'home': 3, 'away': 1},
        'shots_off_target': {'home': 5, 'away': 2}
    }
    
    result = system.analyze_first_half_psychology(test_fixture, test_match)
    if result:
        print(f"✅ {result.psychology_type} detected!")
        print(f"   Reasoning: {result.reasoning}")
    else:
        print("❌ No psychology detected")

if __name__ == "__main__":
    test_enhanced_first_half_system()