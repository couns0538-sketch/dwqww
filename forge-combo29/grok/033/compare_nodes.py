#!/usr/bin/env python3
"""Compare two raw search transcripts position by position."""
import sys
from pathlib import Path

from summarize_nodes import rows_of


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: compare_nodes.py LEFT.raw RIGHT.raw", file=sys.stderr)
        return 2
    left = rows_of(Path(sys.argv[1]).read_text(encoding="utf-8"))
    right = rows_of(Path(sys.argv[2]).read_text(encoding="utf-8"))
    print(f"left_count\t{len(left)}")
    print(f"right_count\t{len(right)}")
    if len(left) != len(right):
        print("length_mismatch\tyes")
        return 1
    differ = 0
    for index, (a, b) in enumerate(zip(left, right), start=1):
        if a[1] != b[1]:
            differ += 1
            if differ <= 20:
                print(f"diff\t{index}\tleft_nodes={a[1]}\tright_nodes={b[1]}\tleft_depth={a[0]}\tright_depth={b[0]}")
    print(f"differ\t{differ}")
    print(f"same\t{len(left) - differ}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
