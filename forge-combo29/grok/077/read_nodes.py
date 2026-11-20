#!/usr/bin/env python3
"""Print a node-sum table from .nodes files. Paste this output; do not retype it."""
import sys
from pathlib import Path


def load(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        index, nodes = line.split()
        rows.append((int(index), int(nodes)))
    rows.sort()
    return rows


def main():
    left = load(sys.argv[1])
    print(f"file {sys.argv[1]} count {len(left)} sum {sum(n for _, n in left)}")
    if left:
        shown = " ".join(str(n) for _, n in left[:3])
        print(f"first3 {shown}")
    if len(sys.argv) > 2:
        right = load(sys.argv[2])
        by_r = dict(right)
        differ = 0
        missing = 0
        for index, nodes in left:
            other = by_r.get(index)
            if other is None:
                missing += 1
            elif other != nodes:
                differ += 1
        print(f"against {sys.argv[2]} differ {differ} of {len(left)} missing {missing}")


if __name__ == "__main__":
    main()
