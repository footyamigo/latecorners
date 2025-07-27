from flask import Flask, render_template, jsonify
import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time

load_dotenv()

app = Flask(__name__)

# --- Simple In-Memory Cache ---
CACHE = {
    'matches': [],
    'last_fetch_time': 0,
    'last_update_str': 'Never'
}
CACHE_DURATION = 60  # seconds

def get_live_data_from_cache_or_api():
    """
    Fetches live match data.
    - Returns cached data if it's less than CACHE_DURATION seconds old.
    - Otherwise, fetches new data from the API and updates the cache.
    """
    current_time = time.time()
    if current_time - CACHE['last_fetch_time'] < CACHE_DURATION:
        # Return data from cache
        return CACHE['matches'], CACHE['last_update_str']

    # --- Fetch new data from API ---
    api_key = os.getenv('SPORTMONKS_API_KEY')
    if not api_key:
        return [], 'API Key Missing'

    url = "https://api.sportmonks.com/v3/football/livescores/inplay"
    params = {'api_token': api_key, 'include': 'scores;participants;state;periods;league'}
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        matches = data.get('data', [])
        
        # Update cache
        CACHE['matches'] = matches
        CACHE['last_fetch_time'] = current_time
        CACHE['last_update_str'] = datetime.now().strftime('%H:%M:%S')
        
        return matches, CACHE['last_update_str']
        
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        # Return stale cache data if API fails
        return CACHE['matches'], f"API Error - {CACHE['last_update_str']}"

def calculate_dashboard_stats(matches, last_update_str):
    """Calculates dashboard stats from a list of matches."""
    matches_with_stats = [m for m in matches if 'statistics' in m and m.get('statistics')]
    late_matches = [m for m in matches if 'minute' in m and m.get('minute', 0) >= 83]
    
    return {
        'total_live': len(matches),
        'with_stats': len(matches_with_stats),
        'late_games': len(late_matches),
        'last_update': last_update_str
    }

@app.route('/')
def dashboard():
    matches, last_update_str = get_live_data_from_cache_or_api()
    stats = calculate_dashboard_stats(matches, last_update_str)
    return render_template('dashboard.html', matches=matches, stats=stats)

@app.route('/api/live-matches')
def api_live_matches():
    matches, last_update_str = get_live_data_from_cache_or_api()
    stats = calculate_dashboard_stats(matches, last_update_str)
    return jsonify({'matches': matches, 'stats': stats})

@app.route('/api/stats')
def api_stats():
    matches, last_update_str = get_live_data_from_cache_or_api()
    stats = calculate_dashboard_stats(matches, last_update_str)
    return jsonify(stats)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    app.run(debug=debug_mode, host='0.0.0.0', port=port) 