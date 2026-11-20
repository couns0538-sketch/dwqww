#!/usr/bin/env python3
"""Print node sums and the first three rows from a .nodes file."""
import sys
from pathlib import Path

path = Path(sys.argv[1])
rows = [int(line) for line in path.read_text().splitlines() if line.strip()]
print(f"file {path.name}")
print(f"n {len(rows)}")
print(f"sum {sum(rows)}")
print("first3 " + " ".join(str(n) for n in rows[:3]))
