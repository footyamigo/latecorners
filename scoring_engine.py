import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

from sportmonks_client import MatchStats
from config import SCORING_MATRIX, TIME_MULTIPLIERS, get_config

@dataclass
class ScoringResult:
    """Container for scoring result"""
    fixture_id: int
    total_score: float
    minute: int
    triggered_conditions: List[str]
    team_focus: str  # 'home' or 'away' - which team is most likely to get corners
    match_context: str
    
class MatchStateTracker:
    """Tracks match state changes to calculate 'last X minutes' stats"""
    
    def __init__(self):
        self.match_states = {}  # fixture_id -> list of (timestamp, MatchStats)
        self.logger = logging.getLogger(__name__)
    
    def update_match_state(self, stats: MatchStats):
        """Update the tracked state for a match"""
        fixture_id = stats.fixture_id
        timestamp = datetime.now()
        
        if fixture_id not in self.match_states:
            self.match_states[fixture_id] = []
        
        self.match_states[fixture_id].append((timestamp, stats))
        
        # Keep only last 30 minutes of data to manage memory
        cutoff_time = timestamp - timedelta(minutes=30)
        self.match_states[fixture_id] = [
            (ts, st) for ts, st in self.match_states[fixture_id] 
            if ts > cutoff_time
        ]
    
    def get_stats_from_minutes_ago(self, fixture_id: int, minutes_ago: int) -> Optional[MatchStats]:
        """Get match stats from X minutes ago"""
        if fixture_id not in self.match_states:
            return None
        
        target_time = datetime.now() - timedelta(minutes=minutes_ago)
        states = self.match_states[fixture_id]
        
        # Find the closest state to our target time
        closest_state = None
        min_diff = timedelta.max
        
        for timestamp, stats in states:
            diff = abs(timestamp - target_time)
            if diff < min_diff:
                min_diff = diff
                closest_state = stats
        
        return closest_state

