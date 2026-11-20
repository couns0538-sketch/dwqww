#!/usr/bin/env python3
"""Read a depth_set.py transcript and print index, nodes, and the sum."""
import sys
from pathlib import Path

def rows(text: str) -> list[int]:
    nodes: list[int] = []
    pending = None
    for line in text.splitlines():
        if line.startswith("info depth "):
            parts = line.split()
            if "nodes" in parts:
                pending = int(parts[parts.index("nodes") + 1])
        elif line.startswith("bestmove ") and pending is not None:
            nodes.append(pending)
            pending = None
    return nodes

def main() -> None:
    for path_text in sys.argv[1:]:
        path = Path(path_text)
        got = rows(path.read_text())
        print(f"{path.name} n={len(got)} sum={sum(got)} first3={got[:3]}")

if __name__ == "__main__":
    main()
