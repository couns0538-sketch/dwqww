#!/usr/bin/env python3
"""budget_moves.py : does the bestmove change across the PC match path's three budgets?
Reads out_nodes.json (written by matchpath.py, fresh process per (position, budget))."""
import json

d = json.load(open("out_nodes.json"))
per = {}
for r in d["records"]:
    per.setdefault(r["fen"], {})[r["n"]] = r["bestmove"]
print("PC r15, PC20, Threads 1, Hash 16; budgets 20000 / 50000 / 250000")
print("| # | fen | 20000 | 50000 | 250000 | same at all three |")
print("|---|---|---|---|---|---|")
chg = 0
for i, (fen, m) in enumerate(per.items(), 1):
    vals = [m.get(n, "?") for n in (20000, 50000, 250000)]
    same = len(set(vals)) == 1
    chg += not same
    print("| %d | %s | %s | %s | %s | %s |" % (i, fen, vals[0], vals[1], vals[2],
                                              "yes" if same else "**NO**"))
print()
print("positions where the move changed: %d of %d" % (chg, len(per)))
