#!/usr/bin/env python3
"""Print the last fastchess Results block and count PGN games."""
import sys
from pathlib import Path


def main() -> int:
    log = Path(sys.argv[1]).read_text().splitlines()
    pgn = Path(sys.argv[2]).read_text().splitlines()
    start = None
    for index, line in enumerate(log):
        if line.startswith("Results of "):
            start = index
    if start is None:
        print("no results block")
        return 1
    for line in log[start:]:
        if line.startswith("fastchess_exit="):
            print(line)
            break
        print(line)
    events = sum(1 for line in pgn if line.startswith("[Event "))
    results = sum(1 for line in pgn if line.startswith("[Result "))
    print(f"pgn_events {events}")
    print(f"pgn_results {results}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
