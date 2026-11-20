#!/usr/bin/env python3
"""Print a node table from a .rows.txt file written by run_depth.py."""
import sys
from pathlib import Path

def main() -> int:
    if len(sys.argv) < 2:
        print("usage: sum_rows.py ROWS [ROWS ...]", file=sys.stderr)
        return 2
    print("file\tpositions\tsum\tfirst3")
    for arg in sys.argv[1:]:
        rows = []
        for line in Path(arg).read_text().splitlines():
            if not line.strip():
                continue
            parts = line.split()
            rows.append(int(parts[1]))
        first = "/".join(str(n) for n in rows[:3])
        print(f"{arg}\t{len(rows)}\t{sum(rows)}\t{first}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
