#!/usr/bin/env python3
"""Compare node rows parsed from two depth_set transcripts."""
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
    left = rows(Path(sys.argv[1]).read_text())
    right = rows(Path(sys.argv[2]).read_text())
    n = min(len(left), len(right))
    differ = [i for i in range(n) if left[i] != right[i]]
    print(f"left_n={len(left)} right_n={len(right)} compared={n} differ={len(differ)}")
    if differ[:12]:
        print("first_diffs " + " ".join(f"{i}:{left[i]}->{right[i]}" for i in differ[:12]))
    if len(left) == len(right) and not differ:
        print("IDENTICAL")

if __name__ == "__main__":
    main()
