#!/usr/bin/env python3
"""mpv3_hash256.py — seat 20 job 54: does the collapse hit MultiPV 3 with Hash 256 (a plausible GUI setting)?
Plus: a SECOND position under load, to test whether the 0-node behaviour generalises beyond the one position.

Part A: MultiPV 3 + Hash 256 vs healthy control, 5 runs idle and 5 under load, zero-node count in each.
Part B: the same four-cell table on a second position, so the warning page can either claim or explicitly not
        claim generality.

usage: mpv3_hash256.py <pc-exe> <outdir> [hogs]
"""
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDIT"))
from hardened import Engine  # noqa: E402

PC, OUT = sys.argv[1], sys.argv[2]
HOGS = int(sys.argv[3]) if len(sys.argv) > 3 else 3
os.makedirs(OUT, exist_ok=True)

S14 = [("Threads", 1), ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
       ("OwnBook", "false"), ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
       ("CorrHistV2", "true"), ("MateAlphaGuard", "true")]
GO = "go wtime 5000 btime 5000"
POS = {
    "P1 (job53)": "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1",
    "P2 (G set)": "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1",
}
CELLS = {
    "Hash256+MPV3": [("Hash", 256), ("MultiPV", 3)] + S14,
    "Hash16+MPV1": [("Hash", 16), ("MultiPV", 1)] + S14,
}


def arm(fen, opts, runs=5, ready_timeout=120.0):
    out = []
    for _ in range(runs):
        e = Engine(PC, opts=list(opts))
        try:
            e.position(fen, ready_timeout=ready_timeout)
            r = e.search(GO, 120)
        finally:
            e.close()
        out.append({"bestmove": r["bestmove"], "nodes": r["nodes"], "score": r["score"],
                    "wall_ms": round(r["wall"] * 1000)})
    return out


def summarize(rows):
    return {"zero": sum(1 for r in rows if r["nodes"] == 0), "n": len(rows),
            "moves": sorted({r["bestmove"] for r in rows}),
            "nodes": sorted({r["nodes"] for r in rows}), "rows": rows}


res = {}
print(f"exe {PC}   {GO}   Threads 1")
print()
print("== IDLE")
for pname, fen in POS.items():
    for cname, opts in CELLS.items():
        s = summarize(arm(fen, opts))
        res[f"idle|{pname}|{cname}"] = s
        print(f"  {pname:11s} {cname:13s} 0-node {s['zero']}/{s['n']}  moves {s['moves']}  nodes {s['nodes']}")
print()

print(f"== UNDER LOAD ({HOGS} busy processes)")
hogs = []
try:
    for _ in range(HOGS):
        hogs.append(subprocess.Popen([sys.executable, "-c", "while True: pass"]))
    time.sleep(0.5)
    for pname, fen in POS.items():
        for cname, opts in CELLS.items():
            s = summarize(arm(fen, opts))
            res[f"load|{pname}|{cname}"] = s
            print(f"  {pname:11s} {cname:13s} 0-node {s['zero']}/{s['n']}  moves {s['moves']}  nodes {s['nodes']}")
finally:
    for h in hogs:
        h.kill()

print()
print("== the specific question: does MultiPV 3 + Hash 256 fail?")
for cond in ("idle", "load"):
    a = res[f"{cond}|P1 (job53)|Hash256+MPV3"]
    b = res[f"{cond}|P1 (job53)|Hash16+MPV1"]
    print(f"  {cond:5s} P1: Hash256+MPV3 0-node {a['zero']}/{a['n']}, healthy control 0-node {b['zero']}/{b['n']}")

with open(os.path.join(OUT, "mpv3_hash256.json"), "w") as f:
    json.dump(res, f, indent=1)
print("\nwrote mpv3_hash256.json")
