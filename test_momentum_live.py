#!/usr/bin/env python3
"""
Poll a live fixture repeatedly and print Momentum10 changes over time.

Usage:
  python latecorners/test_momentum_live.py 19458082 --polls 6 --interval 30

This uses the same mappings as the main system by leveraging SportmonksClient
and MomentumTracker.
"""

import argparse
import time
from typing import Optional, Dict

from sportmonks_client import SportmonksClient
from momentum_tracker import MomentumTracker


def find_live_match(client: SportmonksClient, fixture_id: int) -> Optional[Dict]:
    matches = client.get_live_matches(filter_by_minute=False) or []
    for m in matches:
        if m.get('id') == fixture_id:
            return m
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Momentum10 live tester")
    parser.add_argument("fixture_id", type=int, help="Fixture ID to track")
    parser.add_argument("--polls", type=int, default=60, help="Max polls (default 60)")
    parser.add_argument("--interval", type=int, default=15, help="Seconds between polls (default 15)")
    parser.add_argument("--visual", action="store_true", help="Render simple ASCII bars for momentum")
    parser.add_argument("--no-skip-duplicates", action="store_true", help="Print even if minute hasn't advanced")
    args = parser.parse_args()

    client = SportmonksClient()
    tracker = MomentumTracker(window_minutes=10)

    print(
        f"Tracking fixture {args.fixture_id} up to {args.polls} polls (every {args.interval}s); "
        + ("printing every poll" if args.no_skip_duplicates else "printing only when minute advances")
    )

    last_printed_minute = None

    for i in range(args.polls):
        raw = find_live_match(client, args.fixture_id)
        if not raw:
            print("Fixture not found in current inplay set. Will retry...")
        else:
            stats = client._parse_live_match_data(raw)
            if stats:
                # Skip duplicate minute to show minute-by-minute evolution
                if (not args.no_skip_duplicates) and last_printed_minute is not None and stats.minute == last_printed_minute:
                    if i < args.polls - 1:
                        time.sleep(args.interval)
                        continue
                # add snapshot
                tracker.add_snapshot(
                    fixture_id=stats.fixture_id,
                    minute=stats.minute,
                    home={
                        'shots_on_target': stats.shots_on_target.get('home', 0),
                        'shots_off_target': stats.shots_off_target.get('home', 0),
                        'dangerous_attacks': stats.dangerous_attacks.get('home', 0),
                        'possession': stats.possession.get('home', 0),
                    },
                    away={
                        'shots_on_target': stats.shots_on_target.get('away', 0),
                        'shots_off_target': stats.shots_off_target.get('away', 0),
                        'dangerous_attacks': stats.dangerous_attacks.get('away', 0),
                        'possession': stats.possession.get('away', 0),
                    },
                )
                scores = tracker.compute_scores(stats.fixture_id)
                hm = scores['home']
                am = scores['away']
                coverage = max(hm.get('window_covered', 0), am.get('window_covered', 0))
                combined = hm['total'] + am['total']
                # ASCII-only output for Windows consoles
                base = (
                    "Minute {} | Score {}-{} | Window {}m\n"
                    "  HOME: {} pts (SOT {}, SOFF {}, DA {}, POS {})\n"
                    "  AWAY: {} pts (SOT {}, SOFF {}, DA {}, POS {})\n"
                    "  Combined: {} pts"
                ).format(
                    stats.minute,
                    stats.home_score,
                    stats.away_score,
                    coverage,
                    hm['total'], hm['on_target_points'], hm['off_target_points'], hm['dangerous_points'], hm['possession_points'],
                    am['total'], am['on_target_points'], am['off_target_points'], am['dangerous_points'], am['possession_points'],
                    combined,
                )

                if args.visual:
                    # Simple bar chart (1 char per 2 points, capped to 50 chars)
                    scale = 2
                    max_len = 50
                    hbar = "#" * min(max_len, hm['total'] // scale)
                    abar = "#" * min(max_len, am['total'] // scale)
                    cbar = "#" * min(max_len, combined // scale)
                    base += "\n  HOME [" + hbar.ljust(max_len) + "]\n"
                    base += "  AWAY [" + abar.ljust(max_len) + "]\n"
                    base += "     Σ [" + cbar.ljust(max_len) + "]\n"

                print(base)
                last_printed_minute = stats.minute
            else:
                print("Parse error for live match data")

        if i < args.polls - 1:
            time.sleep(args.interval)


if __name__ == "__main__":
    main()

