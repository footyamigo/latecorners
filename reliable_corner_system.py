#!/usr/bin/env python3
"""
Corner prediction system using only reliable live stats
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class MatchContext:
    """Match context that affects corner probability"""
    minute: int = 0
    score_diff: int = 0  # Positive if team is winning, negative if losing
    is_home: bool = False
    total_corners: int = 0
    corners_last_15: int = 0
    
@dataclass
class TeamMomentum:
    """Track team momentum using reliable stats only"""
    attack_intensity: float = 0.0    # Based on dangerous_attacks vs attacks ratio
    shot_efficiency: float = 0.0     # Based on shots on target ratio
    attack_volume: float = 0.0       # Based on total attacks per minute
    corner_momentum: float = 0.0     # Based on corners per minute and efficiency
    score_context: float = 0.0       # Based on scoreline and timing
    overall_momentum: float = 0.0    # Combined score

@dataclass
class ReliablePattern:
    """Patterns using only reliable stats"""
    name: str
    description: str
    conditions: Dict[str, any]
    weight: float

class ReliableCornerSystem:
    """
    Corner prediction using only reliable live stats
    """
    
    def __init__(self):
        # Define patterns using only reliable stats
        self.patterns = [
            # Core Attack Patterns
            ReliablePattern(
                name="High Attack Quality",
                description="High ratio of dangerous attacks to total attacks",
                conditions={
                    'dangerous_attacks_last_5': {'min': 8},
                    'dangerous_attack_ratio': {'min': 0.7}  # 70% of attacks are dangerous
                },
                weight=2.0
            ),
            ReliablePattern(
                name="Shot Accuracy Pattern",
                description="Good ratio of shots on target",
                conditions={
                    'shots_total_last_5': {'min': 3},
                    'shot_accuracy_ratio': {'min': 0.4}  # 40% shots on target
                },
                weight=1.5
            ),
            
            # Corner-Specific Patterns
            ReliablePattern(
                name="Corner Generation",
                description="High corner efficiency from attacks",
                conditions={
                    'attacks_last_5': {'min': 10},
                    'corner_efficiency': {'min': 0.15}  # 15% of attacks lead to corners
                },
                weight=2.5
            ),
            ReliablePattern(
                name="Corner Momentum",
                description="Recent corner frequency",
                conditions={
                    'corners_per_minute': {'min': 0.4}  # Corner every 2.5 minutes
                },
                weight=2.5
            ),
            
            # Pressure Patterns
            ReliablePattern(
                name="Attack Pressure",
                description="High volume of dangerous attacks",
                conditions={
                    'dangerous_attacks_last_5': {'min': 10},
                    'attacks_last_5': {'min': 15}
                },
                weight=2.0
            ),
            ReliablePattern(
                name="Shot Volume",
                description="High number of shots with good accuracy",
                conditions={
                    'shots_total_last_5': {'min': 4},
                    'shots_on_target_last_5': {'min': 2}
                },
                weight=1.5
            ),
            
            # Score Context Patterns
            ReliablePattern(
                name="Tight Game Push",
                description="Close score with attacking momentum",
                conditions={
                    'score_diff': {'min': -1, 'max': 1},  # Within 1 goal
                    'minute': {'min': 25},  # After initial settling period
                    'dangerous_attacks_last_5': {'min': 6},
                    'attacks_last_5': {'min': 10}
                },
                weight=3.0  # Highest weight - very reliable pattern
            ),
            ReliablePattern(
                name="Draw Breaking Attempt",
                description="Teams trying to break deadlock",
                conditions={
                    'score_diff': {'equals': 0},  # Drawn game
                    'minute': {'min': 60},  # Late enough to need winner
                    'dangerous_attacks_last_5': {'min': 5},
                    'shots_total_last_5': {'min': 2}
                },
                weight=2.8
            ),
            ReliablePattern(
                name="One Goal Chase",
                description="Team trying to equalize",
                conditions={
                    'score_diff': {'equals': -1},  # Down by 1
                    'minute': {'min': 50},
                    'attacks_last_5': {'min': 8},
                    'dangerous_attacks_last_5': {'min': 4}
                },
                weight=2.8
            ),
            ReliablePattern(
                name="Corner Cluster",
                description="Multiple corners in last 15 mins - likely to continue",
                conditions={
                    'corners_last_15': {'min': 3},  # 3+ corners in last 15
                    'attacks_last_5': {'min': 6}    # Still attacking
                },
                weight=2.7
            ),
            ReliablePattern(
                name="Home Dominance",
                description="Home team dominating but not far ahead",
                conditions={
                    'is_home': {'equals': True},
                    'score_diff': {'min': -1, 'max': 1},
                    'dangerous_attacks_last_5': {'min': 8},
                    'shot_accuracy_ratio': {'min': 0.3}
                },
                weight=2.3
            ),
            ReliablePattern(
                name="Early Momentum",
                description="Strong early game momentum",
                conditions={
                    'minute': {'min': 15, 'max': 35},
                    'dangerous_attacks_last_5': {'min': 7},
                    'attacks_last_5': {'min': 12}
                },
                weight=2.0
            )
        ]
        
        logger.info("✅ Initialized Reliable Corner System")
        logger.info(f"   Patterns loaded: {len(self.patterns)}")
    
    def calculate_momentum(self, current_stats: Dict, previous_stats: Dict, 
                         minutes_passed: float) -> Dict[str, TeamMomentum]:
        """
        Calculate momentum using only reliable stats
        """
        momentum = {'home': TeamMomentum(), 'away': TeamMomentum()}
        
        for team in ['home', 'away']:
            # Calculate differences
            attack_diff = current_stats['attacks'][team] - previous_stats['attacks'][team]
            danger_diff = current_stats['dangerous_attacks'][team] - previous_stats['dangerous_attacks'][team]
            shots_diff = current_stats['shots_total'][team] - previous_stats['shots_total'][team]
            shots_on_diff = current_stats['shots_on_target'][team] - previous_stats['shots_on_target'][team]
            
            if minutes_passed > 0:
                # 1. Attack Intensity (0-100)
                # Ratio of dangerous attacks to total attacks
                if attack_diff > 0:
                    attack_intensity = (danger_diff / attack_diff) * 100
                else:
                    attack_intensity = 0
                
                # 2. Shot Efficiency (0-100)
                # Ratio of shots on target
                if shots_diff > 0:
                    shot_efficiency = (shots_on_diff / shots_diff) * 100
                else:
                    shot_efficiency = 0
                
                # 3. Attack Volume (0-100)
                # Attacks per minute normalized
                attack_volume = min(100, (attack_diff / minutes_passed) * 20)
                
                # Calculate corner momentum (0-100)
                # Get corner metrics from diff_stats
                corners_per_min = (current_stats.get('total_corners', 0) - previous_stats.get('total_corners', 0)) / minutes_passed if minutes_passed > 0 else 0
                corner_eff = (current_stats.get('total_corners', 0) - previous_stats.get('total_corners', 0)) / max(1, attack_diff) if attack_diff > 0 else 0
                
                corner_momentum = min(100, (
                    corners_per_min * 150 +  # 0.67 corners/min = 100
                    corner_eff * 500     # 20% efficiency = 100
                ) / 2)
                
                # Store momentum values
                momentum[team].attack_intensity = attack_intensity
                momentum[team].shot_efficiency = shot_efficiency
                momentum[team].attack_volume = attack_volume
                momentum[team].corner_momentum = corner_momentum
                
                # Calculate score context momentum (0-100)
                score_context = 0.0
                
                # Get current score state
                score_diff_global = current_stats.get('score_diff', 0)
                # Team-relative score diff: positive if this team is leading
                score_diff = score_diff_global if team == 'home' else -score_diff_global
                is_home = (team == 'home')
                minute = current_stats.get('minute', 0)
                
                # 1. Tight Score Scenarios (highest weight)
                if abs(score_diff) <= 1:  # 0-0, 1-1, 1-0, 0-1 scenarios
                    # Early game (both teams fresh and attacking)
                    if 15 <= minute <= 35:
                        score_context += 35  # Strong boost early
                    
                    # Middle game (teams settled but still need goals)
                    elif 36 <= minute <= 65:
                        score_context += 30
                    
                    # Late game (urgent need for winner)
                    elif minute > 65:
                        score_context += 40  # Maximum boost late
                
                # 2. Specific Score States
                if score_diff == 0:  # Drawn game (0-0, 1-1, etc)
                    if minute > 65:
                        score_context += 15  # Extra boost for draws late
                
                elif score_diff == -1:  # Team losing by 1
                    if minute > 65:
                        score_context += 25  # Strong boost when chasing game
                    else:
                        score_context += 15  # Moderate boost earlier
                
                elif score_diff == 1:  # Team winning by 1
                    if minute > 75:
                        score_context += 15  # Moderate boost (opponent will push)
                
                # 3. Home Team Advantage in Tight Games
                if is_home and abs(score_diff) <= 1:
                    if minute > 65:
                        score_context += 20  # Strong home boost late
                    else:
                        score_context += 15  # Moderate home boost
                
                # 4. Corner Cluster Effect
                corners_last_15 = current_stats.get('corners_last_15', 0)
                if corners_last_15 >= 3:
                    # Higher boost in tight games
                    if abs(score_diff) <= 1:
                        score_context += 25
                    else:
                        score_context += 15
                
                # Cap at 100
                score_context = min(100, score_context)
                momentum[team].score_context = score_context
                
                # Overall momentum (weighted combination)
                momentum[team].overall_momentum = min(100, (
                    attack_intensity * 0.25 +    # 25% - Attack quality
                    shot_efficiency * 0.15 +     # 15% - Shot precision
                    attack_volume * 0.15 +       # 15% - Attack frequency
                    corner_momentum * 0.25 +     # 25% - Corner dynamics
                    score_context * 0.20         # 20% - Match context
                ))
        
        return momentum
    
    def calculate_stats_differences(self, current_stats: Dict, previous_stats: Dict,
                                  minutes: int) -> Dict[str, Dict[str, float]]:
        """Calculate stat differences and derived metrics"""
        diff_stats = {'home': {}, 'away': {}}
        
        for team in ['home', 'away']:
            # Basic stat differences
            attacks_diff = current_stats['attacks'][team] - previous_stats['attacks'][team]
            danger_diff = current_stats['dangerous_attacks'][team] - previous_stats['dangerous_attacks'][team]
            shots_diff = current_stats['shots_total'][team] - previous_stats['shots_total'][team]
            shots_on_diff = current_stats['shots_on_target'][team] - previous_stats['shots_on_target'][team]
            
            # Calculate corner-related metrics
            total_corners_current = current_stats.get('total_corners', 0)
            total_corners_prev = previous_stats.get('total_corners', 0)
            corners_per_minute = (total_corners_current - total_corners_prev) / minutes if minutes > 0 else 0
            
            # Calculate corner efficiency (corners per X attacks)
            corner_efficiency = (total_corners_current - total_corners_prev) / max(1, attacks_diff) if attacks_diff > 0 else 0
            
            # Store corner metrics
            diff_stats[team].update({
                'corners_per_minute': corners_per_minute,
                'corner_efficiency': corner_efficiency
            })
            
            # Store basic differences
            diff_stats[team].update({
                f'attacks_last_{minutes}': attacks_diff,
                f'dangerous_attacks_last_{minutes}': danger_diff,
                f'shots_total_last_{minutes}': shots_diff,
                f'shots_on_target_last_{minutes}': shots_on_diff
            })
            
            # Calculate derived metrics
            if attacks_diff > 0:
                diff_stats[team]['dangerous_attack_ratio'] = danger_diff / attacks_diff
            else:
                diff_stats[team]['dangerous_attack_ratio'] = 0
                
            if shots_diff > 0:
                diff_stats[team]['shot_accuracy_ratio'] = shots_on_diff / shots_diff
            else:
                diff_stats[team]['shot_accuracy_ratio'] = 0
        
        return diff_stats
    
    def detect_patterns(self, diff_stats: Dict) -> Dict[str, List[ReliablePattern]]:
        """Detect patterns using only reliable stats"""
        detected = {'home': [], 'away': []}
        
        for team in ['home', 'away']:
            for pattern in self.patterns:
                pattern_matched = True
                
                for stat_name, condition in pattern.conditions.items():
                    if stat_name in diff_stats[team]:
                        actual_value = diff_stats[team][stat_name]
                        
                        if 'min' in condition and actual_value < condition['min']:
                            pattern_matched = False
                            break
                            
                        if 'max' in condition and actual_value > condition['max']:
                            pattern_matched = False
                            break
                
                if pattern_matched:
                    detected[team].append(pattern)
        
        return detected
    
    def calculate_corner_probability(self, current_stats: Dict, previous_stats: Dict,
                                   minutes_passed: float) -> Dict[str, Dict[str, float]]:
        """Calculate corner probability using only reliable stats"""
        # Get momentum and differences
        momentum = self.calculate_momentum(current_stats, previous_stats, minutes_passed)
        diff_stats = self.calculate_stats_differences(current_stats, previous_stats, 5)  # 5-minute window
        patterns = self.detect_patterns(diff_stats)
        
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
                    'attack_intensity': momentum[team].attack_intensity,
                    'shot_efficiency': momentum[team].shot_efficiency,
                    'attack_volume': momentum[team].attack_volume,
                    'corner_momentum': momentum[team].corner_momentum,
                    'score_context': momentum[team].score_context,
                    'overall': momentum[team].overall_momentum
                },
                'detected_patterns': [
                    {'name': p.name, 'weight': p.weight}
                    for p in patterns[team]
                ]
            }
        
        return probabilities
    
    def should_alert(self, current_stats: Dict, previous_stats: Dict,
                    minutes_passed: float) -> Dict[str, Dict]:
        """
        Determine if corner alert should be triggered.
        Returns dict with alert decision and detailed reasoning.
        """
        
        result = {
            'home': {'alert': False, 'reasons': [], 'metrics': {}},
            'away': {'alert': False, 'reasons': [], 'metrics': {}},
            # Combined match-level decision (either team wins a corner)
            'combined': {'alert': False, 'reasons': [], 'probability': 0.0, 'best_team': 'home'}
        }
        
        # CRITICAL CHECKS (do not return early; we still want metrics)
        current_minute = current_stats.get('minute', 0)
        timing_ok = 85 <= current_minute <= 89
        if not timing_ok:
            logger.info(f"⏱️ TIMING CHECK FAILED: Minute {current_minute} outside 85-89 window")
        else:
            logger.info(f"✅ TIMING CHECK PASSED: Minute {current_minute}")

        odds_ok = current_stats.get('has_live_asian_corners', False)
        if not odds_ok:
            logger.info("❌ ODDS CHECK FAILED: No live Asian corner odds available")
        else:
            logger.info("✅ ODDS CHECK PASSED: Live Asian corners available")
        
        # Calculate probabilities and patterns
        probabilities = self.calculate_corner_probability(
            current_stats, previous_stats, minutes_passed
        )
        
        # Analyze each team
        for team in ['home', 'away']:
            prob = probabilities[team]
            momentum = prob.get('momentum_indicators', {})
            patterns = prob.get('detected_patterns', [])
            
            logger.info(f"\n📊 ANALYZING {team.upper()} TEAM:")
            
            # Store all metrics for reference
            metrics = {
                'total_probability': prob['total_probability'],
                'attack_intensity': momentum.get('attack_intensity', 0),
                'shot_efficiency': momentum.get('shot_efficiency', 0),
                'attack_volume': momentum.get('attack_volume', 0),
                'corner_momentum': momentum.get('corner_momentum', 0),
                'score_context': momentum.get('score_context', 0),
                'patterns_count': len(patterns),
                'strongest_pattern_weight': max([p['weight'] for p in patterns], default=0),
                'score_diff': abs(current_stats.get('score_diff', 0))
            }
            result[team]['metrics'] = metrics
            
            # Log current metrics
            logger.info(f"   • Total Probability: {metrics['total_probability']:.1f}%")
            logger.info(f"   • Attack Intensity: {metrics['attack_intensity']:.1f}")
            logger.info(f"   • Corner Momentum: {metrics['corner_momentum']:.1f}")
            logger.info(f"   • Patterns Found: {len(patterns)}")
            
            # Check each criterion
            checks = [
                (metrics['total_probability'] >= 80, 
                 "Total probability >= 80%",
                 f"Low probability: {metrics['total_probability']:.1f}%"),
                
                (metrics['attack_intensity'] >= 65,
                 "Strong attack intensity",
                 f"Weak attack intensity: {metrics['attack_intensity']:.1f}"),
                
                (len(patterns) >= 2,
                 "Multiple patterns detected",
                 f"Insufficient patterns: {len(patterns)}"),
                
                (any(p['weight'] >= 2.5 for p in patterns),
                 "Strong pattern present",
                 "No strong patterns found"),
                
                (metrics['corner_momentum'] >= 50,
                 "Good corner momentum",
                 f"Low corner momentum: {metrics['corner_momentum']:.1f}"),
                
                (metrics['score_diff'] <= 1,
                 "Tight game scenario",
                 f"Not a tight game: {metrics['score_diff']} goal difference")
            ]
            
            # Evaluate all checks
            all_passed = True
            for passed, success_msg, failure_msg in checks:
                if passed:
                    logger.info(f"   ✅ {success_msg}")
                    result[team]['reasons'].append(f"✓ {success_msg}")
                else:
                    logger.info(f"   ❌ {failure_msg}")
                    result[team]['reasons'].append(f"✗ {failure_msg}")
                    all_passed = False
            
            # Set final alert decision (only if timing and odds are OK)
            result[team]['alert'] = all_passed and timing_ok and odds_ok
            
            # Team strength guard (without the strict probability threshold)
            team_strong = (
                (metrics['attack_intensity'] >= 65) and
                (metrics['corner_momentum'] >= 50) and
                (len(patterns) >= 2) and
                any(p['weight'] >= 2.5 for p in patterns) and
                (metrics['score_diff'] <= 1)
            )
            result[team]['team_strong'] = team_strong
            
            if all_passed:
                logger.info(f"🎯 ALERT TRIGGERED for {team.upper()} team!")
                logger.info("   Detected Patterns:")
                for p in patterns:
                    logger.info(f"   • {p['name']} (Weight: {p['weight']})")
            else:
                logger.info(f"⏭️ NO ALERT for {team.upper()} team - criteria not met")
        
        # Compute combined match-level probability (either team wins a corner)
        home_prob = result['home']['metrics'].get('total_probability', 0.0)
        away_prob = result['away']['metrics'].get('total_probability', 0.0)
        combined_probability = 100.0 * (1.0 - (1.0 - home_prob / 100.0) * (1.0 - away_prob / 100.0))

        # Determine best team (higher standalone probability)
        best_team = 'home' if home_prob >= away_prob else 'away'

        # Combined decision: high combined probability AND at least one strong team
        combined_reasons = []
        if combined_probability >= 80.0:
            combined_reasons.append("Combined probability >= 80%")
        else:
            combined_reasons.append(f"Low combined probability: {combined_probability:.1f}%")

        if result['home'].get('team_strong') or result['away'].get('team_strong'):
            combined_reasons.append("At least one team is strong (momentum/patterns)")
            combined_guard = True
        else:
            combined_reasons.append("No strong team (momentum/patterns) detected")
            combined_guard = False

        result['combined'] = {
            'alert': (combined_probability >= 80.0) and combined_guard and timing_ok and odds_ok,
            'reasons': [f"✓ {r}" if r.startswith(('Combined probability', 'At least')) else f"✗ {r}" for r in combined_reasons],
            'probability': combined_probability,
            'best_team': best_team
        }

        return result