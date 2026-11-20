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
    elo_hits = re.findall(r"(?<![A-Za-z])Elo:\s*([+-]?\d+(?:\.\d+)?)\s*\+/-\s*([+-]?\d+(?:\.\d+)?)", text)
    game_hits = re.findall(r"Games:\s*(\d+),\s*Wins:\s*(\d+),\s*Losses:\s*(\d+),\s*Draws:\s*(\d+)", text)
    if not elo_hits or not game_hits:
        print("MISSING result line")
        return 1
    elo = elo_hits[-1]
    games = game_hits[-1]
    point = float(elo[0])
    err = float(elo[1])
    print(f"elo {point}")
    print(f"err {err}")
    print(f"elo_low {point - err}")
    print(f"elo_high {point + err}")
    print(f"games {games[0]}")
    print(f"wins {games[1]}")
    print(f"losses {games[2]}")
    print(f"draws {games[3]}")
    whole_below_zero = (point + err) < 0
    print(f"whole_interval_below_0 {str(whole_below_zero).lower()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
