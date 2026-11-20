#!/usr/bin/env python3
"""Compare two depth transcripts position by position."""
from __future__ import annotations

import sys
from pathlib import Path


def rows(text: str, depth: int) -> list[int]:
    counts: list[int] = []
    pending: int | None = None
    for line in text.splitlines():
        if line.startswith("info depth "):
            parts = line.split()
            try:
                got_depth = int(parts[2])
                nodes = int(parts[parts.index("nodes") + 1])
            except (ValueError, IndexError):
                continue
            if got_depth == depth:
                pending = nodes
        elif line.startswith("bestmove"):
            if pending is None:
                raise SystemExit(f"bestmove with no depth-{depth} info: {line}")
            counts.append(pending)
            pending = None
    if pending is not None:
        raise SystemExit("transcript ended after info and before bestmove")
    return counts


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: compare_rows.py DEPTH LEFT.txt RIGHT.txt")
    depth = int(sys.argv[1])
    left = rows(Path(sys.argv[2]).read_text(errors="replace"), depth)
    right = rows(Path(sys.argv[3]).read_text(errors="replace"), depth)
    if len(left) != len(right):
        raise SystemExit(f"length {len(left)} vs {len(right)}")
    differ = [i for i, (a, b) in enumerate(zip(left, right), start=1) if a != b]
    print(f"positions {len(left)}")
    print(f"differ {len(differ)}")
    print(f"left_sum {sum(left)}")
    print(f"right_sum {sum(right)}")
    for index in differ[:40]:
        print(f"{index} {left[index - 1]} {right[index - 1]}")
    if len(differ) > 40:
        print(f"... {len(differ) - 40} more")


if __name__ == "__main__":
    main()
