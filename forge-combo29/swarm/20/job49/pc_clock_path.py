#!/usr/bin/env python3
"""pc_clock_path.py — seat 20 job 49: the PC's real clock path, 6 s + 0.06 per move.

FABLE_TO_swarm_6: the owner's strength matches run the clock 6 seconds + 0.06 per move. Seat 08's 08-F25 recorded
that the high-counter K+R v K case does NOT fit that clock. Nobody has published the basic numbers for that path:
how long does a move actually take, how many nodes/depth does it reach, and is it reproducible at Threads 1?

Method: `go wtime 6000 btime 6000 winc 60 binc 60`, PC r15 + PC20, Threads 1, Hash 16, fresh process, 3 runs per
position, positions from real games. Monotonic wall clock from writing `go` to reading `bestmove`.
The clock is decremented the way a GUI would across a short game: 6 moves in a row, each with the remaining time
passed back in, so the time management sees a realistic sequence rather than a fresh 6 s every ply.

usage: pc_clock_path.py <pc-exe> <outdir>
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDIT"))
from hardened import Engine  # noqa: E402

PC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

S14 = [("Threads", 1), ("Hash", 16), ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
       ("OwnBook", "false")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true")]
POS = {
    "G1": "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1",
    "G2": "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1",
}
WT, INC = 6000, 60


def one_move(fen, t):
    e = Engine(PC, opts=PC20)
    try:
        e.position(fen)
        r = e.search(f"go wtime {t} btime {t} winc {INC} binc {INC}", 60)
        lines = [x for x in e.since(0) if x.startswith("info depth")]
    finally:
        e.close()
    depth = None
    for ln in lines:
        m = re.search(r"depth (\d+)", ln)
        if m:
            depth = int(m.group(1)) if depth is None else max(depth, int(m.group(1)))
    return r, depth


rows = []
print(f"exe {PC}   PC20   Threads 1   Hash 16")
print(f"clock {WT} ms + {INC} ms per move, 6 moves per run, 3 runs per position")
print()
for pname, fen in POS.items():
    print(f"== {pname}")
    for run_i in range(3):
        t = WT
        seq = []
        for mv_no in range(6):
            r, depth = one_move(fen, t)
            wall = r["wall"] * 1000
            # a GUI subtracts the elapsed time and adds the increment
            t = max(0, int(t - wall + INC))
            seq.append(f"{r['bestmove']}/d{depth}/{r['nodes']}n/{wall:.0f}ms")
            rows.append({"pos": pname, "run": run_i, "move": mv_no, "clock_before": None,
                         "bestmove": r["bestmove"], "depth": depth, "nodes": r["nodes"],
                         "wall_ms": round(wall, 1), "score": r["score"]})
        print(f"  run {run_i+1}: " + "  ".join(seq))
    print()

# determinism summary: compare run 1 vs 2 vs 3 per move index
print("== reproducibility at Threads 1 (same move index across the three runs)")
for pname in POS:
    rs = [r for r in rows if r["pos"] == pname]
    for mv_no in range(6):
        cell = [r for r in rs if r["move"] == mv_no]
        same = len({c["bestmove"] for c in cell}) == 1 and len({c["depth"] for c in cell}) == 1
        nset = sorted({c["nodes"] for c in cell})
        wset = [round(c["wall_ms"], 0) for c in cell]
        print(f"  {pname} move {mv_no+1}: {'SAME move+depth' if same else 'VARIES'}  "
              f"nodes {nset}  wall {wset} ms")
    print()

with open(os.path.join(OUT, "pc_clock_path.json"), "w") as f:
    json.dump({"exe": PC, "wtime": WT, "winc": INC, "rows": rows}, f, indent=1)
print("wrote pc_clock_path.json")
