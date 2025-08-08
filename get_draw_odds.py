#!/usr/bin/env python3
import sys
from latecorners.sportmonks_client import SportmonksClient

def main():
    if len(sys.argv) < 2:
        print("Usage: python latecorners/get_draw_odds.py <fixture_id>")
        sys.exit(1)
    fixture_id = int(sys.argv[1])
    client = SportmonksClient()
    odds = client.get_live_draw_odds(fixture_id)
    print(odds)

if __name__ == "__main__":
    main()

