#!/usr/bin/env python3
"""multipv_hash_check.py — seat 20 job 50: independent confirmation of seat 02's S-F7b/S-F7c
(MultiPV x Hash depth collapse on the PC build).

Their claim (PC r15, Threads 1, 5 s clock, 3 runs/cell):
  * MultiPV 1 is SAFE at every Hash size (depth 16 at 16/64/256/2048 MB);
  * Hash 16 MB is safe up to MultiPV 8 (depth 12);
  * Hash 256 MB is ALREADY RUINED at MultiPV 3 (depth 8 vs 16);
  * Hash 2048 MB is depth 1 from MultiPV 2 upward.

The owner has told me to keep this one live, so this re-runs the critical cells with my own harness, Threads 1,
and reports depth per cell from PER-RUN data. I test a reduced but decisive grid: Hash 16, 256, 2048 x MultiPV 1, 3, 8.

usage: multipv_hash_check.py <pc-exe> <outdir>
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDIT"))
from hardened import Engine  # noqa: E402

PC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

S14 = [("Threads", 1), ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
       ("OwnBook", "false"), ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
       ("CorrHistV2", "true"), ("MateAlphaGuard", "true")]
FEN = "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"   # seat 04's / my G1


def cell(hash_mb, multipv, runs=3):
    depths, moves, walls = [], [], []
    for _ in range(runs):
        opts = [("Hash", hash_mb), ("MultiPV", multipv)] + S14
        e = Engine(PC, opts=opts)
        try:
            e.position(FEN)
            r = e.search("go wtime 5000 btime 5000", 60)
            lines = [x for x in e.since(0) if x.startswith("info depth")]
        finally:
            e.close()
        d = None
        for ln in lines:
            m = re.search(r"depth (\d+)", ln)
            if m:
                d = int(m.group(1)) if d is None else max(d, int(m.group(1)))
        depths.append(d)
        moves.append(r["bestmove"])
        walls.append(round(r["wall"] * 1000))
    return depths, moves, walls


rows = []
print(f"exe {PC}   PC20-style + Threads 1   go wtime 5000 btime 5000   {FEN}")
print()
print(f"{'Hash':>6s} {'MultiPV':>8s} {'depths (3 runs)':>20s} {'wall ms':>18s} {'moves':>18s}  verdict")
for h in (16, 256, 2048):
    for mp in (1, 3, 8):
        d, mv, w = cell(h, mp)
        worst = min(x for x in d if x is not None) if any(x is not None for x in d) else None
        healthy = worst is not None and worst >= 10
        verdict = "OK" if healthy else "COLLAPSED"
        rows.append({"hash": h, "multipv": mp, "depths": d, "walls": w, "moves": mv,
                     "worst_depth": worst, "verdict": verdict})
        print(f"{h:6d} {mp:8d} {str(d):>20s} {str(w):>18s} {str(sorted(set(mv))):>18s}  {verdict}")

with open(os.path.join(OUT, "multipv_hash.json"), "w") as f:
    json.dump({"fen": FEN, "rows": rows}, f, indent=1)
print()
print("wrote multipv_hash.json")
