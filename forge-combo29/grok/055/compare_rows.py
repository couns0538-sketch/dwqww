#!/usr/bin/env python3
"""Compare two measure.py tables. Prints sums and how many positions differ."""
import sys
from pathlib import Path


def load(path: Path):
    rows = {}
    summary = {}
    for raw in path.read_text().splitlines():
        parts = raw.split("\t")
        if parts[0] in {"sum", "count"}:
            summary[parts[0]] = parts[1]
            continue
        rows[int(parts[0])] = (int(parts[1]), parts[2], parts[3])
    return summary, rows


def main() -> int:
    left = Path(sys.argv[1])
    right = Path(sys.argv[2])
    ls, lr = load(left)
    rs, rr = load(right)
    keys = sorted(set(lr) | set(rr))
    node_diff = 0
    move_diff = 0
    missing = 0
    for key in keys:
        if key not in lr or key not in rr:
            missing += 1
            continue
        if lr[key][0] != rr[key][0]:
            node_diff += 1
        if lr[key][1] != rr[key][1]:
            move_diff += 1
    print(f"left {left.name} sum {ls.get('sum')} count {ls.get('count')}")
    print(f"right {right.name} sum {rs.get('sum')} count {rs.get('count')}")
    print(f"positions {len(keys)} node_diff {node_diff} move_diff {move_diff} missing {missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
