#!/usr/bin/env python3
"""threshold_vs_overhead.py — seat 20 job 21b: does the increment-ignored boundary track Move Overhead?

If the boundary is `time <= overhead`, then with Move Overhead 0 it should move to 0/1; if 11-13 keep ignoring the
increment at overhead 0 too, the second effect I could not identify is independent of the overhead.

usage: threshold_vs_overhead.py <exe> <outdir>
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDIT"))
from hardened import Engine  # noqa: E402

EXE, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
FEN = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1"


def nodes(wtime, winc, overhead):
    opts = [("Move Overhead", overhead)] if overhead is not None else []
    e = Engine(EXE, opts=opts)
    try:
        e.position(FEN)
        r = e.search(f"go wtime {wtime} btime {wtime} winc {winc} binc {winc}", 120)
    finally:
        e.close()
    assert r["bestmove"] is not None and r["score"] is not None, "unparsed result — refusing to record"
    return r["nodes"], r["bestmove"]


rows = []
print(f"exe {EXE}")
for overhead in (None, 0, 30):
    lab = "default(10)" if overhead is None else str(overhead)
    print(f"\n== Move Overhead {lab}: first wtime where winc 1000 differs from winc 0")
    boundary = None
    for w in (1, 2, 3, 5, 8, 10, 11, 12, 13, 14, 15, 18, 22, 26, 30, 35, 40):
        n0, _ = nodes(w, 0, overhead)
        n1, _ = nodes(w, 1000, overhead)
        same = n0 == n1
        rows.append({"overhead": overhead, "wtime": w, "nodes_winc0": n0, "nodes_winc1000": n1,
                     "identical": same})
        if not same and boundary is None:
            boundary = w
        print(f"  wtime {w:3d}: {n0:7d} vs {n1:7d}  {'identical' if same else 'DIFFERS'}")
    print(f"  -> first differing wtime: {boundary}")

with open(os.path.join(OUT, "threshold_vs_overhead.json"), "w") as f:
    json.dump({"exe": EXE, "rows": rows}, f, indent=1)
print("\nwrote threshold_vs_overhead.json")
