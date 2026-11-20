#!/usr/bin/env python3
"""Print per-position node rows and their sum from a harness transcript.

The node count of a search is the nodes field of the last info line whose
depth equals the requested depth, taken before that search's bestmove.
"""
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
    if len(sys.argv) < 3:
        raise SystemExit("usage: sum_nodes.py DEPTH TRANSCRIPT [TRANSCRIPT...]")
    depth = int(sys.argv[1])
    for name in sys.argv[2:]:
        counts = rows(Path(name).read_text(errors="replace"), depth)
        print(f"file {name}")
        print(f"positions {len(counts)}")
        print(f"sum {sum(counts)}")
        if counts:
            shown = " ".join(str(n) for n in counts[:3])
            print(f"first3 {shown}")
        print("rows")
        for index, nodes in enumerate(counts, start=1):
            print(f"{index} {nodes}")


if __name__ == "__main__":
    main()
