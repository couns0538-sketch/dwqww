#!/usr/bin/env python3
"""Compare two .nodes files position by position. Prints how many differ."""
import sys
from pathlib import Path


def rows(path: Path) -> list[tuple[int, int]]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("SUM"):
            continue
        index, nodes = line.split()
        out.append((int(index), int(nodes)))
    return out


def main() -> int:
    left = rows(Path(sys.argv[1]))
    right = rows(Path(sys.argv[2]))
    if len(left) != len(right):
        print(f"LENGTH {len(left)} {len(right)}")
        return 1
    mismatches = []
    for (i, a), (j, b) in zip(left, right):
        if i != j:
            print(f"INDEX {i} {j}")
            return 1
        if a != b:
            mismatches.append((i, a, b))
    print(f"positions {len(left)}")
    print(f"differ {len(mismatches)} of {len(left)}")
    print(f"sum_left {sum(a for _, a in left)}")
    print(f"sum_right {sum(b for _, b in right)}")
    for index, a, b in mismatches[:12]:
        print(f"pos {index} left {a} right {b}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
