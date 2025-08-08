import sys
from typing import Any, Dict, List

from latecorners.sportmonks_client import SportmonksClient


def list_markets(fixture_id: int) -> None:
    client = SportmonksClient()

    # Primary in-play odds endpoint
    url_primary = f"{client.base_url}/odds/inplay/fixtures/{fixture_id}"
    params = {
        "api_token": client.api_key,
        "include": "bookmaker,markets,markets.selections",
    }

    try:
        resp = client.session.get(url_primary, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("data", [])
    except Exception as e:
        print(f"Failed to fetch primary in-play odds: {e}")
        data = []

    if not data:
        print("No odds data returned from primary endpoint.")

    def _print_payload(payload: List[Dict[str, Any]], tag: str) -> None:
        print(f"=== {tag} markets for fixture {fixture_id} ===")
        for bookmaker in payload:
            bookmaker_name = bookmaker.get("bookmaker", {}).get("name") or bookmaker.get("bookmaker_name") or "Unknown"
            print(f"Bookmaker: {bookmaker_name}")
            for market in bookmaker.get("markets", []):
                market_name = (market.get("market_name") or "").strip()
                print(f"  Market: {market_name}")
                selections = market.get("selections", [])
                for sel in selections:
                    label = (sel.get("label") or "").strip()
                    odds = sel.get("odds") or sel.get("value") or sel.get("decimal") or sel.get("price")
                    print(f"    - {label}: {odds}")

    if data:
        _print_payload(data, "Primary")

    # Fallback endpoint used elsewhere in codebase
    url_fb = f"{client.base_url}/odds/in-play/by-fixture/{fixture_id}"
    try:
        resp_fb = client.session.get(url_fb, params=params, timeout=10)
        resp_fb.raise_for_status()
        data_fb = resp_fb.json().get("data", [])
    except Exception as e:
        print(f"Failed to fetch fallback in-play odds: {e}")
        data_fb = []

    if data_fb:
        _print_payload(data_fb, "Fallback")
    else:
        print("No odds data returned from fallback endpoint.")

    # Flat in-play odds endpoint (market_description / label / value)
    url_flat = f"{client.base_url}/odds/inplay/fixtures/{fixture_id}"
    try:
        resp_flat = client.session.get(url_flat, params={"api_token": client.api_key}, timeout=10)
        resp_flat.raise_for_status()
        flat = resp_flat.json().get("data", [])
    except Exception as e:
        print(f"Failed to fetch flat in-play odds: {e}")
        flat = []

    if flat:
        print(f"=== Flat in-play odds for fixture {fixture_id} ===")
        for odd in flat:
            md = (odd.get("market_description") or "").strip()
            label = (odd.get("label") or "").strip()
            val = odd.get("value") or odd.get("odds") or odd.get("decimal") or odd.get("price")
            bm = odd.get("bookmaker_id")
            mid = odd.get("market_id")
            print(f"MarketID={mid} BM={bm} {md} :: {label} => {val}")
    else:
        print("No odds data returned from flat in-play endpoint.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m latecorners.list_inplay_markets <fixture_id>")
        sys.exit(1)
    try:
        fixture_id = int(sys.argv[1])
    except ValueError:
        print("Fixture id must be an integer.")
        sys.exit(1)
    list_markets(fixture_id)

