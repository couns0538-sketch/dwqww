#!/usr/bin/env python3
"""Read the raw O transcripts and print sums, the first three node counts, and how many differ."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def nodes_of(path):
    last_info = None
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("info "):
            last_info = line
        elif line.startswith("bestmove "):
            if last_info is None or " nodes " not in f" {last_info} ":
                sys.exit(f"STOP: {path.name} bestmove without a nodes info line: {last_info}")
            parts = last_info.split()
            out.append(int(parts[parts.index("nodes") + 1]))
            last_info = None
    if len(out) != 200:
        sys.exit(f"STOP: {path.name} has {len(out)} positions, expected 200")
    return out


def show(label, nodes):
    print(f"{label} sum {sum(nodes)} first {nodes[0]} {nodes[1]} {nodes[2]}")


def main():
    b = nodes_of(ROOT / "o_B.txt")
    off = nodes_of(ROOT / "o_Poff.txt")
    on = nodes_of(ROOT / "o_Pon.txt")
    show("B", b)
    show("Poff", off)
    show("Pon", on)
    differ_off = sum(1 for x, y in zip(b, off) if x != y)
    differ_on = sum(1 for x, y in zip(b, on) if x != y)
    print(f"Poff positions differing from B: {differ_off}")
    print(f"Pon positions differing from B: {differ_on}")
    print(f"Poff identical to B: {'yes' if off == b else 'no'}")


if __name__ == "__main__":
    main()
