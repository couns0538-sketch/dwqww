#!/usr/bin/env python3
"""Compare two depth-sum .rows files. Prints equal count, differ count, and the sums."""
import sys
from pathlib import Path


def load(path: Path) -> list[tuple[str, str, str]]:
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        index, nodes, best, fen = line.split(" ", 3)
        rows.append((nodes, best, fen))
    return rows


def main() -> None:
    left = load(Path(sys.argv[1]))
    right = load(Path(sys.argv[2]))
    if len(left) != len(right):
        raise SystemExit(f"length {len(left)} != {len(right)}")
    differ = 0
    node_differ = 0
    move_differ = 0
    for (ln, lb, lf), (rn, rb, rf) in zip(left, right):
        if lf != rf:
            raise SystemExit("fen mismatch")
        if ln != rn or lb != rb:
            differ += 1
        if ln != rn:
            node_differ += 1
        if lb != rb:
            move_differ += 1
    sum_l = sum(int(n) for n, _, _ in left)
    sum_r = sum(int(n) for n, _, _ in right)
    print(f"positions {len(left)}")
    print(f"equal {len(left) - differ}")
    print(f"differ {differ}")
    print(f"nodes_differ {node_differ}")
    print(f"bestmove_differ {move_differ}")
    print(f"sum_left {sum_l}")
    print(f"sum_right {sum_r}")


if __name__ == "__main__":
    main()
