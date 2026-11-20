#!/usr/bin/env python3
"""Compare partner 'index nodes' rows with this harness's one-number rows."""

import sys
from pathlib import Path


def theirs(path: Path) -> list[int]:
    rows = []
    for line in path.read_text().splitlines():
        parts = line.split()
        if not parts:
            continue
        rows.append(int(parts[-1]))
    return rows


def mine(path: Path) -> list[int]:
    return [int(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> int:
    left = theirs(Path(sys.argv[1]))
    right = mine(Path(sys.argv[2]))
    n = min(len(left), len(right))
    differ = [i for i in range(n) if left[i] != right[i]]
    print(f"partner rows {len(left)} sum {sum(left)}")
    print(f"mine rows {len(right)} sum {sum(right)}")
    print(f"compared {n}")
    print(f"differ {len(differ)}")
    for index in differ[:20]:
        print(f"row {index} partner {left[index]} mine {right[index]}")
    if len(left) != len(right):
        print(f"length mismatch {len(left)} {len(right)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
