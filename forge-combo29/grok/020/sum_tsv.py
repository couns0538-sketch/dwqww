#!/usr/bin/env python3
"""Print node sums from measure_set.py tsv files. Paste this output; do not retype it."""
import sys
from pathlib import Path


def load(path: Path) -> list[int]:
    rows = []
    for line in path.read_text().splitlines()[1:]:
        if not line.strip():
            continue
        rows.append(int(line.split("\t")[1]))
    return rows


def main() -> int:
    for arg in sys.argv[1:]:
        path = Path(arg)
        rows = load(path)
        head = " ".join(str(n) for n in rows[:3])
        print(f"{path.name} n={len(rows)} sum={sum(rows)} first3={head}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
