#!/usr/bin/env python3
"""Compare harness .rows files position by position. Prints counts, never edits them."""
import pathlib
import sys

folder = pathlib.Path(__file__).resolve().parent


def load(name: str) -> list[tuple[str, str, str]]:
    rows = []
    for line in (folder / name).read_text().splitlines():
        if not line.strip():
            continue
        index, nodes, best, *_rest = line.split()
        rows.append((index, nodes, best))
    return rows


def main() -> int:
    left_name, right_name = sys.argv[1], sys.argv[2]
    left, right = load(left_name), load(right_name)
    if len(left) != len(right):
        print(f"{left_name} vs {right_name} length {len(left)} {len(right)} NOT_EQUAL")
        return 1
    differ = 0
    node_sum_l = 0
    node_sum_r = 0
    for (i1, n1, b1), (i2, n2, b2) in zip(left, right):
        if i1 != i2:
            print(f"index mismatch {i1} {i2}")
            return 1
        node_sum_l += int(n1)
        node_sum_r += int(n2)
        if n1 != n2 or b1 != b2:
            differ += 1
    same = len(left) - differ
    print(
        f"{left_name} vs {right_name} positions {len(left)} "
        f"same {same} differ {differ} sum_left {node_sum_l} sum_right {node_sum_r}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
