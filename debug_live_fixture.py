#!/usr/bin/env python3
"""
Fetch a single live fixture from livescores/inplay (via our dashboard helper)
and print the available live stats (home | away) for quick verification.

Usage:
  python latecorners/debug_live_fixture.py 19392535
"""

import os
import sys
from typing import Any, Dict


def main() -> None:
    try:
        from web_dashboard import get_live_matches  # uses inplay feed with statistics
    except Exception as e:
        print(f"❌ Failed to import web_dashboard.get_live_matches: {e}")
        sys.exit(1)

    fixture_id = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    if fixture_id <= 0:
        print("❌ Provide a fixture id, e.g. 19392535")
        sys.exit(1)

    matches = get_live_matches()
    match = next((m for m in matches if m.get('match_id') == fixture_id), None)
    if not match:
        print(f"❌ Fixture {fixture_id} not found in current inplay set ({len(matches)} matches).")
        sys.exit(1)

    print(f"✅ Found fixture {fixture_id}: {match['home_team']} vs {match['away_team']} | minute {match['minute']}")
    stats: Dict[str, Dict[str, Any]] = match.get('statistics') or {}
    home = stats.get('home', {})
    away = stats.get('away', {})

    # Show the core keys we map from inplay
    keys = [
        'corners', 'shots_total', 'shots_on_target', 'shots_off_target',
        'dangerous_attacks', 'attacks', 'possession', 'crosses_total', 'offsides'
    ]

    print("\n📊 Live stats (home | away):")
    for k in keys:
        hv = home.get(k, '-')
        av = away.get(k, '-')
        print(f"  • {k:<18}: {hv} | {av}")


if __name__ == "__main__":
    main()

