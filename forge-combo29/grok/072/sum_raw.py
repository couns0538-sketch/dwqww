#!/usr/bin/env python3
"""Sum depth-N node counts from a search_set.py raw file. Reads the raw file only."""
import re
import sys
from pathlib import Path

def main() -> None:
    raw_path = Path(sys.argv[1])
    depth = int(sys.argv[2])
    text = raw_path.read_text(errors="replace")
    rows = []
    pending = None
    depth_re = re.compile(rf"^info depth {depth}(?: multipv \d+)? .* nodes (\d+) ")
    for line in text.splitlines():
        match = depth_re.match(line)
        if match:
            pending = int(match.group(1))
        elif line.startswith("bestmove ") and pending is not None:
            rows.append(pending)
            pending = None
        elif line.startswith("bestmove "):
            rows.append(-1)
    total = sum(n for n in rows if n >= 0)
    print(f"file {raw_path}")
    print(f"positions {len(rows)}")
    print(f"sum {total}")
    shown = rows[:3]
    print("first3 " + " ".join(str(n) for n in shown))
    missing = sum(1 for n in rows if n < 0)
    print(f"missing {missing}")

if __name__ == "__main__":
    main()
