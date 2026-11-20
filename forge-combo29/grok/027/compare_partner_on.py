#!/usr/bin/env python3
"""Compare my partner-on nodes file with the partner's claimed rows.

Mine is 1-based and tab-separated: index, nodes, best, score, fen.
Theirs is 0-based and space-separated: index, nodes.
"""
import sys
from pathlib import Path


def mine(path: Path) -> list[int]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(int(line.split("\t")[1]))
    return rows


def theirs(path: Path) -> list[int]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(int(line.split()[1]))
    return rows


def main() -> int:
    left = mine(Path(sys.argv[1]))
    right = theirs(Path(sys.argv[2]))
    n = min(len(left), len(right))
    differ = sum(1 for i in range(n) if left[i] != right[i])
    print(f"mine={sys.argv[1]} n={len(left)} sum={sum(left)}")
    print(f"theirs={sys.argv[2]} n={len(right)} sum={sum(right)}")
    print(f"compared={n}")
    print(f"differ={differ}")
    print(f"same_length={str(len(left) == len(right)).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
