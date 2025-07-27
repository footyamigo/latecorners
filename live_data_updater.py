import os
import requests
import json
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('SPORTMONKS_API_KEY')
OUTPUT_FILE = 'live_matches.json'
FETCH_INTERVAL = 60  # seconds


def fetch_live_matches():
    url = 'https://api.sportmonks.com/v3/football/livescores/inplay'
    params = {
        'api_token': API_KEY,
        'include': 'scores;participants;state;periods;league;statistics'
    }
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            matches = data.get('data', [])
            print(f"[{datetime.now()}] ✅ Retrieved {len(matches)} matches from API.")
            return matches
        else:
            print(f"[{datetime.now()}] ❌ API error: {response.status_code} - {response.text[:200]}")
            return []
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Exception: {e}")
        return []

def save_matches(matches):
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'last_update': datetime.now().isoformat(),
                'matches': matches
            }, f, ensure_ascii=False, indent=2)
        print(f"[{datetime.now()}] 💾 Saved {len(matches)} matches to {OUTPUT_FILE}.")
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Failed to save matches: {e}")

def main():
    while True:
        matches = fetch_live_matches()
        save_matches(matches)
        time.sleep(FETCH_INTERVAL)

if __name__ == '__main__':
    main() 