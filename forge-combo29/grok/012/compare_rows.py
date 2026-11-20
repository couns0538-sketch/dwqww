#!/usr/bin/env python3
"""Compare two rows files position by position. Prints equals, differs, and the first mismatches."""
import sys
from pathlib import Path


def load(path: Path) -> list[tuple[str, str, str, str]]:
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        index, nodes, score, best, fen = line.split("\t", 4)
        rows.append((index, nodes, score, best, fen))
    return rows


left = load(Path(sys.argv[1]))
right = load(Path(sys.argv[2]))
if len(left) != len(right):
    raise SystemExit(f"length {len(left)} != {len(right)}")
differ = 0
shown = 0
for a, b in zip(left, right):
    if a[4] != b[4]:
        raise SystemExit(f"fen mismatch at {a[0]}")
    if a[1:] != b[1:]:
        differ += 1
        if shown < 8:
            print(f"differ {a[0]} nodes {a[1]} vs {b[1]} score {a[2]} vs {b[2]} best {a[3]} vs {b[3]}")
            shown += 1
print(f"positions {len(left)}")
print(f"differ {differ}")
print(f"equal {len(left) - differ}")
