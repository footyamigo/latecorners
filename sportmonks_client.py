import requests
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from config import get_config

# Rate limiting tracker
class RateLimitTracker:
    def __init__(self):
        self.request_times = []
        self.last_429_time = 0
        self.backoff_until = 0
        
    def can_make_request(self) -> bool:
        """Check if we can make a request without hitting rate limits"""
        now = time.time()
        
        # If we're in backoff period, wait
        if now < self.backoff_until:
            return False
            
        # Clean old request times (older than 1 minute)
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        # Check if we're under the limit
        config = get_config()
        max_per_minute = getattr(config, 'MAX_REQUESTS_PER_MINUTE', 100)
        return len(self.request_times) < max_per_minute
    
    def record_request(self):
        """Record a successful request"""
        self.request_times.append(time.time())
    
    def record_429_error(self):
        """Record a 429 error and set backoff time"""
        now = time.time()
        self.last_429_time = now
        # Exponential backoff: start with 60 seconds, double each time
        backoff_duration = min(300, 60 * (2 ** len([t for t in self.request_times if now - t < 300])))
        self.backoff_until = now + backoff_duration
        logging.warning(f"⚠️ Rate limit hit! Backing off for {backoff_duration} seconds")

rate_limiter = RateLimitTracker()

@dataclass
class MatchStats:
    """Container for match statistics"""
    fixture_id: int
    minute: int
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    total_corners: int
    
    # Team statistics (total for the match) - UPDATED to match official Sportmonks API
    shots_on_target: Dict[str, int]      # Type 86: Shots that hit the goal
    shots_off_target: Dict[str, int]     # Type 41: Shots that missed the goal  
    shots_total: Dict[str, int]          # Type 42: All shots attempted
    shots_blocked: Dict[str, int]        # Type 58: Shots blocked by defense
    shots_inside_box: Dict[str, int]     # Type 49: Shots from inside penalty area
    shots_outside_box: Dict[str, int]    # Type 50: Shots from outside penalty area
    
    dangerous_attacks: Dict[str, int]    # Type 44: High-threat attacking moves
    attacks: Dict[str, int]              # Type 45: General attacking moves
    counter_attacks: Dict[str, int]      # Type 1527: Counter-attack situations
    
    big_chances_created: Dict[str, int]  # Type 580: Clear scoring opportunities created
    big_chances_missed: Dict[str, int]   # Type 581: Clear scoring opportunities missed
    
    possession: Dict[str, int]           # Type 34: Ball possession percentage
    
    hit_woodwork: Dict[str, int]         # Type 64: Shots hitting post/crossbar
    crosses_total: Dict[str, int]        # Type 98: Total crosses attempted
    key_passes: Dict[str, int]           # Type 117: Passes leading to shots
    successful_dribbles: Dict[str, int]  # Type 109: Successful dribbling attempts
    
    offsides: Dict[str, int]             # Type 51: Offside violations
    fouls: Dict[str, int]                # Type 56: Fouls committed
    free_kicks: Dict[str, int]           # Type 55: Free kicks awarded
    throwins: Dict[str, int]             # Type 60: Throw-ins taken
    
    penalties: Dict[str, int]            # Type 47: Penalty situations
    goals: Dict[str, int]                # Type 52: Goals scored
    goal_attempts: Dict[str, int]        # Type 54: Goal attempts made
    
    saves: Dict[str, int]                # Type 57: Goalkeeper saves
    tackles: Dict[str, int]              # Type 78: Defensive tackles
    assists: Dict[str, int]              # Type 79: Goal assists
    passes: Dict[str, int]               # Type 80: Total passes attempted
    pass_accuracy: Dict[str, int]        # Type 82: Pass success percentage
    
    # Events
    substitutions: List[Dict]
    red_cards: List[Dict]
    
    # Additional live data fields
    state: str = ""
    events: List[Dict] = None
    statistics: List[Dict] = None
    periods: List[Dict] = None
    
    # Period-based statistics for better "recent activity" detection
    second_half_stats: Dict[str, Dict[str, int]] = None  # {'home': {...}, 'away': {...}}
    
    def __post_init__(self):
        if self.events is None:
            self.events = []
        if self.statistics is None:
            self.statistics = []
        if self.periods is None:
            self.periods = []
        if self.second_half_stats is None:
            self.second_half_stats = {'home': {}, 'away': {}}

