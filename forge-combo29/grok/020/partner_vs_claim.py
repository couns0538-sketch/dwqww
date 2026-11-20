#!/usr/bin/env python3
"""Compare my partner-build O nodes tsv to the partner's published node list."""
import sys
from pathlib import Path


def mine(path: Path) -> list[int]:
    rows = []
    for line in path.read_text().splitlines()[1:]:
        if line.strip():
            rows.append(int(line.split("\t")[1]))
    return rows


def theirs(path: Path) -> list[int]:
    rows = []
    for line in path.read_text().splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            rows.append(int(parts[1]))
    return rows


def main() -> int:
    left = mine(Path(sys.argv[1]))
    right = theirs(Path(sys.argv[2]))
    print(f"measured {len(left)} sum {sum(left)}")
    print(f"claimed {len(right)} sum {sum(right)}")
    n = min(len(left), len(right))
    differ = sum(1 for i in range(n) if left[i] != right[i])
    print(f"differ {differ} of {n}")
    if len(left) != len(right):
        print(f"length_mismatch {len(left)} {len(right)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
