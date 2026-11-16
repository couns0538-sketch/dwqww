#!/usr/bin/env python3
"""report_softnodes.py : paste-ready tables from the softnodes runs.

Integrity: every number comes from the committed JSON; a missing file or an empty record list is a hard
failure, and the determinism columns are computed, never typed.
"""
import json
import sys


def load(path):
    try:
        d = json.load(open(path))
    except FileNotFoundError:
        print("HARD FAILURE: missing", path)
        sys.exit(2)
    if not d.get("records"):
        print("HARD FAILURE: no records in", path)
        sys.exit(2)
    return d


fresh = load("out_fresh.json")
print("== fresh-process runs (PC r15, PC20, Threads 1, Hash 16)")
print("exe %s sha %s" % (fresh["meta"]["exe_path_started"], fresh["meta"]["sha256"][:16]))
print()
print("| N | runs | nodes last info (min..max) | overshoot nodes/N (min..max) | partial-depth lines |")
print("|---|---|---|---|---|")
by_n = {}
for r in fresh["records"]:
    by_n.setdefault(r["n"], []).append(r)
for n in sorted(by_n):
    rs = by_n[n]
    ln = [r["last_nodes"] for r in rs]
    ov = [r["last_nodes"] / n for r in rs]
    part = sum(1 for r in rs if r["partial_depth_line"])
    print("| %d | %d | %d..%d | %.2f..%.2f | %d |" %
          (n, len(rs), min(ln), max(ln), min(ov), max(ov), part))

print()
print("== determinism, FRESH process, same position at N=2000, FIVE separate processes (out_repeat.json)")
rep = load("out_repeat.json")
bypos = {}
for r in rep["records"]:
    bypos.setdefault(r["fen"], []).append((r["bestmove"], r["last_nodes"]))
ident_f = 0
for fen, vals in bypos.items():
    same = len(set(vals)) == 1
    ident_f += same
    print("| %s | %d runs | %s |" % (fen[:34], len(vals),
          "IDENTICAL %s" % (vals[0],) if same else "DIFFERS %s" % (vals,)))
print()
print("positions identical across all 5 fresh processes: %d of %d" % (ident_f, len(bypos)))

inp = load("out_inproc_p.json")
print()
print("== in-process, THREE repeats, NOTHING between them (N=2000)")
print("| position | run | bestmove | nodes |")
print("|---|---|---|---|")
rows = {}
for r in inp["records"]:
    rows.setdefault(r["fen"], []).append(r)
ident = 0
total = 0
for fen, rs in rows.items():
    vals = [(r["bestmove"], r["last_nodes"]) for r in rs]
    if len(set(vals)) == 1:
        ident += 1
    total += 1
    for i, r in enumerate(rs):
        print("| %s | %d | %s | %d |" % (fen[:34], i + 1, r["bestmove"], r["last_nodes"]))
print()
print("positions where all three in-process repeats were identical: %d of %d" % (ident, total))

inu = load("out_inproc_u.json")
rows = {}
for r in inu["records"]:
    rows.setdefault(r["fen"], []).append(r)
ident_u = sum(1 for rs in rows.values() if len({(r["bestmove"], r["last_nodes"]) for r in rs}) == 1)
print("positions where all three repeats were identical WITH ucinewgame between: %d of %d" % (ident_u, len(rows)))
