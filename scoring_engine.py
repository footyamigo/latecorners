import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

from sportmonks_client import MatchStats
from config import SCORING_MATRIX, get_config

@dataclass
class ScoringResult:
    """Container for scoring result"""
    fixture_id: int
    total_score: float
    minute: int
    triggered_conditions: List[str]
    high_priority_indicators: int  # Count of high-priority indicators met
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
        
        # Precise 85th minute timing - only evaluate in the exact window
        if not self._is_in_alert_window(current_stats.minute):
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
        
        # Count high-priority indicators
        high_priority_count = self._count_high_priority_indicators(triggered_conditions)
        self.logger.info(f"🧪 SCORING: fixture_id={current_stats.fixture_id}, total_score={total_score}, high_priority_count={high_priority_count}, triggered={triggered_conditions}")
        
        # FLEXIBLE CORNER FILTER: Support different tiers
        total_corners = current_stats.total_corners
        
        # ELITE tier: 7-12 corners (ultra-selective, ONLY tier used)
        elite_corner_ok = 7 <= total_corners <= 12
        
        # Check ELITE qualification only
        elite_qualified = total_score >= 8.0 and high_priority_count >= 2 and elite_corner_ok
        
        if elite_qualified:
            self.logger.info(f"🏆 ELITE QUALIFIED: Match {current_stats.fixture_id} - Score: {total_score}/8.0, High Priority: {high_priority_count}/2, Corners: {total_corners}")
            
            return ScoringResult(
                fixture_id=current_stats.fixture_id,
                total_score=total_score,
                minute=current_stats.minute,
                triggered_conditions=triggered_conditions,
                high_priority_indicators=high_priority_count,
                team_focus=team_focus,
                match_context=self._generate_match_context(current_stats, triggered_conditions)
            )
        else:
            # Log why it didn't qualify for ELITE tier
            if total_corners < 7:
                self.logger.info(f"🚫 CORNER FILTER: Match {current_stats.fixture_id} rejected - {total_corners} corners (need 7+ for ELITE)")
            elif total_corners > 12:
                self.logger.info(f"🚫 CORNER FILTER: Match {current_stats.fixture_id} rejected - {total_corners} corners (max 12 for ELITE)")
            else:
                self.logger.info(f"🚫 SCORE FILTER: Match {current_stats.fixture_id} rejected - Score: {total_score} (need 8+ for ELITE), High Priority: {high_priority_count}")
        
        return None
    
    def _determine_team_focus(self, stats: MatchStats) -> str:
        """Determine which team is most likely to generate corners"""
        
        # Simple logic: focus on team that's behind, or home team if drawing
        if stats.home_score > stats.away_score:
            return 'away'  # Away team trailing, likely to attack
        elif stats.away_score > stats.home_score:
            return 'home'  # Home team trailing, likely to attack
        else:
            # It's a draw - default to home team (slight home advantage)
            return 'home'
    
    def _evaluate_high_priority_conditions(self, stats: MatchStats, team_focus: str) -> Tuple[float, List[str]]:
        """Evaluate high priority scoring conditions (3-5 points)"""
        score = 0.0
        conditions = []
        
        # Note: Favorite team logic temporarily disabled due to team ID/name mapping issues
        # Will be re-enabled when we have reliable team ID mapping from MatchStats
        
        # Game state analysis (HIGH PRIORITY conditions)
        goal_diff = abs(stats.home_score - stats.away_score)
        
        # Trailing by exactly 1 goal (PRIME corner scenario)
        if goal_diff == 1:
            score += SCORING_MATRIX['team_trailing_by_1_after_75min']
            trailing_team = 'home' if stats.home_score < stats.away_score else 'away'
            conditions.append(f'{trailing_team.title()} team trailing by 1 goal after 75\'')
        
        # Draw situation (Both teams pushing for goals)
        elif goal_diff == 0 and stats.minute >= 75:
            score += SCORING_MATRIX['draw_situation_after_75min']
            conditions.append(f'Draw {stats.home_score}-{stats.away_score} after 75\' (both teams attacking)')
        
        # Use second half stats for much better "recent activity" detection
        # This is a major improvement - we now have period-level granularity!
        
        # Get second half stats for the focused team
        second_half_team_stats = stats.second_half_stats.get(team_focus, {})
        
        # High shots on target in 2nd half (much more accurate than total)
        second_half_shots_on_target = second_half_team_stats.get('shots_on_target', 0)
        if second_half_shots_on_target >= 5 and stats.minute >= 75:  # 5+ in 2nd half = very active
            score += SCORING_MATRIX['shots_on_target_last_15min_5plus']
            conditions.append(f'{second_half_shots_on_target} shots on target in 2nd half')
        
        # High total shots on target (reliable metric across all matches)
        team_shots_on_target = stats.shots_on_target[team_focus]
        if team_shots_on_target >= 8:
            score += SCORING_MATRIX['shots_on_target_total_8plus']
            conditions.append(f'{team_shots_on_target} total shots on target')
        
        # High dangerous attacks in 2nd half
        second_half_attacks = second_half_team_stats.get('dangerous_attacks', 0)
        if second_half_attacks >= 6 and stats.minute >= 75:
            score += SCORING_MATRIX['dangerous_attacks_last_10min_6plus']
            conditions.append(f'{second_half_attacks} dangerous attacks in 2nd half')
        

        
        # High total shots blocked (very high corner correlation)
        team_shots_blocked = stats.shots_blocked[team_focus]
        if team_shots_blocked >= 6:
            score += SCORING_MATRIX['shots_blocked_total_6plus'] 
            conditions.append(f'{team_shots_blocked} total shots blocked')
        
        # High big chances in 2nd half
        second_half_big_chances = second_half_team_stats.get('big_chances_created', 0)
        if second_half_big_chances >= 3 and stats.minute >= 75:
            score += SCORING_MATRIX['big_chances_created_last_15min_3plus']
            conditions.append(f'{second_half_big_chances} big chances in 2nd half')
        

        
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
        

        
        # Get second half stats for the focused team (for medium priority)
        second_half_team_stats = stats.second_half_stats.get(team_focus, {})
        
        # High shots inside box in 2nd half
        second_half_shots_inside = second_half_team_stats.get('shots_inside_box', 0)
        if second_half_shots_inside >= 4 and stats.minute >= 70:  # Lower threshold for 2nd half only
            score += SCORING_MATRIX['shots_inside_box_last_20min_5plus']
            conditions.append(f'{second_half_shots_inside} shots inside box in 2nd half')
        
        # Hit woodwork 3+ times (use total match - woodwork is rare)
        woodwork_hits = stats.hit_woodwork.get(team_focus, 0)
        if woodwork_hits >= 3:
            score += SCORING_MATRIX['hit_woodwork_3plus']
            conditions.append(f'{woodwork_hits} times hit woodwork')
        
        # High crosses in 2nd half
        second_half_crosses = second_half_team_stats.get('crosses_total', 0)
        if second_half_crosses >= 6 and stats.minute >= 70:  # 6+ crosses in 2nd half shows attacking intent
            score += SCORING_MATRIX['crosses_last_15min_8plus']
            conditions.append(f'{second_half_crosses} crosses in 2nd half')
        
        # High key passes in 2nd half
        second_half_key_passes = second_half_team_stats.get('key_passes', 0)
        if second_half_key_passes >= 4 and stats.minute >= 70:
            score += SCORING_MATRIX['key_passes_last_10min_4plus']
            conditions.append(f'{second_half_key_passes} key passes in 2nd half')
        
        # Counter attacks in 2nd half (desperation play)
        second_half_counter_attacks = second_half_team_stats.get('counter_attacks', 0)
        if second_half_counter_attacks >= 2 and stats.minute >= 70:
            score += SCORING_MATRIX['counter_attacks_last_15min_2plus']
            conditions.append(f'{second_half_counter_attacks} counter attacks in 2nd half')
        
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
        
        # Get second half stats for tactical indicators
        second_half_team_stats = stats.second_half_stats.get(team_focus, {})
        
        # High offsides in 2nd half (desperate attacking)
        second_half_offsides = second_half_team_stats.get('offsides', 0)
        if second_half_offsides >= 3 and stats.minute >= 70:  # 3+ in 2nd half = desperate
            score += SCORING_MATRIX['offsides_last_15min_3plus']
            conditions.append(f'{second_half_offsides} offsides in 2nd half (desperate attacking)')
        
        # High throwins in 2nd half (pressure play)
        second_half_throwins = second_half_team_stats.get('throwins', 0)
        if second_half_throwins >= 8 and stats.minute >= 70:  # 8+ in 2nd half = sustained pressure
            score += SCORING_MATRIX['throwins_last_20min_8plus']
            conditions.append(f'{second_half_throwins} throwins in 2nd half (pressure play)')
        

        
        return score, conditions
    
    def _evaluate_corner_context(self, stats: MatchStats) -> Tuple[float, List[str]]:
        """Evaluate corner count context - 7-12 corners already verified as mandatory"""
        score = 0.0
        conditions = []
        
        total_corners = stats.total_corners
        
        # Note: 7-12 range already verified before this function is called
        if 8 <= total_corners <= 11:
            score += SCORING_MATRIX['corners_8_to_11_sweet_spot']
            conditions.append(f'{total_corners} corners (SWEET SPOT)')
        elif total_corners == 7:
            score += SCORING_MATRIX['corners_7_baseline']
            conditions.append(f'{total_corners} corners (baseline)')
        elif total_corners == 12:
            score += SCORING_MATRIX['corners_12_maximum']
            conditions.append(f'{total_corners} corners (high but acceptable)')
        
        return score, conditions
    
    def _evaluate_negative_conditions(self, stats: MatchStats) -> Tuple[float, List[str]]:
        """Evaluate negative scoring conditions"""
        score = 0.0
        conditions = []
        
        # Red card issued
        if stats.red_cards:
            score += SCORING_MATRIX['red_card_issued']
            conditions.append(f'{len(stats.red_cards)} red card(s) issued')
        
        # Leading by 2+ goals (comfortable lead reduces corner urgency)
        goal_diff = abs(stats.home_score - stats.away_score)
        if goal_diff >= 2:
            score += SCORING_MATRIX['leading_by_2_goals']
            leading_team = 'home' if stats.home_score > stats.away_score else 'away'
            conditions.append(f'{leading_team.title()} team leading by {goal_diff} goals (comfortable lead)')
        

        
        # Goalkeeper making 8+ saves (shots from distance)
        # Note: saves data not available in current MatchStats, using shots_on_target as proxy
        home_saves = stats.shots_on_target.get('away', 0)  # Away shots on target = home goalkeeper saves attempt
        away_saves = stats.shots_on_target.get('home', 0)  # Home shots on target = away goalkeeper saves attempt
        
        if home_saves >= 8 or away_saves >= 8:
            score += SCORING_MATRIX['gk_making_8plus_saves']
            conditions.append(f'GK facing {max(home_saves, away_saves)} shots on target (high pressure)')
        
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
    

    
    def _is_in_alert_window(self, current_minute: int) -> bool:
        """Check if current minute is in the precise 85th minute alert window"""
        # Primary target: Exactly 85 minutes
        if current_minute == self.config.TARGET_ALERT_MINUTE:
            return True  # Perfect timing!
        
        # Small buffer for API timing variations (84:50-85:15 window)
        if current_minute == (self.config.TARGET_ALERT_MINUTE - 1):
            return True  # 84:xx - close enough for API delays
        
        return False  # Outside the precise window
    
    def _generate_match_context(self, stats: MatchStats, conditions: List[str]) -> str:
        """Generate human-readable match context"""
        score_context = f"{stats.home_score}-{stats.away_score}"
        minute_context = f"{stats.minute}'"
        
        # Top 3 most important conditions
        top_conditions = conditions[:3]
        conditions_text = "; ".join(top_conditions)
        
        return f"{score_context} at {minute_context} | {conditions_text}" 

    def _count_high_priority_indicators(self, triggered_conditions: list) -> int:
        """Count how many high-priority indicators are present in the triggered conditions list"""
        high_priority_keywords = [
            'trailing by 1',
            'draw',
            'shots on target',
            'dangerous attacks',
            'shots blocked',
            'big chances created',
        ]
        count = 0
        for cond in triggered_conditions:
            if any(keyword in cond.lower() for keyword in high_priority_keywords):
                count += 1
        return count 