#!/usr/bin/env python3
"""Compare two node-row files written by sum_nodes.py. Prints counts only."""
import sys
from pathlib import Path


def load(path: Path) -> list[int]:
    return [int(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> int:
    left = load(Path(sys.argv[1]))
    right = load(Path(sys.argv[2]))
    name = sys.argv[3] if len(sys.argv) > 3 else "compare"
    if len(left) != len(right):
        print(f"{name} length {len(left)} vs {len(right)} DIFFER")
        return 1
    differ = [i for i, (a, b) in enumerate(zip(left, right)) if a != b]
    print(f"{name} positions {len(left)} differ {len(differ)} equal {len(left) - len(differ)}")
    if differ[:8]:
        shown = " ".join(f"{i}:{left[i]}->{right[i]}" for i in differ[:8])
        print(f"{name} first_diffs {shown}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
