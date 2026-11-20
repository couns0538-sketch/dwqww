#!/usr/bin/env python3
"""Print position counts and node sums from harness .txt files. Reads raw rows only."""
import sys
from pathlib import Path

def summarize(path: Path) -> None:
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        rows.append(int(parts[1]))
    first = " ".join(str(n) for n in rows[:3])
    print(f"{path.name} positions {len(rows)} sum {sum(rows)} first3 {first}")

for arg in sys.argv[1:]:
    summarize(Path(arg))
