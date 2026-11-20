#!/usr/bin/env python3
"""Print Elo, the error bar, and the game count from a fastchess result file."""
import re
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: parse_match.py <fastchess.out>", file=sys.stderr)
        return 2
    text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    elo = re.search(r"Elo:\s*([+-]?\d+(?:\.\d+)?)\s*\+/-\s*([+-]?\d+(?:\.\d+)?)", text)
    games = re.search(r"Games:\s*(\d+),\s*Wins:\s*(\d+),\s*Losses:\s*(\d+),\s*Draws:\s*(\d+)", text)
    if elo is None or games is None:
        print("MISSING result line")
        return 1
    point = float(elo.group(1))
    err = float(elo.group(2))
    print(f"elo {point}")
    print(f"err {err}")
    print(f"elo_low {point - err}")
    print(f"elo_high {point + err}")
    print(f"games {games.group(1)}")
    print(f"wins {games.group(2)}")
    print(f"losses {games.group(3)}")
    print(f"draws {games.group(4)}")
    whole_below_zero = (point + err) < 0
    print(f"whole_interval_below_0 {str(whole_below_zero).lower()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
