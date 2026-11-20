#!/usr/bin/env python3
"""Compare my measured rows to a partner file of one node count per line."""
import sys
from pathlib import Path


def measured(path: Path):
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        index, nodes, _rest = line.split("\t", 2)
        rows.append(int(nodes))
    return rows


def claimed(path: Path):
    return [int(line.strip()) for line in path.read_text().splitlines() if line.strip()]


mine = measured(Path(sys.argv[1]))
theirs = claimed(Path(sys.argv[2]))
if len(mine) != len(theirs):
    raise SystemExit(f"length {len(mine)} != {len(theirs)}")
differ = sum(1 for a, b in zip(mine, theirs) if a != b)
print(f"measured={sys.argv[1]} claimed={sys.argv[2]} n={len(mine)} differ={differ} measured_sum={sum(mine)} claimed_sum={sum(theirs)}")
