import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    # API Configuration
    SPORTMONKS_API_KEY: str = os.getenv('SPORTMONKS_API_KEY', '')
    SPORTMONKS_BASE_URL: str = 'https://api.sportmonks.com/v3/football'
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID: str = os.getenv('TELEGRAM_CHAT_ID', '')
    
    # Scoring System Configuration
    ALERT_THRESHOLD: int = 6  # Minimum score to trigger alert
    MIN_MINUTE_FOR_ALERT: int = 85  # Don't alert before 85th minute
    
    # Corner Count Sweet Spot (at 85th minute)
    CORNER_SWEET_SPOT_MIN: int = 8
    CORNER_SWEET_SPOT_MAX: int = 11
    
    # Monitoring Configuration
    LIVE_POLL_INTERVAL: int = 60  # Poll every 60 seconds
    MATCH_DISCOVERY_INTERVAL: int = 300  # Check for new matches every 5 minutes
    MIN_MINUTE_TO_START_MONITORING: int = 70  # Start monitoring from 70th minute
    
    # Rate Limiting
    API_RATE_LIMIT_DELAY: float = 0.5  # Delay between API calls (seconds)
    
    # Logging
    LOG_LEVEL: str = 'INFO'
    LOG_FILE: str = 'latecorners.log'

# Scoring Matrix Configuration
SCORING_MATRIX = {
    # High Priority Indicators (3-5 points)
    'favorite_losing_drawing_80plus': 5,
    'shots_on_target_last_15min_5plus': 4,
    'dangerous_attacks_last_10min_6plus': 4,
    'shots_blocked_last_10min_4plus': 4,
    'big_chances_created_last_15min_3plus': 4,
    'team_trailing_by_1_after_75min': 4,
    
    # Medium Priority Indicators (2-3 points)
    'shots_total_second_half_10plus': 3,
    'shots_on_target_8plus_but_less_than_2_goals': 4,
    'possession_last_15min_65plus': 2,
    'shots_inside_box_last_20min_5plus': 3,
    'hit_woodwork_3plus': 3,
    'crosses_last_15min_8plus': 2,
    'key_passes_last_10min_4plus': 2,
    'counter_attacks_last_15min_2plus': 2,
    
    # Tactical Indicators (1-2 points)
    'attacking_sub_after_70min': 2,
    'fouls_drawn_15plus': 1,
    'successful_dribbles_last_20min_5plus': 1,
    'offsides_last_15min_3plus': 1,
    'throwins_last_20min_8plus': 1,
    'low_pass_accuracy_under_75percent': 1,
    
    # Corner Count Context (at 85th minute)
    'corners_8_to_11_sweet_spot': 3,
    'corners_6_to_7_positive': 1,
    'corners_12_to_14_high_action': 1,
    'corners_5_or_less_red_flag': -2,
    'corners_15plus_oversaturated': -1,
    
    # Negative Indicators
    'red_card_issued': -3,
    'leading_by_3plus_goals': -5,
    'possession_under_30percent': -2,
    'gk_making_8plus_saves': -1,
}

# Historical multipliers
HISTORICAL_MULTIPLIERS = {
    'team_averages_6plus_corners_per_game': 1.3,
    'head_to_head_avg_10plus_corners': 1.2,
    'home_team_losing_at_home': 1.4,
    'derby_rivalry_match': 1.2,
}

# Time-based progression
TIME_MULTIPLIERS = {
    '70_to_80_minutes': 1.0,
    '80_to_90_minutes': 1.5,
    '90plus_minutes': 2.0,
}

def get_config() -> Config:
    """Get configuration instance with validation."""
    config = Config()
    
    # Validate required API keys
    if not config.SPORTMONKS_API_KEY:
        raise ValueError("SPORTMONKS_API_KEY environment variable is required")
    
    if not config.TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        
    if not config.TELEGRAM_CHAT_ID:
        raise ValueError("TELEGRAM_CHAT_ID environment variable is required")
    
    return config 