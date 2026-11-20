#!/usr/bin/env python3
"""Compare two node files position by position. Paste this output."""
import pathlib
import sys


def load(path: pathlib.Path) -> list[tuple[str, str, str]]:
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        index, nodes, move, *_ = line.split("\t")
        rows.append((index, nodes, move))
    return rows


def main() -> int:
    left = load(pathlib.Path(sys.argv[1]))
    right = load(pathlib.Path(sys.argv[2]))
    if len(left) != len(right):
        print(f"length {len(left)} {len(right)}")
        return 1
    differ = 0
    for (i, a, am), (j, b, bm) in zip(left, right):
        if i != j:
            print(f"index mismatch {i} {j}")
            return 1
        if a != b or am != bm:
            differ += 1
    print(f"positions {len(left)}")
    print(f"differ {differ}")
    print(f"same {len(left) - differ}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
