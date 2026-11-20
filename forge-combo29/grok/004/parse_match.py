#!/usr/bin/env python3
"""Print the last Elo and game-count lines from a fastchess log."""
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: parse_match.py match.log")
    lines = Path(sys.argv[1]).read_text(errors="replace").splitlines()
    elo = [line for line in lines if line.startswith("Elo:")]
    games = [line for line in lines if line.startswith("Games:")]
    finished = sum(1 for line in lines if line.startswith("Finished game "))
    print(f"finished_lines {finished}")
    if elo:
        print(elo[-1])
    if games:
        print(games[-1])
    if not elo:
        print("no Elo line yet")


if __name__ == "__main__":
    main()
