#!/usr/bin/env python3
"""Print the fastchess results block and count finished games from a log."""
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: extract_match.py LOG", file=sys.stderr)
        return 2
    lines = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace").splitlines()
    finished = sum(1 for line in lines if line.startswith("Finished game "))
    print(f"finished_games\t{finished}")
    start = None
    for index, line in enumerate(lines):
        if line.startswith("Results of "):
            start = index
    if start is None:
        print("results\tmissing")
        return 1
    for line in lines[start:]:
        print(line)
        if line.startswith("Total Time:"):
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
