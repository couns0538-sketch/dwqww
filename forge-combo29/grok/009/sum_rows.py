#!/usr/bin/env python3
"""Print count, sum, and the first three node counts from a .rows file."""
import sys
from pathlib import Path

def main() -> int:
    if len(sys.argv) < 2:
        print("usage: sum_rows.py ROWS [ROWS ...]", file=sys.stderr)
        return 2
    for arg in sys.argv[1:]:
        path = Path(arg)
        nodes = [int(line.split()[1]) for line in path.read_text().splitlines() if line.strip()]
        first = " ".join(str(n) for n in nodes[:3])
        print(f"{path.name} count {len(nodes)} sum {sum(nodes)} first {first}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
