#!/usr/bin/env python3
"""Print the node sum and the first three node counts from a .nodes.txt file.

Each row is: index depth nodes
"""
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: sum_nodes.py <nodes.txt>", file=sys.stderr)
        return 2
    rows = []
    for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        index, depth, nodes = line.split()
        rows.append((int(index), int(depth), int(nodes)))
    total = sum(nodes for _, _, nodes in rows)
    print(f"file {sys.argv[1]}")
    print(f"positions {len(rows)}")
    print(f"sum {total}")
    shown = rows[:3]
    print("first3 " + " / ".join(str(nodes) for _, _, nodes in shown))
    depths = sorted({depth for _, depth, _ in rows})
    print("depths " + " ".join(str(depth) for depth in depths))
    return 0


if __name__ == "__main__":
    sys.exit(main())
