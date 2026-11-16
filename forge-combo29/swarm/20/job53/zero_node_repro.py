#!/usr/bin/env python3
"""zero_node_repro.py — seat 20 job 53: is the 0-node answer in the collapsed cell LOAD-driven?
 
S-C29 saw, on `1r6/2k2pp1/...` with Hash 2048 + MultiPV 8 at `go wtime 5000`, one run return `d5d4` with **0 nodes**
where the others returned `b8a8` at depth 1. My hypothesis: under CPU contention the per-line tt.clear() eats the
whole clock before any depth is published, so the engine falls back to its first move with 0 nodes.
 
Test: run the SAME cell 10 times on an idle machine, then 10 times with N artificial CPU hogs running.

Rule-1 control: the same 10-run comparison on the HEALTHY cell (Hash 16, MultiPV 1) must NOT produce any 0-node
answer; if it does, the 0-node answer is a general property and not specific to the collapsed cell.

usage: zero_node_repro.py <pc-exe> <outdir> [hogs]
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
FEN = "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"


def cell(opts, go, runs=10, ready_timeout=20.0):
    out = []
    for _ in range(runs):
        e = Engine(PC, opts=list(opts))
        try:
            e.position(FEN, ready_timeout=ready_timeout)
            r = e.search(go, 90)
        finally:
            e.close()
        out.append({"bestmove": r["bestmove"], "nodes": r["nodes"], "score": r["score"],
                    "wall_ms": round(r["wall"] * 1000)})
    return out


def summarize(label, rows):
    zero = sum(1 for r in rows if r["nodes"] == 0)
    moves = sorted({r["bestmove"] for r in rows})
    nodes = sorted({r["nodes"] for r in rows})
    print(f"  {label:26s} 0-node answers {zero}/{len(rows)}  moves {moves}")
    print(f"  {'':26s} node counts {nodes}")
    return {"label": label, "zero_node": zero, "n": len(rows), "moves": moves, "nodes": nodes,
            "rows": rows}


COLLAPSED = [("Hash", 2048), ("MultiPV", 8)] + S14
HEALTHY = [("Hash", 16), ("MultiPV", 1)] + S14
GO = "go wtime 5000 btime 5000"

res = {}
print(f"exe {PC}   {GO}")
print()
print("== IDLE machine")
res["collapsed_idle"] = summarize("Hash2048+MPV8 collapsed", cell(COLLAPSED, GO))
res["healthy_idle"] = summarize("Hash16+MPV1 healthy", cell(HEALTHY, GO))
print()

print(f"== UNDER LOAD: {HOGS} busy-loop processes (isready timeout raised to 120s: the engine is starved, not hung; the 19-F12 discipline is unchanged — we still refuse to continue without a readyok)")
hogs = []
try:
    for _ in range(HOGS):
        hogs.append(subprocess.Popen([sys.executable, "-c", "while True: pass"]))
    time.sleep(0.5)
    res["collapsed_load"] = summarize("Hash2048+MPV8 collapsed", cell(COLLAPSED, GO, ready_timeout=120.0))
    res["healthy_load"] = summarize("Hash16+MPV1 healthy", cell(HEALTHY, GO, ready_timeout=120.0))
finally:
    for h in hogs:
        h.kill()

print()
print("== verdict")
ci, cl = res["collapsed_idle"], res["collapsed_load"]
hi, hl = res["healthy_idle"], res["healthy_load"]
print(f"  collapsed: 0-node answers idle {ci['zero_node']}/{ci['n']} -> under load {cl['zero_node']}/{cl['n']}")
print(f"  healthy  : 0-node answers idle {hi['zero_node']}/{hi['n']} -> under load {hl['zero_node']}/{hl['n']}")
if hl["zero_node"] > 0:
    print("  CAUTION: the healthy cell also produced 0-node answers under load, so the 0-node path is not")
    print("  specific to the MultiPV/Hash collapse.")
elif cl["zero_node"] > ci["zero_node"]:
    print("  -> load makes the COLLAPSED cell worse while the healthy cell stays clean: the 0-node answer is")
    print("     specific to the collapse and is aggravated by contention.")
else:
    print("  -> no load effect observed in this sample; the 0-node answer seen in S-C29 was a one-off here.")

with open(os.path.join(OUT, "zero_node.json"), "w") as f:
    json.dump(res, f, indent=1)
print("\nwrote zero_node.json")
