#!/usr/bin/env python3
"""one_sided_clock.py — seat 20 job 61: does `go wtime N` without `btime` run away? (seat 30's 30-F52/F53)

Seat 30: "never send a `go` line with only one side's clock. `go wtime N` (no btime) makes this engine search 219
million nodes and 180 s without stopping; `go wtime 0 btime 0` answers in 4 ms."

My first probe did NOT reproduce it: `go wtime 2000` gave 147 ms / 242,214 nodes, identical to `go wtime 2000 btime
2000`. So this tests it properly, with the machine verified clean first and a hard 20 s cap per case, across BOTH
builds, several wtime values, and both colours (a one-sided clock may depend on which side is missing).

A HANG is the evidence: the runner reports hang=True and kills the process, so a runaway cannot eat the turn.

usage: one_sided_clock.py <pc-exe> <base-exe> <outdir>
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDIT"))
from hardened import Engine  # noqa: E402

PC, BASE, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
S14 = [("Threads", 1), ("Hash", 16), ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
       ("OwnBook", "false"), ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
       ("CorrHistV2", "true"), ("MateAlphaGuard", "true")]
WHITE = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1"
BLACK = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 0 1"
CASES = ["go wtime 2000 btime 2000", "go wtime 2000", "go btime 2000",
         "go wtime 500 btime 500", "go wtime 500", "go btime 500",
         "go wtime 0 btime 0"]
CAP = 20.0


def one(exe, fen, go):
    e = Engine(exe, opts=S14)
    try:
        e.position(fen, ready_timeout=60.0)
        t0 = time.monotonic()
        r = e.search(go, CAP)
        el = (time.monotonic() - t0) * 1000
    finally:
        e.close()
    return {"go": go, "hang": r["hang"], "wall_ms": round(el), "nodes": r["nodes"],
            "depths": r["info_depth_lines"]}


rows = []
for label, exe in (("pc_r15", PC), ("base", BASE)):
    for cname, fen in (("white", WHITE), ("black", BLACK)):
        print(f"== {label} / {cname} to move (cap {CAP:.0f}s)")
        for go in CASES:
            r = one(exe, fen, go)
            rows.append(dict(r, build=label, side=cname))
            flag = "  <== RUNAWAY/HANG" if r["hang"] else ""
            print(f"  {go:24s} hang={str(r['hang']):5s} {r['wall_ms']:7d} ms  nodes {r['nodes']:10d} "
                  f"depths {r['depths']:2d}{flag}")
        print()

print("== verdict")
one_sided = [r for r in rows if ("btime" not in r["go"])]
two_sided = [r for r in rows if ("wtime" in r["go"] and "btime" in r["go"])]
if any(r["hang"] for r in one_sided):
    print("  RUNAWAY CONFIRMED: a one-sided clock produced a hang.")
else:
    print("  NOT REPRODUCED: no one-sided clock hung in this run (cap 20 s).")
    print(f"  one-sided cases: {len(one_sided)}, all answered; max wall "
          f"{max(r['wall_ms'] for r in one_sided)} ms")

with open(os.path.join(OUT, "one_sided_clock.json"), "w") as f:
    json.dump({"rows": rows, "cap_s": CAP}, f, indent=1)
print("\nwrote one_sided_clock.json")
