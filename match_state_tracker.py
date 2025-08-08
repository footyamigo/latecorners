#!/usr/bin/env python3
"""
Track live match statistics with time windows
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class TimeWindowStats:
    """Stats for a specific time window"""
    window_start: datetime
    window_end: datetime
    shots_on_target: Dict[str, int] = None
    shots_off_target: Dict[str, int] = None
    shots_total: Dict[str, int] = None
    dangerous_attacks: Dict[str, int] = None
    attacks: Dict[str, int] = None
    possession: Dict[str, int] = None
    corners: Dict[str, int] = None
    
    def __post_init__(self):
        # Initialize all stat dictionaries
        for field in ['shots_on_target', 'shots_off_target', 'shots_total', 
                     'dangerous_attacks', 'attacks', 'possession', 'corners']:
            if getattr(self, field) is None:
                setattr(self, field, {'home': 0, 'away': 0})

class MatchStateTracker:
    """Track match state and statistics over time"""
    
    def __init__(self, fixture_id: int, window_sizes: List[int] = None):
        """
        Initialize match state tracker
        
        Args:
            fixture_id: Match ID
            window_sizes: List of window sizes in minutes to track (default: [5, 10, 15])
        """
        self.fixture_id = fixture_id
        self.window_sizes = window_sizes or [5, 10, 15]  # Default windows: 5, 10, 15 minutes
        self.stats_history: List[TimeWindowStats] = []
        self.last_update = None
        
        # SportMonks stat type mapping
        self.stat_type_mapping = {
            33: 'corners',            # Corners
            34: 'possession',         # Possession
            41: 'shots_off_target',   # Shots off target
            42: 'shots_total',        # Total shots
            44: 'dangerous_attacks',  # Dangerous attacks
            45: 'attacks',            # Attacks
            86: 'shots_on_target',    # Shots on target
        }
        
        logger.info(f"🎯 Initialized MatchStateTracker for fixture {fixture_id}")
        logger.info(f"   Window sizes: {self.window_sizes} minutes")
    
    def update_stats(self, current_stats: Dict[str, Dict[str, int]], timestamp: datetime = None) -> None:
        """
        Update match statistics
        
        Args:
            current_stats: Current match statistics
            timestamp: Timestamp for the stats (default: current time)
        """
        if timestamp is None:
            timestamp = datetime.now()
            
        # Create new time window stats
        window_stats = TimeWindowStats(
            window_start=timestamp,
            window_end=timestamp
        )
        
        # Update stats from current values
        for stat_name in ['shots_on_target', 'shots_off_target', 'shots_total',
                         'dangerous_attacks', 'attacks', 'possession', 'corners']:
            if stat_name in current_stats:
                setattr(window_stats, stat_name, current_stats[stat_name])
        
        # Add to history
        self.stats_history.append(window_stats)
        self.last_update = timestamp
        
        # Clean old history (keep last 20 minutes)
        cutoff_time = timestamp - timedelta(minutes=20)
        self.stats_history = [
            stats for stats in self.stats_history 
            if stats.window_start > cutoff_time
        ]
        
        logger.debug(f"📊 Updated stats for fixture {self.fixture_id}")
        logger.debug(f"   History size: {len(self.stats_history)} entries")
    
    def get_window_stats(self, minutes: int, current_time: datetime = None) -> Optional[Dict[str, Dict[str, int]]]:
        """
        Get statistics for the last X minutes
        
        Args:
            minutes: Number of minutes to look back
            current_time: Current timestamp (default: now)
            
        Returns:
            Dict with stats for the time window, or None if not enough history
        """
        if not self.stats_history:
            return None
            
        if current_time is None:
            current_time = datetime.now()
            
        window_start = current_time - timedelta(minutes=minutes)
        
        # Get stats entries in the window
        window_entries = [
            stats for stats in self.stats_history 
            if stats.window_start >= window_start
        ]
        
        if not window_entries:
            return None
            
        # Get the first and last entries
        first_stats = window_entries[0]
        last_stats = window_entries[-1]
        
        # Calculate differences for each stat
        window_stats = {}
        for stat_name in ['shots_on_target', 'shots_off_target', 'shots_total',
                         'dangerous_attacks', 'attacks', 'corners']:
            first_values = getattr(first_stats, stat_name)
            last_values = getattr(last_stats, stat_name)
            
            window_stats[stat_name] = {
                'home': last_values['home'] - first_values['home'],
                'away': last_values['away'] - first_values['away']
            }
            
        # For possession, take the average
        possession_values = [
            getattr(stats, 'possession') for stats in window_entries
        ]
        if possession_values:
            window_stats['possession'] = {
                'home': sum(p['home'] for p in possession_values) / len(possession_values),
                'away': sum(p['away'] for p in possession_values) / len(possession_values)
            }
        
        return window_stats
    
    def get_all_windows_stats(self, current_time: datetime = None) -> Dict[int, Dict[str, Dict[str, int]]]:
        """
        Get statistics for all configured time windows
        
        Args:
            current_time: Current timestamp (default: now)
            
        Returns:
            Dict mapping window size to stats
        """
        all_stats = {}
        for window_size in self.window_sizes:
            stats = self.get_window_stats(window_size, current_time)
            if stats:
                all_stats[window_size] = stats
        return all_stats
    
    def parse_sportmonks_stats(self, live_stats: List[Dict]) -> Dict[str, Dict[str, int]]:
        """
        Parse SportMonks live statistics format into our format
        
        Args:
            live_stats: List of SportMonks live statistics
            
        Returns:
            Dict with parsed statistics
        """
        parsed_stats = {
            'shots_on_target': {'home': 0, 'away': 0},
            'shots_off_target': {'home': 0, 'away': 0},
            'shots_total': {'home': 0, 'away': 0},
            'dangerous_attacks': {'home': 0, 'away': 0},
            'attacks': {'home': 0, 'away': 0},
            'possession': {'home': 0, 'away': 0},
            'corners': {'home': 0, 'away': 0}
        }
        
        for stat in live_stats:
            type_id = stat.get('type_id')
            value = stat.get('data', {}).get('value', 0)
            location = stat.get('location', '').lower()
            
            if type_id in self.stat_type_mapping and location in ['home', 'away']:
                stat_name = self.stat_type_mapping[type_id]
                parsed_stats[stat_name][location] = value
        
        return parsed_stats