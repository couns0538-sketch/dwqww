#!/usr/bin/env python3
"""Compare my depth_sum tsv to a partner rows file (header, 1-based index)."""
import sys
from pathlib import Path


def load_tsv(path: Path):
    rows = []
    for line in path.read_text().splitlines():
        parts = line.split("\t")
        rows.append(int(parts[1]))
    return rows


def load_partner(path: Path):
    rows = []
    for line in path.read_text().splitlines():
        if line.startswith("index"):
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        rows.append(int(parts[1]))
    return rows


def main() -> int:
    mine = load_tsv(Path(sys.argv[1]))
    theirs = load_partner(Path(sys.argv[2]))
    n = min(len(mine), len(theirs))
    diff = sum(1 for i in range(n) if mine[i] != theirs[i])
    print(f"rows {len(mine)} {len(theirs)}")
    print(f"node_diff {diff} of {n}")
    print(f"sum {sum(mine)} {sum(theirs)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
