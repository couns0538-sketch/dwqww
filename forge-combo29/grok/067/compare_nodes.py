#!/usr/bin/env python3
"""Compare two measure_depth .nodes files position by position."""
import sys
from pathlib import Path

def load(path: Path):
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        index, nodes, move = line.split("\t")
        rows.append((int(index), int(nodes), move))
    return rows

def main() -> None:
    left = load(Path(sys.argv[1]))
    right = load(Path(sys.argv[2]))
    if len(left) != len(right):
        raise SystemExit(f"length {len(left)} != {len(right)}")
    differ = 0
    for (i, a, am), (j, b, bm) in zip(left, right):
        if i != j:
            raise SystemExit(f"index {i} != {j}")
        if a != b:
            differ += 1
            if differ <= 8:
                print(f"diff pos {i} nodes {a} vs {b} move {am} vs {bm}")
    print(f"N {len(left)} DIFFER {differ} SAME {len(left) - differ}")

if __name__ == "__main__":
    main()
