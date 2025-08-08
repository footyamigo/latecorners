#!/usr/bin/env python3
"""
Quick checker for SportMonks fixture statistics focusing on shot-zone metrics:
- shots_inside_box (type_id 49)
- shots_outside_box (type_id 50)
- shots_blocked (type_id 58)

Usage:
  python latecorners/test_shot_zones_fixture.py 19392535

Requires environment variable SPORTMONKS_API_KEY.
"""

import os
import sys
import json
from typing import Dict, Any

import requests
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass


TYPE_NAMES: Dict[int, str] = {
    49: "shots_inside_box",
    50: "shots_outside_box",
    58: "shots_blocked",
    41: "shots_off_target",
    42: "shots_total",
    86: "shots_on_target",
    33: "corners",
    34: "possession",
    44: "dangerous_attacks",
    45: "attacks",
}


def extract_value_and_location(stat: Dict[str, Any]) -> tuple[str, int]:
    """Return (location, value) from a statistics row supporting both formats."""
    location = stat.get("location")
    if not location:
        # Fallback to participant_id mapping if provided in this endpoint (older format)
        participant_id = stat.get("participant_id")
        location = "home" if participant_id == stat.get("home_participant_id") else "away"
    value = stat.get("value", stat.get("data", {}).get("value", 0))
    return location or "unknown", int(value or 0)


def main() -> None:
    api_key = os.getenv("SPORTMONKS_API_KEY", "")
    if not api_key:
        print("❌ Missing SPORTMONKS_API_KEY in environment")
        sys.exit(1)

    fixture_id = sys.argv[1] if len(sys.argv) > 1 else "19392535"
    try:
        int(fixture_id)
    except ValueError:
        print("❌ Invalid fixture id. Provide a numeric ID, e.g. 19392535")
        sys.exit(1)

    url = f"https://api.sportmonks.com/v3/football/fixtures/{fixture_id}"
    params = {
        "api_token": api_key,
        # Include nested period statistics too to check for possession coverage there
        "include": "statistics;participants;state;periods;periods.statistics",
    }
    print(f"🌐 Fetching fixture {fixture_id} statistics...")
    resp = requests.get(url, params=params, timeout=25)
    try:
        resp.raise_for_status()
    except Exception as e:
        print(f"❌ Request failed: {e}")
        print(f"Response text: {resp.text[:500]}")
        sys.exit(1)

    data = resp.json().get("data")
    if not data:
        print("❌ No data in response")
        print(json.dumps(resp.json(), indent=2)[:1000])
        sys.exit(1)

    participants = data.get("participants", [])
    home_name = away_name = "Unknown"
    for p in participants:
        loc = p.get("meta", {}).get("location")
        if loc == "home":
            home_name = p.get("name", "Home")
        elif loc == "away":
            away_name = p.get("name", "Away")

    # Determine live minute if available
    minute = 0
    for period in data.get("periods", []):
        if period.get("ticking", False):
            minute = int(period.get("minutes", 0))
            desc = (period.get("description") or "").lower()
            if "2nd" in desc or "second" in desc:
                minute += 45
            break

    stats = data.get("statistics", [])
    print(f"✅ Retrieved {len(stats)} statistics entries | {home_name} vs {away_name} | minute {minute}")

    # Aggregate by type_id -> {home:value, away:value}
    by_type: Dict[int, Dict[str, int]] = {}
    for s in stats:
        type_id = int(s.get("type_id"))
        location, value = extract_value_and_location(s)
        if type_id not in by_type:
            by_type[type_id] = {"home": 0, "away": 0}
        if location in ("home", "away"):
            by_type[type_id][location] = value

    focus_ids = [49, 50, 58]
    print("\n🎯 Focus shot-zone stats (home | away):")
    for tid in focus_ids:
        name = TYPE_NAMES.get(tid, f"type_{tid}")
        vals = by_type.get(tid)
        if vals:
            print(f"   • {name:<18} (id {tid}): {vals['home']} | {vals['away']}")
        else:
            print(f"   • {name:<18} (id {tid}): NOT PRESENT in statistics")

    # Helpful context
    print("\n📋 Also present (sample):")
    for tid in sorted(set(by_type.keys()) & {41, 42, 44, 45, 86, 33, 34}):
        name = TYPE_NAMES.get(tid, str(tid))
        print(f"   • {name:<18} (id {tid}): {by_type[tid]['home']} | {by_type[tid]['away']}")

    # Show raw rows for the focus types for debugging
    print("\n🔍 Raw entries for focus types (first occurrence each):")
    seen = set()
    for s in stats:
        tid = int(s.get("type_id"))
        if tid in focus_ids and tid not in seen:
            print(json.dumps(s, indent=2))
            seen.add(tid)
        if len(seen) == len(focus_ids):
            break

    # Period-level possession probe
    periods = data.get("periods", [])
    if periods:
        print("\n🧪 Periods statistics (probing for possession):")
        for p in periods:
            pdesc = p.get("description", "")
            pstats = p.get("statistics", [])
            if pstats:
                has_pos = any(int(ps.get("type_id", 0)) in (34, 45, 52) for ps in pstats)
                if has_pos:
                    print(f"  Period: {pdesc} -> found potential possession types among {[ps.get('type_id') for ps in pstats]}")
                    for ps in pstats:
                        if int(ps.get("type_id", 0)) in (34, 45, 52):
                            print("   ", json.dumps(ps, indent=2))


if __name__ == "__main__":
    main()

