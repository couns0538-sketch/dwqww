#!/usr/bin/env python3
"""Compare my search_set tsv nodes to a claimed index/nodes table."""
import sys
from pathlib import Path


def mine(path: Path):
    rows = []
    for line in path.read_text().splitlines()[1:]:
        if not line.strip():
            continue
        index, nodes, score, fen = line.split("\t", 3)
        rows.append((int(index), int(nodes)))
    return rows


def claimed(path: Path):
    rows = []
    for line in path.read_text().splitlines()[1:]:
        if not line.strip():
            continue
        parts = line.split("\t")
        rows.append((int(parts[0]), int(parts[1])))
    return rows


left = mine(Path(sys.argv[1]))
right = claimed(Path(sys.argv[2]))
if len(left) != len(right):
    raise SystemExit(f"length {len(left)} != {len(right)}")
differ = [(i, a, b) for (i, a), (j, b) in zip(left, right) if i != j or a != b]
if any(i != j for (i, _), (j, _) in zip(left, right)):
    raise SystemExit("index mismatch")
print(f"positions {len(left)}")
print(f"differ {len(differ)}")
print(f"same {len(left) - len(differ)}")
print(f"my_sum {sum(n for _, n in left)}")
print(f"claimed_sum {sum(n for _, n in right)}")
for i, a, b in differ[:15]:
    print(f"pos {i} mine {a} claimed {b}")
