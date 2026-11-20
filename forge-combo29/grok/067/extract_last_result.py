#!/usr/bin/env python3
"""Print the last fastchess Results block, including the Finished match line."""
import sys
from pathlib import Path

def main() -> None:
    lines = Path(sys.argv[1]).read_text().splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith("Results of ")]
    if not starts:
        raise SystemExit("no Results block")
    start = starts[-1]
    end = len(lines)
    for i in range(start, len(lines)):
        if lines[i].startswith("Finished match"):
            end = i + 1
            break
    print("\n".join(lines[start:end]))

if __name__ == "__main__":
    main()
