"""
First Half Corner Alert System

This system focuses on predicting corners in the 30-35 minute window of the first half,
using different patterns and thresholds than the late-game system.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class FirstHalfContext:
    minute: int
    score_diff: int
    total_corners: int
    corners_last_10: int
    is_home: bool

@dataclass
class FirstHalfMomentum:
    attack_intensity: float  # Based on dangerous attacks and total attacks
    shot_efficiency: float  # Shots on target vs total shots
    corner_rate: float      # Corners per attack ratio
    pressure_score: float   # Combined score of all metrics

@dataclass
class FirstHalfPattern:
    name: str
    conditions: List[str]
    weight: float

class FirstHalfCornerSystem:
    def __init__(self):
        """Initialize first half corner prediction system"""
        logger.info("✅ Initialized First Half Corner System")
        
        # Define first half specific patterns
        self.patterns = [
            FirstHalfPattern(
                name="Early Pressure",
                conditions=[
                    "High dangerous attacks ratio",
                    "Multiple shots on target",
                    "Possession dominance"
                ],
                weight=2.5
            ),
            FirstHalfPattern(
                name="Corner Generator",
                conditions=[
                    "Above average corner rate",
                    "Consistent attacking presence",
                    "Good shot accuracy"
                ],
                weight=2.0
            ),
            FirstHalfPattern(
                name="Tactical Advantage",
                conditions=[
                    "Superior shot efficiency",
                    "High quality attacks",
                    "Territory control"
                ],
                weight=1.8
            ),
            FirstHalfPattern(
                name="Early Game Push",
                conditions=[
                    "Aggressive start",
                    "Multiple early corners",
                    "Shot volume"
                ],
                weight=1.5
            )
        ]
        
        logger.info(f"Patterns loaded: {len(self.patterns)}")

    def calculate_first_half_momentum(self, current_stats: Dict, previous_stats: Dict, window_minutes: int = 10) -> FirstHalfMomentum:
        """Calculate momentum indicators specific to first half"""
        
        # Calculate deltas over the time window
        deltas = {
            'dangerous_attacks': {
                'home': current_stats.get('dangerous_attacks', {}).get('home', 0) - 
                        previous_stats.get('dangerous_attacks', {}).get('home', 0),
                'away': current_stats.get('dangerous_attacks', {}).get('away', 0) - 
                        previous_stats.get('dangerous_attacks', {}).get('away', 0)
            },
            'attacks': {
                'home': current_stats.get('attacks', {}).get('home', 0) - 
                        previous_stats.get('attacks', {}).get('home', 0),
                'away': current_stats.get('attacks', {}).get('away', 0) - 
                        previous_stats.get('attacks', {}).get('away', 0)
            },
            'shots_on_target': {
                'home': current_stats.get('shots_on_target', {}).get('home', 0) - 
                        previous_stats.get('shots_on_target', {}).get('home', 0),
                'away': current_stats.get('shots_on_target', {}).get('away', 0) - 
                        previous_stats.get('shots_on_target', {}).get('away', 0)
            },
            'corners': (current_stats.get('total_corners', 0) - previous_stats.get('total_corners', 0))
        }
        
        # Calculate first half specific metrics
        attack_intensity = (
            (deltas['dangerous_attacks']['home'] + deltas['dangerous_attacks']['away']) / 
            max(1, deltas['attacks']['home'] + deltas['attacks']['away'])
        ) * 100
        
        shot_efficiency = (
            (deltas['shots_on_target']['home'] + deltas['shots_on_target']['away']) /
            max(1, deltas['attacks']['home'] + deltas['attacks']['away'])
        ) * 100
        
        corner_rate = (
            deltas['corners'] /
            max(1, deltas['attacks']['home'] + deltas['attacks']['away'])
        ) * 100
        
        # Combined pressure score weighted for first half
        pressure_score = (
            (attack_intensity * 0.4) +
            (shot_efficiency * 0.3) +
            (corner_rate * 0.3)
        )
        
        return FirstHalfMomentum(
            attack_intensity=attack_intensity,
            shot_efficiency=shot_efficiency,
            corner_rate=corner_rate,
            pressure_score=pressure_score
        )

    def detect_patterns(self, stats: Dict, momentum: FirstHalfMomentum) -> List[FirstHalfPattern]:
        """Detect active patterns in first half context"""
        detected = []
        
        for pattern in self.patterns:
            # Pattern specific thresholds for first half
            if pattern.name == "Early Pressure":
                if (momentum.attack_intensity >= 50 and
                    momentum.pressure_score >= 40):
                    detected.append(pattern)
                    
            elif pattern.name == "Corner Generator":
                if (momentum.corner_rate >= 15 and
                    momentum.attack_intensity >= 40):
                    detected.append(pattern)
                    
            elif pattern.name == "Tactical Advantage":
                if (momentum.shot_efficiency >= 30 and
                    momentum.pressure_score >= 35):
                    detected.append(pattern)
                    
            elif pattern.name == "Early Game Push":
                if (momentum.attack_intensity >= 45 and
                    momentum.corner_rate >= 10):
                    detected.append(pattern)
        
        return detected

    def should_alert(self, current_stats: Dict, previous_stats: Dict, window_minutes: int = 10) -> Dict:
        """Evaluate if conditions warrant a first half corner alert"""
        
        # Basic checks
        minute = current_stats.get('minute', 0)
        if not (30 <= minute <= 35):
            logger.info(f"❌ Outside first half alert window (need 30-35', currently {minute}')")
            return {'alert': False, 'reasons': [f"Wrong timing: {minute}'"]}
            
        # Calculate momentum
        momentum = self.calculate_first_half_momentum(current_stats, previous_stats, window_minutes)
        
        # Detect patterns
        patterns = self.detect_patterns(current_stats, momentum)
        
        # Log detailed metrics
        logger.info("\n📊 FIRST HALF METRICS:")
        logger.info(f"• Attack Intensity: {momentum.attack_intensity:.1f}%")
        logger.info(f"• Shot Efficiency: {momentum.shot_efficiency:.1f}%")
        logger.info(f"• Corner Rate: {momentum.corner_rate:.1f}%")
        logger.info(f"• Pressure Score: {momentum.pressure_score:.1f}")
        logger.info(f"• Patterns Found: {len(patterns)}")
        
        # Alert criteria for first half
        alert_worthy = (
            momentum.pressure_score >= 45 and  # High overall pressure
            len(patterns) >= 2 and            # Multiple patterns detected
            any(p.weight >= 2.0 for p in patterns)  # At least one strong pattern
        )
        
        if alert_worthy:
            return {
                'alert': True,
                'momentum_indicators': {
                    'attack_intensity': momentum.attack_intensity,
                    'shot_efficiency': momentum.shot_efficiency,
                    'corner_rate': momentum.corner_rate,
                    'pressure_score': momentum.pressure_score
                },
                'detected_patterns': [
                    {'name': p.name, 'weight': p.weight} for p in patterns
                ],
                'reasons': [
                    f"Strong pressure score: {momentum.pressure_score:.1f}",
                    f"Multiple patterns detected: {len(patterns)}",
                    f"High attack intensity: {momentum.attack_intensity:.1f}%"
                ]
            }
        
        return {
            'alert': False,
            'reasons': [
                f"Low pressure score: {momentum.pressure_score:.1f}",
                f"Insufficient patterns: {len(patterns)}",
                f"Weak attack intensity: {momentum.attack_intensity:.1f}%"
            ]
        }