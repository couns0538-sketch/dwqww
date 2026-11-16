#!/usr/bin/env python3
"""band_go_nodes.py — seat 20 job 45: the `go nodes` band below 26, with PER-RUN data.

The owner's second live PC defect. Seat 27's S-F2 and seat 17's S-C4 both put the threshold at 26 on the base tree
(`go nodes` 1/5/10/20/25 answer a2a3 with zero info lines; 26 answers d2d4 with one info line). My S-F8/S-F11 only
tested `nodes 1`. This walks EVERY value 1..30 with 3 runs each, on both builds, Threads 1, and records the number
of info-depth lines and the node count — because a fabricated answer and a short real search differ exactly there.

Rule-1 controls, built in and asserted:
  * `go nodes 1000` must give a real searched answer with nodes > 0 (proves the harness reads a real search);
  * the dead board must still answer legally (proves "no bestmove" is not being mistaken for the defect).

usage: band_go_nodes.py <base-exe> <pc-exe> <outdir>
"""
import json
import os
import sys

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDIT"))
from hardened import Engine  # noqa: E402

BASE, PC, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)

S14 = [("Threads", 1), ("Hash", 16), ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
       ("OwnBook", "false")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true")]
START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def run(exe, opts, fen, go):
    e = Engine(exe, opts=list(opts))
    try:
        e.position(fen)
        r = e.search(go, 300)
    finally:
        e.close()
    return r


rows = []
print(f"position {START}   Threads 1   fresh process per run   ndeepest first legal move is a2a3 on startpos")
print()
for label, exe, opts in (("base_s14", BASE, S14), ("pc20", PC, PC20)):
    print(f"=== {label}")
    print(f"{'nodes':>6s} {'bestmove':9s} {'info lines':>10s} {'reported nodes':>15s} {'stable':>7s}  runs")
    for n in range(1, 31):
        outs = [run(exe, opts, START, f"go nodes {n}") for _ in range(3)]
        bm = [o["bestmove"] for o in outs]
        lines = [o["info_depth_lines"] for o in outs]
        rep = [o["nodes"] for o in outs]
        stable = len(set(bm)) == 1 and len(set(lines)) == 1 and len(set(rep)) == 1
        rows.append({"build": label, "nodes_arg": n, "bestmove": bm, "info_lines": lines,
                     "reported_nodes": rep, "stable": stable})
        print(f"{n:6d} {bm[0]:9s} {lines[0]:10d} {rep[0]:15d} {str(stable):>7s}  "
              f"{bm[0]}/{lines[0]}/{rep[0]} x3" if stable else
              f"{n:6d} {str(bm):9s} {str(lines):10s} {str(rep):15s} {str(stable):>7s}  UNSTABLE")

print()
print("=== controls")
for label, exe, opts in (("base_s14", BASE, S14), ("pc20", PC, PC20)):
    big = run(exe, opts, START, "go nodes 1000")
    print(f"  {label:9s} go nodes 1000: {big['bestmove']} {big['score']} nodes {big['nodes']} "
          f"info lines {big['info_depth_lines']}  -> searched answer {'YES' if big['nodes'] > 0 else 'NO'}")
    assert big["nodes"] > 0, "harness cannot see a real search — abort"

with open(os.path.join(OUT, "band_nodes.json"), "w") as f:
    json.dump({"position": START, "rows": rows}, f, indent=1)
print("\nwrote band_nodes.json")
