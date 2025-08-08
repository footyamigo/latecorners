#!/usr/bin/env python3
"""
Corner prediction system using momentum tracking and pattern detection
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class MomentumIndicators:
    """Track team momentum indicators"""
    attack_momentum: float = 0.0      # 0-100: Based on dangerous attacks and shots
    territory_momentum: float = 0.0   # 0-100: Based on possession and field position
    pressure_momentum: float = 0.0    # 0-100: Based on shots blocked and crosses
    overall_momentum: float = 0.0     # 0-100: Weighted combination

@dataclass
class CornerPattern:
    """Define patterns that often lead to corners"""
    name: str
    description: str
    conditions: Dict[str, any]
    weight: float  # How strongly this pattern indicates a corner

class CornerMomentumSystem:
    """
    Predict corners using momentum tracking and pattern detection
    """
    
    def __init__(self):
        # Configure momentum weights
        self.momentum_weights = {
            'dangerous_attacks': 2.5,    # High impact
            'shots_blocked': 2.0,        # Very relevant
            'crosses': 2.0,              # Direct indicator
            'shots_on_target': 1.5,      # Good pressure
            'possession': 1.0,           # Base factor
            'territory': 1.5,            # Field position
            'successful_dribbles': 1.0,  # Build-up
            'key_passes': 1.2            # Chance creation
        }
        
        # Define corner patterns
        self.patterns = [
            CornerPattern(
                name="High Pressure Pattern",
                description="Sustained attacking pressure with blocked shots",
                conditions={
                    'shots_blocked_last_5': {'min': 2},
                    'dangerous_attacks_last_5': {'min': 3},
                    'possession_last_5': {'min': 60},
                    'territory_last_5': {'min': 65}
                },
                weight=3.0
            ),
            CornerPattern(
                name="Wing Attack Pattern",
                description="Heavy focus on wing play with crosses",
                conditions={
                    'crosses_last_5': {'min': 3},
                    'successful_dribbles_last_5': {'min': 2},
                    'attacks_last_5': {'min': 4}
                },
                weight=2.5
            ),
            CornerPattern(
                name="Shot Blocking Pattern",
                description="Multiple blocked shots indicating defensive pressure",
                conditions={
                    'shots_blocked_last_5': {'min': 2},
                    'shots_total_last_5': {'min': 3},
                    'possession_last_5': {'min': 55}
                },
                weight=2.0
            ),
            CornerPattern(
                name="Territory Dominance",
                description="Strong territorial control with attacks",
                conditions={
                    'possession_last_5': {'min': 65},
                    'territory_last_5': {'min': 70},
                    'dangerous_attacks_last_5': {'min': 2}
                },
                weight=2.0
            ),
            CornerPattern(
                name="Quick Attack Pattern",
                description="Rapid succession of attacks and shots",
                conditions={
                    'dangerous_attacks_last_3': {'min': 2},
                    'shots_total_last_3': {'min': 2},
                    'attacks_last_3': {'min': 3}
                },
                weight=1.5
            )
        ]
        
        logger.info("✅ Initialized Corner Momentum System")
        logger.info(f"   Patterns loaded: {len(self.patterns)}")
    
    def calculate_momentum(self, stats: Dict, window_minutes: int = 5) -> Dict[str, MomentumIndicators]:
        """
        Calculate momentum indicators for both teams
        
        Args:
            stats: Dictionary with recent match statistics
            window_minutes: Time window to consider
            
        Returns:
            Dict with momentum indicators for each team
        """
        momentum = {'home': MomentumIndicators(), 'away': MomentumIndicators()}
        
        for team in ['home', 'away']:
            # 1. Attack Momentum (0-100)
            attack_score = (
                stats['dangerous_attacks'][team] * self.momentum_weights['dangerous_attacks'] +
                stats['shots_on_target'][team] * self.momentum_weights['shots_on_target'] +
                stats['key_passes'][team] * self.momentum_weights['key_passes']
            ) / window_minutes * 10
            
            # 2. Territory Momentum (0-100)
            territory_score = (
                stats['possession'][team] * self.momentum_weights['possession'] +
                stats['successful_dribbles'][team] * self.momentum_weights['successful_dribbles'] +
                stats['territory'][team] * self.momentum_weights['territory']
            ) / 3
            
            # 3. Pressure Momentum (0-100)
            pressure_score = (
                stats['shots_blocked'][team] * self.momentum_weights['shots_blocked'] +
                stats['crosses'][team] * self.momentum_weights['crosses']
            ) / window_minutes * 20
            
            # Cap scores at 100
            momentum[team].attack_momentum = min(100, attack_score)
            momentum[team].territory_momentum = min(100, territory_score)
            momentum[team].pressure_momentum = min(100, pressure_score)
            
            # Overall momentum (weighted average)
            momentum[team].overall_momentum = min(100, (
                momentum[team].attack_momentum * 0.4 +
                momentum[team].territory_momentum * 0.3 +
                momentum[team].pressure_momentum * 0.3
            ))
        
        return momentum
    
    def detect_patterns(self, stats: Dict) -> Dict[str, List[CornerPattern]]:
        """
        Detect active corner patterns for both teams
        
        Args:
            stats: Dictionary with recent match statistics
            
        Returns:
            Dict with detected patterns for each team
        """
        detected = {'home': [], 'away': []}
        
        for team in ['home', 'away']:
            for pattern in self.patterns:
                pattern_matched = True
                
                # Check each condition
                for stat_name, condition in pattern.conditions.items():
                    # Extract time window from stat name (e.g., 'shots_blocked_last_5')
                    base_stat = '_'.join(stat_name.split('_')[:-2])  # Remove '_last_X'
                    window = int(stat_name.split('_')[-1])
                    
                    # Get actual value
                    if base_stat in stats:
                        actual_value = stats[base_stat][team]
                        
                        # Check minimum condition
                        if 'min' in condition and actual_value < condition['min']:
                            pattern_matched = False
                            break
                            
                        # Check maximum condition
                        if 'max' in condition and actual_value > condition['max']:
                            pattern_matched = False
                            break
                
                if pattern_matched:
                    detected[team].append(pattern)
        
        return detected
    
    def calculate_corner_probability(self, stats: Dict) -> Dict[str, Dict[str, float]]:
        """
        Calculate corner probability for both teams
        
        Args:
            stats: Dictionary with recent match statistics
            
        Returns:
            Dict with probabilities and contributing factors
        """
        # Get momentum and patterns
        momentum = self.calculate_momentum(stats)
        patterns = self.detect_patterns(stats)
        
        probabilities = {}
        for team in ['home', 'away']:
            # Base probability from momentum (0-50%)
            base_prob = momentum[team].overall_momentum * 0.5
            
            # Additional probability from patterns (0-50%)
            pattern_prob = min(50, sum(p.weight * 10 for p in patterns[team]))
            
            # Combine probabilities
            total_prob = min(100, base_prob + pattern_prob)
            
            probabilities[team] = {
                'total_probability': total_prob,
                'momentum_contribution': base_prob,
                'pattern_contribution': pattern_prob,
                'momentum_indicators': {
                    'attack': momentum[team].attack_momentum,
                    'territory': momentum[team].territory_momentum,
                    'pressure': momentum[team].pressure_momentum,
                    'overall': momentum[team].overall_momentum
                },
                'detected_patterns': [
                    {'name': p.name, 'weight': p.weight}
                    for p in patterns[team]
                ]
            }
        
        return probabilities
    
    def should_alert(self, stats: Dict) -> Dict[str, bool]:
        """
        Determine if corner alert should be triggered
        
        Args:
            stats: Dictionary with recent match statistics
            
        Returns:
            Dict indicating if alert should be triggered for each team
        """
        probabilities = self.calculate_corner_probability(stats)
        alerts = {'home': False, 'away': False}
        
        for team in ['home', 'away']:
            prob = probabilities[team]
            
            # Alert criteria:
            # 1. High total probability (>70%)
            # 2. Strong momentum (>60)
            # 3. At least one strong pattern detected
            alerts[team] = (
                prob['total_probability'] >= 70 and
                prob['momentum_indicators']['overall'] >= 60 and
                len(prob['detected_patterns']) >= 1 and
                any(p['weight'] >= 2.0 for p in prob['detected_patterns'])
            )
        
        return alerts