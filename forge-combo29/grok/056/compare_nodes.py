#!/usr/bin/env python3
"""Compare two .nodes files position by position. Prints the table row."""
import sys
from pathlib import Path


def load(path: Path) -> list[int]:
    return [int(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    left = load(Path(sys.argv[1]))
    right = load(Path(sys.argv[2]))
    n = min(len(left), len(right))
    differ = [i for i in range(n) if left[i] != right[i]]
    print(f"left={sys.argv[1]} n={len(left)} sum={sum(left)}")
    print(f"right={sys.argv[2]} n={len(right)} sum={sum(right)}")
    print(f"compared={n} equal={n - len(differ)} differ={len(differ)}")
    if len(left) != len(right):
        print(f"length_mismatch {len(left)} {len(right)}")
    for i in differ[:20]:
        print(f"diff {i} {left[i]} {right[i]}")


if __name__ == "__main__":
    main()
