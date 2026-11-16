#!/usr/bin/env python3
"""confirm_30c36.py — seat 20 job 57: independent confirmation of seat 30's 30-C36 and their repair.

Their claims checked here, with my own harness and my own fresh processes:
  C36a  at Hash 512, MultiPV 3, `go wtime 5000`, Threads 1: SHIPPED depth 1 (5/5) vs REPAIRED depth 12 (5/5).
  C36b  at Hash 256 the shipped build is unstable ({7,5,10}) while the repaired one is stable.
  C31   the repair keeps all four honesty pins (verified separately: 4/4).

Controls: the HEALTHY cell (Hash 16, MultiPV 1) must be identical on both builds — the patch should not touch the
MultiPV 1 path, so any difference there would mean the repair changed something it should not.

usage: confirm_30c36.py <shipped-exe> <repaired-exe> <outdir>
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDIT"))
from hardened import Engine  # noqa: E402

SHIP, FIX, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)

S14 = [("Threads", 1), ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
       ("OwnBook", "false"), ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
       ("CorrHistV2", "true"), ("MateAlphaGuard", "true")]
GO = "go wtime 5000 btime 5000"
FEN = "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"


def arm(exe, h, mp, runs=5):
    out = []
    for _ in range(runs):
        e = Engine(exe, opts=[("Hash", h), ("MultiPV", mp)] + S14)
        try:
            e.position(FEN, ready_timeout=120.0)
            r = e.search(GO, 180)
            lines = [x for x in e.since(0) if x.startswith("info depth")]
        finally:
            e.close()
        d = None
        for ln in lines:
            m = re.search(r"depth (\d+)", ln)
            if m:
                v = int(m.group(1))
                d = v if d is None else max(d, v)
        out.append({"depth": d, "nodes": r["nodes"], "bestmove": r["bestmove"],
                    "wall_ms": round(r["wall"] * 1000)})
    return out


rows = []
print(f"shipped  {SHIP}")
print(f"repaired {FIX}")
print(f"position {FEN}")
print(f"MultiPV 3, {GO}, Threads 1, 5 fresh processes per cell")
print()
print(f"{'Hash':>6s} {'build':9s} {'depths (5 runs)':>22s} {'nodes':>34s} {'stable':>7s}")
for h in (256, 512):
    for label, exe in (("shipped", SHIP), ("repaired", FIX)):
        rs = arm(exe, h, 3)
        ds = [r["depth"] for r in rs]
        ns = [r["nodes"] for r in rs]
        stable = len(set(ds)) == 1 and len(set(ns)) == 1
        rows.append({"hash": h, "build": label, "depths": ds, "nodes": ns,
                     "bestmoves": sorted({r["bestmove"] for r in rs}), "stable": stable})
        print(f"{h:6d} {label:9s} {str(ds):>22s} {str(ns):>34s} {str(stable):>7s}")

print()
print("== control: the MultiPV 1 path must be identical on both builds")
for h in (16, 512):
    a = arm(SHIP, h, 1, runs=3)
    b = arm(FIX, h, 1, runs=3)
    same_depth = [r["depth"] for r in a] == [r["depth"] for r in b]
    same_nodes = [r["nodes"] for r in a] == [r["nodes"] for r in b]
    rows.append({"control_hash": h, "shipped": a, "repaired": b,
                 "same_depth": same_depth, "same_nodes": same_nodes})
    print(f"  Hash {h:4d} MPV 1: shipped depths {[r['depth'] for r in a]} nodes {[r['nodes'] for r in a]}")
    print(f"  {'':14s} repaired depths {[r['depth'] for r in b]} nodes {[r['nodes'] for r in b]}")
    print(f"  {'':14s} identical depth {same_depth}, identical nodes {same_nodes}")

with open(os.path.join(OUT, "confirm_30c36.json"), "w") as f:
    json.dump({"fen": FEN, "rows": rows}, f, indent=1)
print("\nwrote confirm_30c36.json")
