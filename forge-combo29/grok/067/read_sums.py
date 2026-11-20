#!/usr/bin/env python3
"""Print node sums and the first three counts from measure_depth .nodes files."""
import sys
from pathlib import Path

def counts(path: Path):
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rows.append(int(line.split("\t")[1]))
    return rows

def main() -> None:
    folder = Path(sys.argv[1])
    for name in sys.argv[2:]:
        values = counts(folder / name)
        first = " ".join(str(value) for value in values[:3])
        print(f"{name} N {len(values)} SUM {sum(values)} FIRST {first}")

if __name__ == "__main__":
    main()
