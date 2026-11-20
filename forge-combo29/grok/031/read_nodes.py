#!/usr/bin/env python3
"""Read a measure_set.py transcript and print one node count per position."""
import sys
from pathlib import Path


def nodes_of(chunk: list[str]) -> tuple[int, int]:
    depth = -1
    nodes = -1
    for line in chunk:
        if not line.startswith("info depth "):
            continue
        parts = line.split()
        if "depth" not in parts or "nodes" not in parts:
            continue
        depth = int(parts[parts.index("depth") + 1])
        nodes = int(parts[parts.index("nodes") + 1])
    return depth, nodes


def main() -> int:
    path = Path(sys.argv[1])
    lines = path.read_text().splitlines()
    chunks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        current.append(line)
        if line.startswith("bestmove "):
            chunks.append(current)
            current = []
    total = 0
    bad = 0
    print("index\tdepth\tnodes")
    for index, chunk in enumerate(chunks, start=1):
        depth, nodes = nodes_of(chunk)
        if nodes < 0:
            bad += 1
            print(f"{index}\tMISSING\tMISSING")
            continue
        total += nodes
        print(f"{index}\t{depth}\t{nodes}")
    print(f"positions\t{len(chunks)}")
    print(f"sum\t{total}")
    if chunks:
        first = []
        for chunk in chunks[:3]:
            _depth, nodes = nodes_of(chunk)
            first.append(str(nodes))
        print("first3\t" + "\t".join(first))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
