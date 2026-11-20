#!/usr/bin/env python3
"""Print the last fastchess results block and the finished-game count."""
import sys
from pathlib import Path


def main() -> int:
    text = Path(sys.argv[1]).read_text(errors="replace")
    finished = sum(1 for line in text.splitlines() if line.startswith("Finished game "))
    print(f"finished_lines {finished}")
    start = text.rfind("Results of ")
    if start < 0:
        print("no results block")
        return 1
    print(text[start:].rstrip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
