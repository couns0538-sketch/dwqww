#!/usr/bin/env python3
"""Read raw O-run transcripts and print sums, first three, and differences.

Usage: python3 summarize_o.py <label=raw.txt> ...
The first file is the reference (exe B). Later files are compared to it.
A position's nodes are the nodes field of the last 'info depth' line before
that position's bestmove.
"""
import sys
from pathlib import Path


def positions(path):
    nodes = []
    last = None
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("info depth ") and " nodes " in line:
            parts = line.split()
            last = int(parts[parts.index("nodes") + 1])
        elif line.startswith("bestmove"):
            if last is None:
                sys.exit(f"STOP: bestmove without an info depth line in {path}")
            nodes.append(last)
            last = None
    return nodes


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    parsed = []
    for arg in sys.argv[1:]:
        label, path = arg.split("=", 1)
        nodes = positions(path)
        parsed.append((label, nodes))
        head = " / ".join(str(n) for n in nodes[:3])
        print(f"{label} positions {len(nodes)} sum {sum(nodes)} first {head}")
    ref_label, ref = parsed[0]
    for label, nodes in parsed[1:]:
        if len(nodes) != len(ref):
            print(f"{label} length {len(nodes)} differs from {ref_label} length {len(ref)}")
            continue
        differ = sum(1 for a, b in zip(nodes, ref) if a != b)
        print(f"{label} differ_from_{ref_label} {differ}")


if __name__ == "__main__":
    main()
