#!/usr/bin/env python3
"""Count the DISTINCT positions a set of fixtures compares, and prove the arithmetic.

The incremental harness prints comparisons per run, and those runs overlap: seq_small is a
prefix of seq_large, and seq_large is a prefix of seq_deep, because all three take the first
N rows of the same corpus with the same first 40 plies. Adding the per-run counts therefore
double-counts heavily. This script computes the union of positions actually compared, which
is the only honest denominator.

A position is identified by (root FEN, move prefix), so two fixtures that reach the same board
by the same move list are counted once.

Usage: count_distinct.py <fixture> ...
Exit status 1 if a fixture cannot be parsed (a silent zero would otherwise look like success).
"""
import sys

files = sys.argv[1:]
if not files:
    print("usage: count_distinct.py <fixture> ...")
    sys.exit(2)

sets = {}
for path in files:
    positions = set()
    try:
        handle = open(path, encoding="utf-8")
    except OSError as exc:
        print("COUNT FAIL cannot open %s: %s" % (path, exc))
        sys.exit(1)
    with handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            if "|" in line:
                fen, moves = line.split("|", 1)
            else:
                fen, moves = line, ""
            fen = fen.strip()
            moves = moves.split()
            if not fen:
                continue
            for k in range(len(moves) + 1):
                positions.add((fen, tuple(moves[:k])))
    if not positions:
        print("COUNT FAIL %s yielded no positions" % path)
        sys.exit(1)
    sets[path] = positions
    print("COUNT %-28s distinct_positions %d" % (path.split("/")[-1], len(positions)))

union = set()
for positions in sets.values():
    union |= positions
# Report pairwise overlap so the union is auditable rather than a black box.
names = list(sets)
print("COUNT pairwise_overlap")
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        overlap = len(sets[names[i]] & sets[names[j]])
        print("COUNT   %-24s vs %-24s %d"
              % (names[i].split("/")[-1], names[j].split("/")[-1], overlap))
print("COUNT union_distinct_positions %d" % len(union))
