#!/usr/bin/env python3
"""Print the fastchess results block and the finished-game count."""
import sys
from pathlib import Path

def main() -> int:
    if len(sys.argv) != 2:
        print("usage: summarize_match.py LOG", file=sys.stderr)
        return 2
    text = Path(sys.argv[1]).read_text()
    finished = sum(1 for line in text.splitlines() if line.startswith("Finished game "))
    print(f"finished_games {finished}")
    keep = False
    for line in text.splitlines():
        if line.startswith("Results of "):
            keep = True
        if keep:
            print(line)
        if keep and line.startswith("Finished match"):
            break
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