class ScoringEngine:
    """Main scoring engine that evaluates match conditions"""
    
    def __init__(self):
        self.config = get_config()
        self.state_tracker = MatchStateTracker()
        self.logger = logging.getLogger(__name__)
        
        # Cache for pre-match favorites
        self.favorites_cache = {}  # fixture_id -> team_id
    
    def set_favorite(self, fixture_id: int, favorite_team_id: int):
        """Set the pre-match favorite for a fixture"""
        self.favorites_cache[fixture_id] = favorite_team_id
    
    def evaluate_match(self, current_stats: MatchStats) -> Optional[ScoringResult]:
        """Main evaluation method - returns scoring result if conditions are met"""
        
        # Update state tracking
        self.state_tracker.update_match_state(current_stats)
        
        # Only evaluate matches at 85+ minutes
        if current_stats.minute < self.config.MIN_MINUTE_FOR_ALERT:
            return None
        
        # Calculate all scoring conditions
        triggered_conditions = []
        total_score = 0.0
        team_focus = self._determine_team_focus(current_stats)
        
        # HIGH PRIORITY INDICATORS (3-5 points)
        score, conditions = self._evaluate_high_priority_conditions(current_stats, team_focus)
        total_score += score
        triggered_conditions.extend(conditions)
        
        # MEDIUM PRIORITY INDICATORS (2-3 points)
        score, conditions = self._evaluate_medium_priority_conditions(current_stats, team_focus)
        total_score += score
        triggered_conditions.extend(conditions)
        
        # TACTICAL INDICATORS (1-2 points)
        score, conditions = self._evaluate_tactical_conditions(current_stats, team_focus)
        total_score += score
        triggered_conditions.extend(conditions)
        
        # CORNER COUNT CONTEXT
        score, conditions = self._evaluate_corner_context(current_stats)
        total_score += score
        triggered_conditions.extend(conditions)
        
        # NEGATIVE INDICATORS
        score, conditions = self._evaluate_negative_conditions(current_stats)
        total_score += score
        triggered_conditions.extend(conditions)
        
        # Apply time multiplier
        time_multiplier = self._get_time_multiplier(current_stats.minute)
        total_score *= time_multiplier
        
        self.logger.info(
            f"Fixture {current_stats.fixture_id} at {current_stats.minute}': "
            f"Score = {total_score:.1f} (threshold: {self.config.ALERT_THRESHOLD})"
        )
        
        # Check if alert threshold is met
        if total_score >= self.config.ALERT_THRESHOLD:
            return ScoringResult(
                fixture_id=current_stats.fixture_id,
                total_score=total_score,
                minute=current_stats.minute,
                triggered_conditions=triggered_conditions,
                team_focus=team_focus,
                match_context=self._generate_match_context(current_stats, triggered_conditions)
            )
        
        return None
    
    def _determine_team_focus(self, stats: MatchStats) -> str:
        """Determine which team is most likely to generate corners"""
        
        # Check if we know the pre-match favorite
        favorite_team_id = self.favorites_cache.get(stats.fixture_id)
        
        # Simple logic: focus on team that's behind or drawing (if favorite)
        if stats.home_score > stats.away_score:
            return 'away'  # Away team trailing, likely to attack
        elif stats.away_score > stats.home_score:
            return 'home'  # Home team trailing, likely to attack
        else:
            # It's a draw - focus on favorite or home team
            if favorite_team_id == stats.home_team_id:
                return 'home'
            elif favorite_team_id == stats.away_team_id:
                return 'away'
            else:
                return 'home'  # Default to home team
    
    def _evaluate_high_priority_conditions(self, stats: MatchStats, team_focus: str) -> Tuple[float, List[str]]:
        """Evaluate high priority scoring conditions (3-5 points)"""
        score = 0.0
        conditions = []
        
        # Favorite losing/drawing after 80 minutes
        favorite_team_id = self.favorites_cache.get(stats.fixture_id)
        if favorite_team_id:
            if ((favorite_team_id == stats.home_team_id and stats.home_score <= stats.away_score) or
                (favorite_team_id == stats.away_team_id and stats.away_score <= stats.home_score)):
                score += SCORING_MATRIX['favorite_losing_drawing_80plus']
                conditions.append('Favorite losing/drawing after 80\'')
        
        # Shots on target in last 15 minutes (5+)
        shots_last_15 = self._get_last_minutes_stat(stats, 'shots_on_target', 15, team_focus)
        if shots_last_15 >= 5:
            score += SCORING_MATRIX['shots_on_target_last_15min_5plus']
            conditions.append(f'{shots_last_15} shots on target in last 15min')
        
        # Dangerous attacks in last 10 minutes (6+)
        attacks_last_10 = self._get_last_minutes_stat(stats, 'dangerous_attacks', 10, team_focus)
        if attacks_last_10 >= 6:
            score += SCORING_MATRIX['dangerous_attacks_last_10min_6plus']
            conditions.append(f'{attacks_last_10} dangerous attacks in last 10min')
        
        # Shots blocked in last 10 minutes (4+)
        blocked_last_10 = self._get_last_minutes_stat(stats, 'shots_blocked', 10, team_focus)
        if blocked_last_10 >= 4:
            score += SCORING_MATRIX['shots_blocked_last_10min_4plus']
            conditions.append(f'{blocked_last_10} shots blocked in last 10min')
        
        # Big chances created in last 15 minutes (3+)
        big_chances_last_15 = self._get_last_minutes_stat(stats, 'big_chances_created', 15, team_focus)
        if big_chances_last_15 >= 3:
            score += SCORING_MATRIX['big_chances_created_last_15min_3plus']
            conditions.append(f'{big_chances_last_15} big chances created in last 15min')
        
        # Team trailing by 1 goal after 75 minutes
        if stats.minute >= 75:
            goal_diff = abs(stats.home_score - stats.away_score)
            if goal_diff == 1:
                score += SCORING_MATRIX['team_trailing_by_1_after_75min']
                conditions.append('Team trailing by 1 goal after 75\'')
        
        return score, conditions
    
    def _evaluate_medium_priority_conditions(self, stats: MatchStats, team_focus: str) -> Tuple[float, List[str]]:
        """Evaluate medium priority scoring conditions (2-3 points)"""
        score = 0.0
        conditions = []
        
        # Shots in second half (10+)
        if team_focus == 'home':
            second_half_shots = stats.shots_total['home']  # This is total, we'd need first half data to be precise
        else:
            second_half_shots = stats.shots_total['away']
        
        if second_half_shots >= 10:
            score += SCORING_MATRIX['shots_total_second_half_10plus']
            conditions.append(f'{second_half_shots} shots in second half')
        
        # Shots on target 8+ but less than 2 goals
        team_shots_on_target = stats.shots_on_target[team_focus]
        team_goals = stats.home_score if team_focus == 'home' else stats.away_score
        
        if team_shots_on_target >= 8 and team_goals < 2:
            score += SCORING_MATRIX['shots_on_target_8plus_but_less_than_2_goals']
            conditions.append(f'{team_shots_on_target} shots on target but only {team_goals} goals')
        
        # Possession in last 15 minutes (65%+)
        current_possession = stats.possession[team_focus]
        if current_possession >= 65:
            score += SCORING_MATRIX['possession_last_15min_65plus']
            conditions.append(f'{current_possession}% possession')
        
        # Shots inside box in last 20 minutes (5+)
        shots_inside_last_20 = self._get_last_minutes_stat(stats, 'shots_inside_box', 20, team_focus)
        if shots_inside_last_20 >= 5:
            score += SCORING_MATRIX['shots_inside_box_last_20min_5plus']
            conditions.append(f'{shots_inside_last_20} shots inside box in last 20min')
        
        # Hit woodwork 3+ times
        woodwork_hits = stats.hit_woodwork[team_focus]
        if woodwork_hits >= 3:
            score += SCORING_MATRIX['hit_woodwork_3plus']
            conditions.append(f'{woodwork_hits} times hit woodwork')
        
        # Crosses in last 15 minutes (8+)
        crosses_last_15 = self._get_last_minutes_stat(stats, 'crosses_total', 15, team_focus)
        if crosses_last_15 >= 8:
            score += SCORING_MATRIX['crosses_last_15min_8plus']
            conditions.append(f'{crosses_last_15} crosses in last 15min')
        
        # Key passes in last 10 minutes (4+)
        key_passes_last_10 = self._get_last_minutes_stat(stats, 'key_passes', 10, team_focus)
        if key_passes_last_10 >= 4:
            score += SCORING_MATRIX['key_passes_last_10min_4plus']
            conditions.append(f'{key_passes_last_10} key passes in last 10min')
        
        # Counter attacks in last 15 minutes (2+)
        counter_attacks_last_15 = self._get_last_minutes_stat(stats, 'counter_attacks', 15, team_focus)
        if counter_attacks_last_15 >= 2:
            score += SCORING_MATRIX['counter_attacks_last_15min_2plus']
            conditions.append(f'{counter_attacks_last_15} counter attacks in last 15min')
        
        return score, conditions
    
    def _evaluate_tactical_conditions(self, stats: MatchStats, team_focus: str) -> Tuple[float, List[str]]:
        """Evaluate tactical scoring conditions (1-2 points)"""
        score = 0.0
        conditions = []
        
        # Attacking substitution after 70 minutes
        attacking_subs = [sub for sub in stats.substitutions if sub.get('minute', 0) > 70]
        if attacking_subs:
            score += SCORING_MATRIX['attacking_sub_after_70min']
            conditions.append(f'{len(attacking_subs)} attacking subs after 70\'')
        
        # Fouls drawn (15+)
        fouls_drawn = stats.fouls_drawn[team_focus]
        if fouls_drawn >= 15:
            score += SCORING_MATRIX['fouls_drawn_15plus']
            conditions.append(f'{fouls_drawn} fouls drawn')
        
        # Successful dribbles in last 20 minutes (5+)
        dribbles_last_20 = self._get_last_minutes_stat(stats, 'successful_dribbles', 20, team_focus)
        if dribbles_last_20 >= 5:
            score += SCORING_MATRIX['successful_dribbles_last_20min_5plus']
            conditions.append(f'{dribbles_last_20} successful dribbles in last 20min')
        
        # Offsides in last 15 minutes (3+)
        offsides_last_15 = self._get_last_minutes_stat(stats, 'offsides', 15, team_focus)
        if offsides_last_15 >= 3:
            score += SCORING_MATRIX['offsides_last_15min_3plus']
            conditions.append(f'{offsides_last_15} offsides in last 15min')
        
        # Throwins in last 20 minutes (8+)
        throwins_last_20 = self._get_last_minutes_stat(stats, 'throwins', 20, team_focus)
        if throwins_last_20 >= 8:
            score += SCORING_MATRIX['throwins_last_20min_8plus']
            conditions.append(f'{throwins_last_20} throwins in last 20min')
        
        # Low pass accuracy (<75%)
        pass_accuracy = stats.successful_passes_percentage[team_focus]
        if pass_accuracy < 75:
            score += SCORING_MATRIX['low_pass_accuracy_under_75percent']
            conditions.append(f'{pass_accuracy}% pass accuracy (rushed play)')
        
        return score, conditions
    
    def _evaluate_corner_context(self, stats: MatchStats) -> Tuple[float, List[str]]:
        """Evaluate corner count context at 85th minute"""
        score = 0.0
        conditions = []
        
        total_corners = stats.total_corners
        
        if self.config.CORNER_SWEET_SPOT_MIN <= total_corners <= self.config.CORNER_SWEET_SPOT_MAX:
            score += SCORING_MATRIX['corners_8_to_11_sweet_spot']
            conditions.append(f'{total_corners} corners (SWEET SPOT)')
        elif 6 <= total_corners <= 7:
            score += SCORING_MATRIX['corners_6_to_7_positive']
            conditions.append(f'{total_corners} corners (positive)')
        elif 12 <= total_corners <= 14:
            score += SCORING_MATRIX['corners_12_to_14_high_action']
            conditions.append(f'{total_corners} corners (high action)')
        elif total_corners <= 5:
            score += SCORING_MATRIX['corners_5_or_less_red_flag']
            conditions.append(f'{total_corners} corners (RED FLAG - too low)')
        elif total_corners >= 15:
            score += SCORING_MATRIX['corners_15plus_oversaturated']
            conditions.append(f'{total_corners} corners (oversaturated)')
        
        return score, conditions
    
    def _evaluate_negative_conditions(self, stats: MatchStats) -> Tuple[float, List[str]]:
        """Evaluate negative scoring conditions"""
        score = 0.0
        conditions = []
        
        # Red card issued
        if stats.red_cards:
            score += SCORING_MATRIX['red_card_issued']
            conditions.append(f'{len(stats.red_cards)} red card(s) issued')
        
        # Leading by 3+ goals
        goal_diff = abs(stats.home_score - stats.away_score)
        if goal_diff >= 3:
            score += SCORING_MATRIX['leading_by_3plus_goals']
            conditions.append(f'Leading by {goal_diff} goals (game over)')
        
        # Possession under 30%
        home_possession = stats.possession['home']
        away_possession = stats.possession['away']
        
        if home_possession < 30 or away_possession < 30:
            score += SCORING_MATRIX['possession_under_30percent']
            conditions.append('Team has <30% possession (no control)')
        
        # Goalkeeper making 8+ saves (shots from distance)
        home_saves = stats.saves['home']
        away_saves = stats.saves['away']
        
        if home_saves >= 8 or away_saves >= 8:
            score += SCORING_MATRIX['gk_making_8plus_saves']
            conditions.append(f'GK making {max(home_saves, away_saves)} saves (distant shots)')
        
        return score, conditions
    
    def _get_last_minutes_stat(self, current_stats: MatchStats, stat_name: str, minutes: int, team_focus: str) -> int:
        """Calculate stat difference for last X minutes"""
        
        # Get stats from X minutes ago
        old_stats = self.state_tracker.get_stats_from_minutes_ago(
            current_stats.fixture_id, minutes
        )
        
        if not old_stats:
            # If we don't have old data, return current value (conservative estimate)
            current_value = getattr(current_stats, stat_name, {}).get(team_focus, 0)
            return current_value
        
        # Calculate difference
        current_value = getattr(current_stats, stat_name, {}).get(team_focus, 0)
        old_value = getattr(old_stats, stat_name, {}).get(team_focus, 0)
        
        return max(0, current_value - old_value)
    
    def _get_time_multiplier(self, minute: int) -> float:
        """Get time-based multiplier"""
        if 90 <= minute:
            return TIME_MULTIPLIERS['90plus_minutes']
        elif 80 <= minute < 90:
            return TIME_MULTIPLIERS['80_to_90_minutes']
        else:
            return TIME_MULTIPLIERS['70_to_80_minutes']
    
    def _generate_match_context(self, stats: MatchStats, conditions: List[str]) -> str:
        """Generate human-readable match context"""
        score_context = f"{stats.home_score}-{stats.away_score}"
        minute_context = f"{stats.minute}'"
        
        # Top 3 most important conditions
        top_conditions = conditions[:3]
        conditions_text = "; ".join(top_conditions)
        
        return f"{score_context} at {minute_context} | {conditions_text}" 