#!/usr/bin/env python3
"""Read O-run raw engine transcripts and print sums, first three, and differences."""
import sys


def nodes_from_raw(path):
    counts = []
    pending = []
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.rstrip("\n")
        if line.startswith("info "):
            pending.append(line)
        elif line.startswith("bestmove"):
            if not pending or " nodes " not in pending[-1]:
                sys.exit(f"STOP: {path} bestmove {len(counts) + 1} has no nodes info")
            parts = pending[-1].split()
            counts.append(int(parts[parts.index("nodes") + 1]))
            pending = []
    return counts


def show(label, counts):
    print(f"{label} n={len(counts)} sum={sum(counts)} first={counts[0]} {counts[1]} {counts[2]}")


def main():
    base, off, on = [nodes_from_raw(path) for path in sys.argv[1:4]]
    show("B", base)
    show("Poff", off)
    show("Pon", on)
    same = sum(1 for a, b in zip(base, off) if a == b)
    differ = sum(1 for a, b in zip(base, on) if a != b)
    print(f"Poff equal to B: {same} of {len(base)}")
    print(f"Pon differ from B: {differ} of {len(base)}")
    if len(base) == len(off):
        mismatches = [(i + 1, a, b) for i, (a, b) in enumerate(zip(base, off)) if a != b]
        if mismatches[:5]:
            print("Poff mismatches (first 5): " + " ".join(f"{i}:{a}!={b}" for i, a, b in mismatches[:5]))


if __name__ == "__main__":
    main()
