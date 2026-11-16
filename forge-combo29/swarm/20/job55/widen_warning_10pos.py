#!/usr/bin/env python3
"""widen_warning_10pos.py — seat 20 job 55: widen the MultiPV/Hash warning from 2 positions to 10.

The current warning (S-F50/S-C31) says: at Hash 2048 MB with any MultiPV above 1 the engine can return a move with
**no search** (0 nodes). It was measured on ONE position for the load arm and on a few for the boundary sweep, so the
owner cannot act on a rate. This job measures:

  * 10 positions from the swarm G set (real-game positions, valid, non-terminal),
  * Hash 2048 MB x MultiPV {2, 3, 8}, plus the healthy control Hash 16 + MultiPV 1,
  * 5 fresh processes per cell,
  * counting per cell: ZERO-NODE answers, and DEPTH COLLAPSE (deepest depth <= 3, i.e. the analysis is worthless).

Per cell I report the counts, and I list the positions that failed so seat-20's claim can be re-checked by id.
A cell that comes out clean is reported as clean, and the warning will be narrowed to whatever the data supports.

Threads 1 throughout, as the swarm rule requires. `isready` timeout is 90 s because the engine can be slow with a
2 GB table; the 19-F12 discipline (never continue without a readyok) is unchanged.

usage: widen_warning_10pos.py <pc-exe> <outdir> [n_positions] [runs]
"""
import json
import os
import re
import sys

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDIT"))
from hardened import Engine  # noqa: E402

PC, OUT = sys.argv[1], sys.argv[2]
NPOS = int(sys.argv[3]) if len(sys.argv) > 3 else 10
RUNS = int(sys.argv[4]) if len(sys.argv) > 4 else 5
os.makedirs(OUT, exist_ok=True)

S14 = [("Threads", 1), ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
       ("OwnBook", "false"), ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
       ("CorrHistV2", "true"), ("MateAlphaGuard", "true")]
GO = "go wtime 5000 btime 5000"
CELLS = [("healthy", 16, 1), ("mpv2", 2048, 2), ("mpv3", 2048, 3), ("mpv8", 2048, 8)]

GF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job24", "G_353.fens")
fens = []
for line in open(GF, encoding="utf-8", errors="replace"):
    if not line.strip():
        continue
    f = " ".join(line.split()[:6])
    try:
        b = chess.Board(f)
        if b.is_valid() and not b.is_game_over() and b.legal_moves.count() > 8 and not b.is_check():
            fens.append(f)
    except ValueError:
        pass
    if len(fens) >= NPOS:
        break

print(f"pc exe {PC}")
print(f"{len(fens)} positions from the swarm G set, {RUNS} fresh processes per cell, Threads 1")
print(f"cells: healthy (Hash 16 MPV 1), then Hash 2048 x MultiPV 2 / 3 / 8")
print(f"criteria: ZERO-NODE = a run whose bestmove came with 0 nodes; COLLAPSE = deepest depth <= 3")
print()


def one(fen, opts):
    e = Engine(PC, opts=list(opts))
    try:
        e.position(fen, ready_timeout=90.0)
        r = e.search(GO, 180)
        lines = [x for x in e.since(0) if x.startswith("info depth")]
    finally:
        e.close()
    depth = None
    for ln in lines:
        m = re.search(r"depth (\d+)", ln)
        if m:
            d = int(m.group(1))
            depth = d if depth is None else max(depth, d)
    return {"bestmove": r["bestmove"], "nodes": r["nodes"], "depth": depth,
            "score": r["score"], "wall_ms": round(r["wall"] * 1000)}


rows = []
summary = {}
for label, h, mp in CELLS:
    opts = [("Hash", h), ("MultiPV", mp)] + S14
    zero_total = 0
    collapse_total = 0
    cells = []
    print(f"== {label}: Hash {h} MB, MultiPV {mp}")
    for i, fen in enumerate(fens, 1):
        runs = [one(fen, opts) for _ in range(RUNS)]
        z = sum(1 for r in runs if r["nodes"] == 0)
        worst_depth = min([r["depth"] for r in runs if r["depth"] is not None], default=None)
        collapsed = worst_depth is not None and worst_depth <= 3
        zero_total += z
        collapse_total += 1 if collapsed else 0
        cells.append({"pos": i, "fen": fen, "zero": z, "worst_depth": worst_depth,
                      "collapsed": collapsed, "nodes": sorted({r["nodes"] for r in runs}),
                      "moves": sorted({r["bestmove"] for r in runs})})
        flag = ""
        if z:
            flag += f"  ZERO-NODE {z}/{RUNS}"
        if collapsed:
            flag += f"  COLLAPSE (d{worst_depth})"
        print(f"  pos {i:2d}: nodes {str(cells[-1]['nodes']):24s} depth {str(worst_depth):>3s} "
              f"moves {str(cells[-1]['moves'])[:24]:24s}{flag}")
    summary[label] = {"hash": h, "multipv": mp, "zero_runs": zero_total,
                      "zero_positions": sum(1 for c in cells if c["zero"] > 0),
                      "collapsed_positions": collapse_total, "cells": cells}
    print(f"  -> {label}: ZERO-NODE {zero_total}/{len(fens)*RUNS} runs "
          f"on {summary[label]['zero_positions']}/{len(fens)} positions; "
          f"COLLAPSE on {collapse_total}/{len(fens)} positions")
    print()

print("== SUMMARY")
print(f"{'cell':10s} {'zero-node runs':>15s} {'positions w/ zero':>18s} {'collapsed pos':>14s}")
for label, _, _ in CELLS:
    s = summary[label]
    print(f"{label:10s} {s['zero_runs']:>10d}/{len(fens)*RUNS:<4d} "
          f"{s['zero_positions']:>13d}/{len(fens):<4d} {s['collapsed_positions']:>9d}/{len(fens):<4d}")

with open(os.path.join(OUT, "widen_10pos.json"), "w") as f:
    json.dump({"exe": PC, "runs": RUNS, "summary": summary}, f, indent=1)
print("\nwrote widen_10pos.json")
