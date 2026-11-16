#!/usr/bin/env python3
"""deepseek6 long 34: analysis of the extreme-value sweep.

Reads sweep/sweep.tsv and prints the tables the report needs:
  * the whole inventory (116 rows) sorted by option,
  * the ratio of each extreme to the S14 baseline (the baseline is its own run: the option
    that changes nothing at either end reproduces it),
  * the identity runs (both ends equal the baseline node for node),
  * the slowest five (P4) and the five inert options (P5).

usage: analyze34.py [sweep dir]
"""
import os
import sys

D = sys.argv[1] if len(sys.argv) > 1 else "sweep"
rows = []
with open(os.path.join(D, "sweep.tsv")) as f:
    head = f.readline().rstrip("\n").split("\t")
    for line in f:
        v = line.rstrip("\n").split("\t")
        if len(v) != len(head):
            continue
        rows.append(dict(zip(head, v)))

for r in rows:
    r["nodes"] = int(r["nodes"])
    r["san_lines"] = int(r["san_lines"])
    r["illegal"] = int(r["illegal"])
    r["missing"] = int(r["missing"])
    r["secs"] = float(r["secs"])

# The baseline: the most common node total among runs whose option is one the item calls inert
# is NOT assumed. The honest baseline is the mode of all runs, because most options do not
# change the tree at all; the report also names a specific baseline run to prove it.
counts = {}
for r in rows:
    counts[r["nodes"]] = counts.get(r["nodes"], 0) + 1
mode_nodes = max(counts, key=counts.get)
print("== BASELINE: the most frequent node total across the 116 runs is %d (%d of 116 runs)" %
      (mode_nodes, counts[mode_nodes]))
print("   (an independent baseline: the plain build's own S14 rows at depth 8, see the report)")

base = mode_nodes
print()
print("== SANITIZER / CRASH / LEGALITY")
print("runs: %d" % len(rows))
print("runs with a sanitizer line: %d" % sum(1 for r in rows if r["san_lines"]))
print("runs that died or refused: %d" % sum(1 for r in rows if r["death"] != "-"))
print("runs with an illegal bestmove: %d" % sum(1 for r in rows if r["illegal"]))
print("runs with a missing bestmove: %d" % sum(1 for r in rows if r["missing"]))

print()
print("== IDENTITY RUNS (both ends reproduce the baseline node-for-node)")
by_opt = {}
for r in rows:
    by_opt.setdefault(r["option"], {})[r["end"]] = r
ident = []
for name, e in sorted(by_opt.items()):
    if len(e) == 2 and e["min"]["nodes"] == base and e["max"]["nodes"] == base:
        ident.append(name)
print("%d options are identical at BOTH ends: %s" % (len(ident), ", ".join(ident)))

print()
print("== SLOWEST FIVE RUNS (largest node total)")
for r in sorted(rows, key=lambda r: -r["nodes"])[:5]:
    print("  %-28s %-3s %-6s nodes=%9d ratio=%.3f  %.1fs" %
          (r["option"], r["end"], r["value"], r["nodes"], r["nodes"] / base, r["secs"]))

print()
print("== EVERY OPTION, BOTH ENDS, RATIO TO THE BASELINE")
print("| option | min | min nodes | min ratio | max | max nodes | max ratio |")
print("|---|---|---|---|---|---|---|")
for name, e in sorted(by_opt.items()):
    if len(e) != 2:
        continue
    a, b = e["min"], e["max"]
    print("| %s | %s | %d | %.4f | %s | %d | %.4f |" %
          (name, a["value"], a["nodes"], a["nodes"] / base, b["value"], b["nodes"], b["nodes"] / base))

print()
print("== OPTIONS WHOSE EXTREMES BOTH CHANGE THE TREE (neither end is the baseline)")
both = [n for n, e in sorted(by_opt.items())
        if len(e) == 2 and (e["min"]["nodes"] != base and e["max"]["nodes"] != base)]
print("%d: %s" % (len(both), ", ".join(both)))