class SportmonksClient:
    """Client for interacting with Sportmonks API"""
    
    def __init__(self):
        self.config = get_config()
        self.base_url = self.config.SPORTMONKS_BASE_URL
        self.api_key = self.config.SPORTMONKS_API_KEY
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
        
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make a request to the Sportmonks API with rate limiting"""
        # Check rate limiting before making request
        if not rate_limiter.can_make_request():
            self.logger.warning("⚠️ Rate limit check failed, skipping request")
            return None
        
        url = f"{self.base_url}{endpoint}"
        
        if params is None:
            params = {}
        
        params['api_token'] = self.api_key
        
        try:
            # Rate limiting delay
            time.sleep(self.config.API_RATE_LIMIT_DELAY)
            
            response = self.session.get(url, params=params)
            
            # Handle 429 specifically
            if response.status_code == 429:
                rate_limiter.record_429_error()
                self.logger.error(f"❌ Rate limit exceeded (429) for {endpoint}. Backing off...")
                return None
            
            response.raise_for_status()
            rate_limiter.record_request()
            
            data = response.json()
            
            if data.get('data') is None:
                self.logger.warning(f"No data returned from {endpoint}")
                return None
                
            return data
            
        except requests.exceptions.RequestException as e:
            if "429" in str(e):
                rate_limiter.record_429_error()
            self.logger.error(f"API request failed for {endpoint}: {e}")
            return None
        except ValueError as e:
            self.logger.error(f"JSON decode error for {endpoint}: {e}")
            return None
    
    def get_live_matches(self, filter_by_minute: bool = False) -> List[Dict]:
        """Get all currently live matches
        
        Args:
            filter_by_minute: If True, only return matches past MIN_MINUTE_TO_START_MONITORING
                             If False, return ALL live matches (useful for testing)
        """
        self.logger.info("Fetching live matches...")
        
        # 🎯 KEY FIX: Add includes to get live data + periods for minute
        params = {
            'include': 'scores;participants;state;events;periods'  # 🎯 ADDED: periods for match minute
        }
        
        data = self._make_request("/livescores/inplay", params=params)
        if not data:
            return []
        
        all_matches = data.get('data', [])
        
        # 🎯 NEW: Filter for TRULY LIVE matches (actively playing + half-time)
        TRULY_LIVE_STATES = {
            'INPLAY_1ST_HALF',     # Playing 1st half
            'INPLAY_2ND_HALF',     # Playing 2nd half 
            'HT',                  # Half-time break (will resume in 2nd half)
            'INPLAY_ET',           # Extra time
            'INPLAY_PENALTIES'     # Penalty shootout
        }
        
        # First filter: Only truly playing matches
        truly_live_matches = []
        for match in all_matches:
            state = match.get('state', {})
            if isinstance(state, dict):
                state_name = state.get('developer_name', '')
                if state_name in TRULY_LIVE_STATES:
                    truly_live_matches.append(match)
        
        if not filter_by_minute:
            # Return all truly live matches
            self.logger.info(f"Found {len(truly_live_matches)} truly live matches (out of {len(all_matches)} total)")
            return truly_live_matches
        
        # Filter matches that are in 2nd half and past 70 minutes
        relevant_matches = []
        for match in truly_live_matches:
            # 🔧 FIXED: Extract minute from proper location
            minute = self._extract_minute(match)
            
            # 🔧 FIXED: Extract state from proper location  
            state = self._extract_state(match)
            
            # 🎯 OPTIMIZED: Only monitor 2nd half matches (where late corners happen)
            if (state == 'INPLAY_2ND_HALF' and 
                minute >= self.config.MIN_MINUTE_TO_START_MONITORING):
                relevant_matches.append(match)
        
        self.logger.info(f"Found {len(relevant_matches)} relevant live matches (past {self.config.MIN_MINUTE_TO_START_MONITORING} minutes)")
        return relevant_matches
    
    def _extract_minute(self, match: Dict) -> int:
        """Extract current minute from match data"""
        # 🎯 FIXED: Get minute from periods data (the correct way)
        periods = match.get('periods', [])
        
        # Find the currently active period (ticking = true)
        for period in periods:
            if period.get('ticking', False):
                # The 'minutes' field already represents total match time
                # DO NOT add 45 for 2nd half - it's already included!
                return period.get('minutes', 0)
        
        # Fallback: try the old way (usually returns 0)
        minute = match.get('minute', 0)
        if minute == 0:
            state = match.get('state', {})
            if isinstance(state, dict):
                minute = state.get('minute', 0)
        
        return minute
    
    def _extract_state(self, match: Dict) -> str:
        """Extract current state from match data"""
        state = match.get('state', {})
        if isinstance(state, dict):
            # Use developer_name which has full state names like "INPLAY_2ND_HALF"
            return state.get('developer_name', state.get('short_name', ''))
        return ''
    
    def _extract_teams(self, match: Dict) -> tuple:
        """Extract home and away team names from match data"""
        participants = match.get('participants', [])
        home_team = "Unknown"
        away_team = "Unknown"
        
        for participant in participants:
            meta = participant.get('meta', {})
            if meta.get('location') == 'home':
                home_team = participant.get('name', 'Unknown')
            elif meta.get('location') == 'away':
                away_team = participant.get('name', 'Unknown')
        
        return home_team, away_team
    
    def _extract_score(self, match: Dict) -> tuple:
        """Extract current score from match data"""
        scores = match.get('scores', [])
        home_score = 0
        away_score = 0
        
        # Find CURRENT score entries and match by participant
        for score_entry in scores:
            if score_entry.get('description') == 'CURRENT':
                score_data = score_entry.get('score', {})
                goals = score_data.get('goals', 0)
                participant = score_data.get('participant', '')
                
                if participant == 'home':
                    home_score = goals
                elif participant == 'away':
                    away_score = goals
        
        return home_score, away_score
    
    def get_pre_match_favorite(self, fixture_id: int) -> Optional[int]:
        """Get the pre-match favorite team ID"""
        self.logger.info(f"Getting pre-match favorite for fixture {fixture_id}")
        
        data = self._make_request(f"/odds/pre-match/by-fixture/{fixture_id}")
        if not data:
            return None
        
        try:
            odds_data = data.get('data', [])
            
            # Find 1X2 market (match winner)
            for bookmaker_data in odds_data:
                markets = bookmaker_data.get('markets', [])
                for market in markets:
                    if market.get('market_id') == 1:  # 1X2 market
                        selections = market.get('selections', [])
                        
                        # Find team with lowest odds (favorite)
                        min_odds = float('inf')
                        favorite_team_id = None
                        
                        for selection in selections:
                            if selection.get('label') in ['1', '2']:  # Home or Away win
                                odds = float(selection.get('odds', float('inf')))
                                if odds < min_odds:
                                    min_odds = odds
                                    # Map selection to team
                                    if selection.get('label') == '1':
                                        # This is a simplified approach - we'd need the fixture data
                                        # to properly map to team IDs
                                        pass
                        
                        return favorite_team_id
            
        except Exception as e:
            self.logger.error(f"Error parsing pre-match odds for fixture {fixture_id}: {e}")
        
        return None
    
    def get_fixture_stats(self, fixture_id: int) -> Optional[MatchStats]:
        """Get detailed fixture statistics and events"""
        self.logger.info(f"Fetching stats for fixture {fixture_id}")
        
        # 🎯 KEY FIX: Add includes to get detailed match data + periods for minute
        # Using exact format from SportMonks documentation: statistics,periods with period-level stats
        params = {
            'include': 'statistics,periods.statistics,events,scores,participants,state'  # 🎯 FIXED: Using comma separators + periods.statistics as per docs
        }
        
        data = self._make_request(f"/fixtures/{fixture_id}", params=params)
        if not data:
            return None
        
        fixture = data.get('data')
        if not fixture:
            return None
        
        # 🔧 FIXED: Use helper methods for extraction
        minute = self._extract_minute(fixture)
        state = self._extract_state(fixture)
        home_team, away_team = self._extract_teams(fixture)
        home_score, away_score = self._extract_score(fixture)
        
        # Parse statistics
        stats = fixture.get('statistics', [])
        events = fixture.get('events', [])
        
        # Initialize counters
        total_corners = 0
        shots_on_target = 0
        
        # Extract corner and shot statistics
        for stat in stats:
            stat_type = stat.get('type', {}).get('name', '')
            value = stat.get('value', 0)
            
            if stat_type == 'Corner Kicks':
                total_corners += value
            elif stat_type == 'Shots on Goal':
                shots_on_target += value
        
        return MatchStats(
            fixture_id=fixture_id,
            minute=minute,
            home_team=home_team,
            away_team=away_team,
            home_score=home_score,
            away_score=away_score,
            total_corners=total_corners,
            shots_on_target={'home': 0, 'away': 0},  # Placeholder - to be filled by scoring engine
            shots_total={'home': 0, 'away': 0},
            shots_blocked={'home': 0, 'away': 0},
            dangerous_attacks={'home': 0, 'away': 0},
            big_chances_created={'home': 0, 'away': 0},
            big_chances_missed={'home': 0, 'away': 0},
            possession={'home': 0, 'away': 0},
            shots_inside_box={'home': 0, 'away': 0},
            hit_woodwork={'home': 0, 'away': 0},
            crosses_total={'home': 0, 'away': 0},
            key_passes={'home': 0, 'away': 0},
            counter_attacks={'home': 0, 'away': 0},
            fouls={'home': 0, 'away': 0},
            successful_dribbles={'home': 0, 'away': 0},
            offsides={'home': 0, 'away': 0},
            throwins={'home': 0, 'away': 0},
            pass_accuracy={'home': 0, 'away': 0},
            
            # Events
            substitutions=[],
            red_cards=[],
            
            # Additional fields for our system
            state=state,
            events=events,
            statistics=stats
        )
    
    def _parse_fixture_data(self, fixture_data: Dict) -> MatchStats:
        """Parse fixture data into MatchStats object"""
        
        # Basic match info
        fixture_id = fixture_data['id']
        minute = fixture_data.get('minute', 0)
        match_state = fixture_data.get('state', {}).get('state', '') if isinstance(fixture_data.get('state'), dict) else fixture_data.get('state', '')
        
        # Team IDs
        participants = fixture_data.get('participants', [])
        home_team_id = None
        away_team_id = None
        
        for participant in participants:
            if participant.get('meta', {}).get('location') == 'home':
                home_team_id = participant['id']
            else:
                away_team_id = participant['id']
        
        # Scores
        scores = fixture_data.get('scores', [])
        home_score = away_score = 0
        
        for score in scores:
            if score.get('description') == 'CURRENT':
                goals = score.get('score', {}).get('goals', {})
                home_score = goals.get('home', 0)
                away_score = goals.get('away', 0)
                break
        
        # Statistics parsing
        statistics = fixture_data.get('statistics', [])
        
        # Initialize stat dictionaries - UPDATED to match official Sportmonks API
        stats_dict = {
            # Shooting statistics
            'shots_on_target': {'home': 0, 'away': 0},      # Type 86
            'shots_off_target': {'home': 0, 'away': 0},     # Type 41  
            'shots_total': {'home': 0, 'away': 0},          # Type 42
            'shots_blocked': {'home': 0, 'away': 0},        # Type 58
            'shots_inside_box': {'home': 0, 'away': 0},     # Type 49
            'shots_outside_box': {'home': 0, 'away': 0},    # Type 50
            
            # Attacking statistics
            'dangerous_attacks': {'home': 0, 'away': 0},    # Type 44
            'attacks': {'home': 0, 'away': 0},              # Type 45
            'counter_attacks': {'home': 0, 'away': 0},      # Type 1527
            
            # Chances statistics
            'big_chances_created': {'home': 0, 'away': 0},  # Type 580
            'big_chances_missed': {'home': 0, 'away': 0},   # Type 581
            
            # Possession statistics
            'possession': {'home': 0, 'away': 0},           # Type 34
            
            # Technical statistics
            'hit_woodwork': {'home': 0, 'away': 0},         # Type 64
            'crosses_total': {'home': 0, 'away': 0},        # Type 98
            'key_passes': {'home': 0, 'away': 0},           # Type 117
            'successful_dribbles': {'home': 0, 'away': 0},  # Type 109
            
            # Disciplinary statistics  
            'offsides': {'home': 0, 'away': 0},             # Type 51
            'fouls': {'home': 0, 'away': 0},                # Type 56
            'free_kicks': {'home': 0, 'away': 0},           # Type 55
            'throwins': {'home': 0, 'away': 0},             # Type 60
            
            # Goal-related statistics
            'penalties': {'home': 0, 'away': 0},            # Type 47
            'goals': {'home': 0, 'away': 0},                # Type 52
            'goal_attempts': {'home': 0, 'away': 0},        # Type 54
            
            # Defensive statistics
            'saves': {'home': 0, 'away': 0},                # Type 57
            'tackles': {'home': 0, 'away': 0},              # Type 78
            'assists': {'home': 0, 'away': 0},              # Type 79
            'passes': {'home': 0, 'away': 0},               # Type 80
            'pass_accuracy': {'home': 0, 'away': 0},        # Type 82
        }
        
        # Map Sportmonks stat IDs to our stat names (CORRECTED based on official documentation)
        stat_id_mapping = {
            # OFFICIAL MAPPINGS - https://docs.sportmonks.com/football/definitions/types/statistics/fixture-statistics
            33: 'corners',                # ✅ CORNERS (official)
            34: 'possession',             # ✅ POSSESSION (official) - NOT corners!
            41: 'shots_off_target',       # ✅ SHOTS_OFF_TARGET (official) - NOT shots on target!
            42: 'shots_total',            # ✅ SHOTS_TOTAL (confirmed)
            44: 'dangerous_attacks',      # ✅ DANGEROUS_ATTACKS (confirmed)
            45: 'attacks',                # ✅ ATTACKS (official) - general attacking moves
            47: 'penalties',              # ✅ PENALTIES
            49: 'shots_inside_box',       # ✅ SHOTS_INSIDEBOX
            50: 'shots_outside_box',      # ✅ SHOTS_OUTSIDEBOX
            51: 'offsides',               # ✅ OFFSIDES (confirmed)
            52: 'goals',                  # ✅ GOALS
            54: 'goal_attempts',          # ✅ GOAL_ATTEMPTS (official) - NOT offsides!
            55: 'free_kicks',             # ✅ FREE_KICKS
            56: 'fouls',                  # ✅ FOULS
            57: 'saves',                  # ✅ SAVES
            58: 'shots_blocked',          # ✅ SHOTS_BLOCKED
            60: 'throwins',               # ✅ THROWINS
            64: 'hit_woodwork',           # ✅ HIT_WOODWORK
            78: 'tackles',                # ✅ TACKLES
            79: 'assists',                # ✅ ASSISTS
            80: 'passes',                 # ✅ PASSES
            82: 'pass_accuracy',          # ✅ SUCCESSFUL_PASSES_PERCENTAGE
            86: 'shots_on_target',        # ✅ SHOTS_ON_TARGET (confirmed)
            98: 'crosses_total',          # ✅ TOTAL_CROSSES
            109: 'successful_dribbles',   # ✅ SUCCESSFUL_DRIBBLES
            117: 'key_passes',            # ✅ KEY_PASSES
            580: 'big_chances_created',   # ✅ BIG_CHANCES_CREATED
            581: 'big_chances_missed',    # ✅ BIG_CHANCES_MISSED
            1527: 'counter_attacks',      # ✅ COUNTER_ATTACKS
        }
        
        total_corners = 0
        
        # Parse statistics for each team
        self.logger.info(f"📊 PARSING MAIN STATISTICS: {len(statistics)} total stats")
        
        parsed_stats_count = 0
        unknown_types = []
        zero_value_count = 0
        
        for stat in statistics:
            stat_id = stat.get('type_id')
            stat_name = stat_id_mapping.get(stat_id)
            
            if not stat_name:
                unknown_types.append(stat_id)
                continue
                
            # Handle both legacy format (participant_id + value) and live format (location + data.value)
            participant_id = stat.get('participant_id')
            location = stat.get('location')  # Live data format
            value = stat.get('value', stat.get('data', {}).get('value', 0))  # Support both formats
            
            if value == 0:
                zero_value_count += 1
                
            # Debug logging for important stats
            if stat_name in ['possession', 'dangerous_attacks', 'shots_on_target', 'corners']:
                self.logger.info(f"   🎯 {stat_name}: type_id={stat_id}, location={location}, value={value}")
            
            if stat_name == 'corners':
                total_corners += value
                self.logger.info(f"   ⚽ CORNER: +{value} (total: {total_corners})")
            elif participant_id == home_team_id or location == 'home':
                stats_dict[stat_name]['home'] = value
                parsed_stats_count += 1
            elif participant_id == away_team_id or location == 'away':
                stats_dict[stat_name]['away'] = value  
                parsed_stats_count += 1
        
        self.logger.info(f"📈 MAIN STATS SUMMARY:")
        self.logger.info(f"   ✅ Parsed: {parsed_stats_count} statistics")
        self.logger.info(f"   ❌ Unknown type_ids: {unknown_types}")
        self.logger.info(f"   ⚪ Zero values: {zero_value_count}")
        self.logger.info(f"   ⚽ Total corners: {total_corners}")
        
        # Parse events (substitutions, red cards)
        events = fixture_data.get('events', [])
        substitutions = []
        red_cards = []
        
        for event in events:
            event_type = event.get('type', {}).get('name', '')
            if 'substitution' in event_type.lower():
                substitutions.append(event)
            elif 'red card' in event_type.lower():
                red_cards.append(event)
        
        # Parse periods and extract second half statistics
        periods = fixture_data.get('periods', [])
        
        # DEBUG: Log what periods data we're getting from SportMonks
        self.logger.info(f"🔍 PERIODS DEBUG for {fixture_id}: Found {len(periods)} periods in API response")
        if periods:
            for i, period in enumerate(periods):
                period_desc = period.get('description', 'Unknown')
                period_stats_count = len(period.get('statistics', []))
                self.logger.info(f"   Period {i+1}: {period_desc} - {period_stats_count} statistics")
        else:
            self.logger.warning(f"⚠️ PERIODS MISSING: No periods data in SportMonks response for {fixture_id}")
            self.logger.warning(f"   API Include: 'statistics;events;scores;participants;state;periods;periods.statistics'")
            # Log the actual fixture data keys to debug
            fixture_keys = list(fixture_data.keys())
            self.logger.warning(f"   Available keys in fixture_data: {fixture_keys}")
        
        second_half_stats = self._extract_second_half_stats(periods, home_team_id, away_team_id, stat_id_mapping, 
                                                             fixture_data.get('statistics', []), match_state)
        
        return MatchStats(
            fixture_id=fixture_id,
            minute=minute,
            home_team=home_team_id,
            away_team=away_team_id,
            home_score=home_score,
            away_score=away_score,
            total_corners=total_corners,
            **stats_dict,
            substitutions=substitutions,
            red_cards=red_cards,
            periods=periods,
            second_half_stats=second_half_stats
        )
    
    def _extract_second_half_stats(self, periods: List[Dict], home_team_id: int, away_team_id: int, stat_id_mapping: Dict, 
                                  live_statistics: List[Dict] = None, match_state: str = None) -> Dict[str, Dict[str, int]]:
        """Extract statistics for the second half period"""
        second_half_stats = {'home': {}, 'away': {}}
        
        self.logger.info(f"🔍 EXTRACTING 2ND HALF STATS:")
        self.logger.info(f"   Periods count: {len(periods) if periods else 0}")
        self.logger.info(f"   Live stats count: {len(live_statistics) if live_statistics else 0}")
        self.logger.info(f"   Match state: {match_state}")
        
        # Method 1: Try to extract from periods data (historical/finished matches)
        second_half_period = None
        for period in periods:
            description = period.get('description', '').lower()
            if '2nd' in description or 'second' in description:
                second_half_period = period
                break
        
        if second_half_period:
            self.logger.info(f"📊 FOUND 2ND HALF PERIOD: Extracting from periods data")
            # Extract statistics from the second half period
            period_statistics = second_half_period.get('statistics', [])
            
            for stat in period_statistics:
                stat_id = stat.get('type_id')
                stat_name = stat_id_mapping.get(stat_id)
                
                if stat_name and stat_name != 'corners':  # Skip corners as they're handled separately
                    participant_id = stat.get('participant_id')
                    value = stat.get('value', 0)
                    
                    if participant_id == home_team_id:
                        second_half_stats['home'][stat_name] = value
                    elif participant_id == away_team_id:
                        second_half_stats['away'][stat_name] = value
        
        # Method 2: If we're in a live second half match, use live statistics
        elif live_statistics and match_state:
            is_second_half = ('2nd' in match_state.lower() or 'inplay_2nd_half' in match_state.lower())
            self.logger.info(f"🔴 LIVE STATS AVAILABLE: match_state='{match_state}', is_2nd_half={is_second_half}")
            
            if is_second_half:
                self.logger.info(f"🔴 LIVE 2ND HALF DETECTED: Parsing live statistics as second half data")
                
                # Parse live statistics for second half
                stats_parsed = 0
                for stat in live_statistics:
                    stat_id = stat.get('type_id')
                    stat_name = stat_id_mapping.get(stat_id)
                    
                    if stat_name and stat_name != 'corners':  # Skip corners as they're handled separately
                        location = stat.get('location')  # 'home' or 'away'
                        value = stat.get('data', {}).get('value', 0)
                        
                        # Special validation for possession (should be percentage 0-100)
                        if stat_name == 'possession':
                            if value < 0 or value > 100:
                                self.logger.warning(f"⚠️ SUSPICIOUS POSSESSION: {location} {stat_name}={value}% (Type {stat_id})")
                                # Don't skip, but log the issue
                            self.logger.info(f"   🎯 POSSESSION: {location} = {value}%")
                        
                        if location in ['home', 'away'] and value > 0:
                            second_half_stats[location][stat_name] = value
                            stats_parsed += 1
                            self.logger.info(f"   ✅ {location} {stat_name}: {value}")
                
                self.logger.info(f"   📊 TOTAL PARSED: {stats_parsed} live statistics")
        
        # Final verification
        home_stats_count = len(second_half_stats['home'])
        away_stats_count = len(second_half_stats['away'])
        
        if home_stats_count > 0 or away_stats_count > 0:
            self.logger.info(f"✅ 2ND HALF STATS EXTRACTED: {home_stats_count} home, {away_stats_count} away")
            self.logger.info(f"   🏠 Home stats: {list(second_half_stats['home'].keys())}")
            self.logger.info(f"   🚌 Away stats: {list(second_half_stats['away'].keys())}")
        else:
            self.logger.warning(f"⚠️ NO 2ND HALF STATS EXTRACTED!")
            self.logger.warning(f"   Debug: periods={len(periods)}, live_stats={len(live_statistics) if live_statistics else 0}")
        
        return second_half_stats

    def _parse_live_match_data(self, match_data: Dict) -> Optional[MatchStats]:
        """Parse live match data from livescores/inplay endpoint into MatchStats format"""
        try:
            fixture_id = match_data['id']
            minute = self._extract_minute(match_data)
            state = self._extract_state(match_data)
            home_team, away_team = self._extract_teams(match_data)
            home_score, away_score = self._extract_score(match_data)
            
            # Parse statistics from live feed
            stats = match_data.get('statistics', [])
            events = match_data.get('events', [])
            
            # SportMonks type_id mapping for live data - REMOVED OLD INCONSISTENT MAPPINGS
            # Using only the official corrected mappings now
            stat_type_mapping = {
                33: 'corners',                # ✅ CORNERS (official)
                34: 'possession',             # ✅ POSSESSION (official)
                41: 'shots_off_target',       # ✅ SHOTS_OFF_TARGET (official)
                42: 'shots_total',            # ✅ SHOTS_TOTAL (confirmed)
                44: 'dangerous_attacks',      # ✅ DANGEROUS_ATTACKS (confirmed)
                45: 'attacks',                # ✅ ATTACKS (official)
                51: 'offsides',               # ✅ OFFSIDES (confirmed)
                54: 'goal_attempts',          # ✅ GOAL_ATTEMPTS (official)
                86: 'shots_on_target',        # ✅ SHOTS_ON_TARGET (confirmed)
            }
            
            # Initialize statistics dictionaries
            home_stats = {}
            away_stats = {}
            total_corners = 0
            
            # Parse raw statistics with type_id mapping
            for stat in stats:
                type_id = stat.get('type_id')
                value = stat.get('data', {}).get('value', 0)
                location = stat.get('location', '')
                
                if type_id in stat_type_mapping:
                    stat_name = stat_type_mapping[type_id]
                    
                    if type_id == 33:  # Corners - special handling for total
                        total_corners += value
                    elif location == 'home':
                        home_stats[stat_name] = value
                    elif location == 'away':
                        away_stats[stat_name] = value
            
            # Debug logging for parsed statistics
            if home_stats or away_stats:
                self.logger.debug(f"🧪 PARSED STATS for {fixture_id}: Home={home_stats}, Away={away_stats}, Corners={total_corners}")
            
            # Map to MatchStats format with proper defaults
            return MatchStats(
                fixture_id=fixture_id,
                minute=minute,
                home_team=home_team,
                away_team=away_team,
                home_score=home_score,
                away_score=away_score,
                total_corners=total_corners,
                shots_on_target={
                    'home': home_stats.get('shots_on_target', 0),
                    'away': away_stats.get('shots_on_target', 0)
                },
                shots_off_target={
                    'home': home_stats.get('shots_off_target', 0),
                    'away': away_stats.get('shots_off_target', 0)
                },
                shots_total={
                    'home': home_stats.get('shots_total', 0),
                    'away': away_stats.get('shots_total', 0)
                },
                shots_blocked={
                    'home': home_stats.get('shots_blocked', 0),
                    'away': away_stats.get('shots_blocked', 0)
                },
                shots_inside_box={
                    'home': home_stats.get('shots_inside_box', 0),
                    'away': away_stats.get('shots_inside_box', 0)
                },
                shots_outside_box={
                    'home': home_stats.get('shots_outside_box', 0),
                    'away': away_stats.get('shots_outside_box', 0)
                },
                dangerous_attacks={
                    'home': home_stats.get('dangerous_attacks', 0),
                    'away': away_stats.get('dangerous_attacks', 0)
                },
                attacks={
                    'home': home_stats.get('attacks', 0),
                    'away': away_stats.get('attacks', 0)
                },
                counter_attacks={'home': 0, 'away': 0},  # Not available in live feed
                big_chances_created={'home': 0, 'away': 0},  # Not available in live feed
                big_chances_missed={'home': 0, 'away': 0},   # Not available in live feed
                possession={
                    'home': home_stats.get('possession', 0),
                    'away': away_stats.get('possession', 0)
                },
                hit_woodwork={
                    'home': home_stats.get('hit_woodwork', 0),
                    'away': away_stats.get('hit_woodwork', 0)
                },
                crosses_total={
                    'home': home_stats.get('crosses_total', 0),
                    'away': away_stats.get('crosses_total', 0)
                },
                key_passes={
                    'home': home_stats.get('key_passes', 0),
                    'away': away_stats.get('key_passes', 0)
                },
                successful_dribbles={
                    'home': home_stats.get('successful_dribbles', 0),
                    'away': away_stats.get('successful_dribbles', 0)
                },
                offsides={
                    'home': home_stats.get('offsides', 0),
                    'away': away_stats.get('offsides', 0)
                },
                fouls={
                    'home': home_stats.get('fouls', 0),
                    'away': away_stats.get('fouls', 0)
                },
                free_kicks={
                    'home': home_stats.get('free_kicks', 0),
                    'away': away_stats.get('free_kicks', 0)
                },
                throwins={
                    'home': home_stats.get('throwins', 0),
                    'away': away_stats.get('throwins', 0)
                },
                penalties={
                    'home': home_stats.get('penalties', 0),
                    'away': away_stats.get('penalties', 0)
                },
                goals={
                    'home': home_stats.get('goals', 0),
                    'away': away_stats.get('goals', 0)
                },
                goal_attempts={
                    'home': home_stats.get('goal_attempts', 0),
                    'away': away_stats.get('goal_attempts', 0)
                },
                saves={
                    'home': home_stats.get('saves', 0),
                    'away': away_stats.get('saves', 0)
                },
                tackles={
                    'home': home_stats.get('tackles', 0),
                    'away': away_stats.get('tackles', 0)
                },
                assists={
                    'home': home_stats.get('assists', 0),
                    'away': away_stats.get('assists', 0)
                },
                passes={
                    'home': home_stats.get('passes', 0),
                    'away': away_stats.get('passes', 0)
                },
                pass_accuracy={
                    'home': home_stats.get('pass_accuracy', 0),
                    'away': away_stats.get('pass_accuracy', 0)
                },
                
                # Events
                substitutions=[],
                red_cards=[],
                
                # Additional fields
                state=state,
                events=events,
                statistics=stats
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing live match data for fixture {match_data.get('id', 'unknown')}: {e}")
            return None
    
    def get_live_corner_odds(self, fixture_id: int) -> Optional[Dict]:
        """Get live corner betting odds"""
        self.logger.info(f"Getting live corner odds for fixture {fixture_id}")
        
        data = self._make_request(f"/odds/in-play/by-fixture/{fixture_id}")
        if not data:
            return None
        
        try:
            odds_data = data.get('data', [])
            corner_odds = {}
            
            # Look for corner-related markets
            for bookmaker_data in odds_data:
                markets = bookmaker_data.get('markets', [])
                bookmaker_name = bookmaker_data.get('bookmaker', {}).get('name', 'Unknown')
                
                for market in markets:
                    market_name = market.get('market_name', '').lower()
                    
                    # Look for Asian corner markets
                    if 'corner' in market_name and ('asian' in market_name or 'handicap' in market_name):
                        selections = market.get('selections', [])
                        
                        for selection in selections:
                            label = selection.get('label', '')
                            odds = selection.get('odds')
                            
                            if 'over' in label.lower() and odds:
                                corner_odds[f"{bookmaker_name}_{label}"] = {
                                    'odds': odds,
                                    'market': market_name,
                                    'selection': label
                                }
            
            return corner_odds if corner_odds else None
            
        except Exception as e:
            self.logger.error(f"Error parsing live corner odds for fixture {fixture_id}: {e}")
            return None 