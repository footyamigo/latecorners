#!/usr/bin/env python3
"""
Enhanced match state tracker with comprehensive stats and derived metrics
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class EnhancedTimeWindowStats:
    """Enhanced stats tracking for a specific time window"""
    window_start: datetime
    window_end: datetime
    
    # Basic stats (raw numbers)
    shots_on_target: Dict[str, int] = None
    shots_off_target: Dict[str, int] = None
    shots_total: Dict[str, int] = None
    shots_blocked: Dict[str, int] = None
    shots_inside_box: Dict[str, int] = None
    shots_outside_box: Dict[str, int] = None
    
    # Attack indicators
    dangerous_attacks: Dict[str, int] = None
    attacks: Dict[str, int] = None
    counter_attacks: Dict[str, int] = None
    big_chances_created: Dict[str, int] = None
    big_chances_missed: Dict[str, int] = None
    
    # Possession and control
    possession: Dict[str, int] = None
    crosses_total: Dict[str, int] = None
    key_passes: Dict[str, int] = None
    successful_dribbles: Dict[str, int] = None
    
    # Set pieces and pressure
    corners: Dict[str, int] = None
    free_kicks: Dict[str, int] = None
    throwins: Dict[str, int] = None
    
    # Additional stats
    passes: Dict[str, int] = None
    pass_accuracy: Dict[str, int] = None
    
    def __post_init__(self):
        """Initialize all stat dictionaries"""
        for field in [
            'shots_on_target', 'shots_off_target', 'shots_total',
            'shots_blocked', 'shots_inside_box', 'shots_outside_box',
            'dangerous_attacks', 'attacks', 'counter_attacks',
            'big_chances_created', 'big_chances_missed',
            'possession', 'crosses_total', 'key_passes',
            'successful_dribbles', 'corners', 'free_kicks',
            'throwins', 'passes', 'pass_accuracy'
        ]:
            if getattr(self, field) is None:
                setattr(self, field, {'home': 0, 'away': 0})

class EnhancedMatchTracker:
    """Enhanced match state tracker with derived metrics"""
    
    def __init__(self, fixture_id: int, window_sizes: List[int] = None):
        """
        Initialize enhanced match tracker
        
        Args:
            fixture_id: Match ID
            window_sizes: List of window sizes in minutes (default: [5, 10, 15])
        """
        self.fixture_id = fixture_id
        self.window_sizes = window_sizes or [5, 10, 15]
        self.stats_history: List[EnhancedTimeWindowStats] = []
        self.last_update = None
        
        # SportMonks stat type mapping
        self.stat_type_mapping = {
            33: 'corners',            # Corners
            34: 'possession',         # Possession
            41: 'shots_off_target',   # Shots off target
            42: 'shots_total',        # Total shots
            44: 'dangerous_attacks',  # Dangerous attacks
            45: 'attacks',            # Attacks
            49: 'shots_inside_box',   # Shots inside box
            50: 'shots_outside_box',  # Shots outside box
            55: 'free_kicks',         # Free kicks
            58: 'shots_blocked',      # Blocked shots
            60: 'throwins',           # Throw-ins
            80: 'passes',             # Total passes
            82: 'pass_accuracy',      # Pass accuracy
            86: 'shots_on_target',    # Shots on target
            98: 'crosses_total',      # Total crosses
            109: 'successful_dribbles', # Successful dribbles
            117: 'key_passes',        # Key passes
            580: 'big_chances_created', # Big chances created
            581: 'big_chances_missed'   # Big chances missed
        }
        
        logger.info(f"🎯 Initialized EnhancedMatchTracker for fixture {fixture_id}")
        logger.info(f"   Window sizes: {self.window_sizes} minutes")
    
    def update_stats(self, current_stats: Dict[str, Dict[str, int]], timestamp: datetime = None) -> None:
        """Update match statistics"""
        if timestamp is None:
            timestamp = datetime.now()
            
        # Create new time window stats
        window_stats = EnhancedTimeWindowStats(
            window_start=timestamp,
            window_end=timestamp
        )
        
        # Update all available stats
        for field in window_stats.__dataclass_fields__:
            if field not in ['window_start', 'window_end'] and field in current_stats:
                setattr(window_stats, field, current_stats[field])
        
        # Add to history
        self.stats_history.append(window_stats)
        self.last_update = timestamp
        
        # Clean old history (keep last 20 minutes)
        cutoff_time = timestamp - timedelta(minutes=20)
        self.stats_history = [
            stats for stats in self.stats_history 
            if stats.window_start > cutoff_time
        ]
    
    def get_window_stats(self, minutes: int, current_time: datetime = None) -> Optional[Dict]:
        """Get comprehensive stats for the last X minutes"""
        if not self.stats_history:
            return None
            
        if current_time is None:
            current_time = datetime.now()
            
        window_start = current_time - timedelta(minutes=minutes)
        window_entries = [
            stats for stats in self.stats_history 
            if stats.window_start >= window_start
        ]
        
        if not window_entries:
            return None
            
        # Get first and last entries
        first_stats = window_entries[0]
        last_stats = window_entries[-1]
        
        # Calculate basic stats differences
        window_stats = {}
        for field in first_stats.__dataclass_fields__:
            if field not in ['window_start', 'window_end', 'possession', 'pass_accuracy']:
                first_values = getattr(first_stats, field)
                last_values = getattr(last_stats, field)
                
                window_stats[field] = {
                    'home': last_values['home'] - first_values['home'],
                    'away': last_values['away'] - first_values['away']
                }
        
        # Calculate averages for percentage-based stats
        for field in ['possession', 'pass_accuracy']:
            values = [getattr(stats, field) for stats in window_entries]
            if values:
                window_stats[field] = {
                    'home': sum(v['home'] for v in values) / len(values),
                    'away': sum(v['away'] for v in values) / len(values)
                }
        
        # Add derived metrics
        window_stats.update(self._calculate_derived_metrics(window_stats))
        
        return window_stats
    
    def _calculate_derived_metrics(self, stats: Dict) -> Dict[str, Dict[str, float]]:
        """Calculate derived metrics from raw stats"""
        derived = {}
        
        for team in ['home', 'away']:
            # Attack effectiveness
            total_attacks = stats['attacks'][team]
            dangerous_ratio = (stats['dangerous_attacks'][team] / total_attacks * 100) if total_attacks > 0 else 0
            
            # Shot quality
            total_shots = stats['shots_total'][team]
            shots_on_target_ratio = (stats['shots_on_target'][team] / total_shots * 100) if total_shots > 0 else 0
            shots_inside_ratio = (stats['shots_inside_box'][team] / total_shots * 100) if total_shots > 0 else 0
            
            # Pressure metrics
            crosses_per_attack = (stats['crosses_total'][team] / total_attacks) if total_attacks > 0 else 0
            set_pieces = stats['corners'][team] + stats['free_kicks'][team]
            
            # Store derived metrics
            for metric, value in {
                'dangerous_attack_ratio': dangerous_ratio,
                'shots_on_target_ratio': shots_on_target_ratio,
                'shots_inside_box_ratio': shots_inside_ratio,
                'crosses_per_attack': crosses_per_attack,
                'set_pieces_total': set_pieces
            }.items():
                if metric not in derived:
                    derived[metric] = {}
                derived[metric][team] = value
        
        return derived
    
    def get_attack_momentum(self, minutes: int = 5) -> Dict[str, float]:
        """
        Calculate attack momentum score (0-100) for each team
        Based on recent dangerous attacks, shots, and possession
        """
        stats = self.get_window_stats(minutes)
        if not stats:
            return {'home': 0, 'away': 0}
            
        momentum = {}
        for team in ['home', 'away']:
            # Weight different factors
            dangerous_attacks_weight = stats['dangerous_attacks'][team] * 2
            shots_weight = (stats['shots_on_target'][team] * 3 + 
                          stats['shots_inside_box'][team] * 2)
            possession_weight = stats['possession'][team] * 0.5
            
            # Calculate momentum score (0-100)
            momentum[team] = min(100, (
                dangerous_attacks_weight +
                shots_weight +
                possession_weight
            ))
            
        return momentum
    
    def get_corner_probability_factors(self, minutes: int = 5) -> Dict[str, Dict[str, float]]:
        """
        Calculate factors that influence corner probability
        Returns dict with various probability factors (0-100)
        """
        stats = self.get_window_stats(minutes)
        if not stats:
            return {}
            
        factors = {}
        for team in ['home', 'away']:
            # Attack pressure
            attack_pressure = min(100, (
                stats['dangerous_attacks'][team] * 10 +
                stats['crosses_total'][team] * 15 +
                stats['shots_blocked'][team] * 20
            ) / minutes)
            
            # Territory control
            territory = min(100, (
                stats['possession'][team] * 0.5 +
                stats['successful_dribbles'][team] * 10 +
                stats['passes'][team] * 0.1
            ))
            
            # Set piece threat
            set_piece_threat = min(100, (
                stats['corners'][team] * 15 +
                stats['free_kicks'][team] * 10
            ))
            
            factors[team] = {
                'attack_pressure': attack_pressure,
                'territory_control': territory,
                'set_piece_threat': set_piece_threat,
                'overall_corner_probability': (
                    attack_pressure * 0.5 +
                    territory * 0.3 +
                    set_piece_threat * 0.2
                )
            }
            
        return factors