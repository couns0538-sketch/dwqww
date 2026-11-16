#!/usr/bin/env python3
"""pc_path_limits.py — seat 20 job 48: the PC's actual match path.

FABLE_TO_swarm_6: the owner's matches use `go nodes` 20000, 50000 and 250000 (plus the clock 6 s + 0.06 and
`go softnodes 2000` for self-play). A find on that path counts most, so this asks the question that matters for
every match result the owner will ever read:

  * is the search at those budgets DETERMINISTIC at Threads 1? (score, bestmove AND node count, 3 fresh processes)
  * does the hard limit actually hold at these sizes, or overrun?
  * how deep does each budget reach, on real-game positions?

Also records whether any budget produces a SANITIZER-looking line or a hang (the two real defect classes per file 6).

usage: pc_path_limits.py <pc-exe> <outdir>
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
BUDGETS = (20000, 50000, 250000)


def run(fen, go):
    e = Engine(PC, opts=PC20)
    try:
        e.position(fen)
        r = e.search(go, 900)
        lines = [x for x in e.since(0) if x.startswith("info depth")]
    finally:
        e.close()
    san = [x for x in lines if "Sanitizer" in x or "runtime error" in x]
    depth = None
    for ln in lines:
        m = re.search(r"depth (\d+)", ln)
        if m:
            depth = int(m.group(1)) if depth is None else max(depth, int(m.group(1)))
    return {"bestmove": r["bestmove"], "score": r["score"], "nodes": r["nodes"], "depth": depth,
            "hang": r["hang"], "sanitizer_lines": len(san), "wall_ms": round(r["wall"] * 1000)}


rows = []
print(f"exe {PC}   PC20   Threads 1   Hash 16 — the PC's match path")
print()
for pname, fen in POS.items():
    print(f"== {pname}  {fen}")
    for N in BUDGETS:
        outs = [run(fen, f"go nodes {N}") for _ in range(3)]
        nodes = [o["nodes"] for o in outs]
        det = len({o["score"] for o in outs}) == 1 and len({o["bestmove"] for o in outs}) == 1 \
            and len(set(nodes)) == 1
        overrun = all(n > N for n in nodes)
        rows.append({"pos": pname, "budget": N, "nodes": nodes, "scores": [o["score"] for o in outs],
                     "moves": [o["bestmove"] for o in outs], "depth": outs[0]["depth"],
                     "deterministic": det, "overran_budget": overrun,
                     "wall_ms": outs[0]["wall_ms"], "hang": any(o["hang"] for o in outs),
                     "sanitizer_lines": sum(o["sanitizer_lines"] for o in outs)})
        print(f"  go nodes {N:6d}: nodes {nodes}  depth {outs[0]['depth']}  "
              f"{str(outs[0]['score']):9s} {str(outs[0]['bestmove']):6s}  {outs[0]['wall_ms']:6d} ms  "
              f"{'DETERMINISTIC' if det else 'VARIES'}"
              f"{'  OVERRUN' if overrun else ''}"
              f"{'  HANG' if any(o['hang'] for o in outs) else ''}")
    print()

with open(os.path.join(OUT, "pc_path_limits.json"), "w") as f:
    json.dump({"exe": PC, "rows": rows}, f, indent=1)
print("wrote pc_path_limits.json")
