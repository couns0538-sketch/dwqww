#!/usr/bin/env python3
"""Print node sums from harness .nodes.txt files. No hand-typed totals."""
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: sum_nodes.py file.nodes.txt ...")
    for name in sys.argv[1:]:
        path = Path(name)
        counts = [int(line) for line in path.read_text().splitlines() if line.strip()]
        head = " ".join(str(n) for n in counts[:3])
        print(f"{path.name} positions {len(counts)} sum {sum(counts)} first {head}")


if __name__ == "__main__":
    main()
