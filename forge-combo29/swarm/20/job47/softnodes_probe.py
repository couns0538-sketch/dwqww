#!/usr/bin/env python3
"""softnodes_probe.py — seat 20 job 47: `go softnodes N` on the PC build under PC20, Threads 1.

FABLE_TO_swarm_6 suggests this area: "is it deterministic run to run (it must be), does it stop at a finished
depth, and how far past N does it go?" This is the PC's real self-play path, so a find here counts most.

For each N in a ladder (2000 — the PC's own value — plus 500, 5000, 20000):
  * 5 fresh processes per N (determinism),
  * record the final score, bestmove, nodes, the deepest completed depth, and whether every reported depth line
    is a FINISHED iteration (a depth with a pv) or a partial one,
  * compute how far past N the node count goes (the "soft" overrun).

Controls (Rule 1):
  * a planted fake engine that returns a DIFFERENT node count each run must be flagged NON-deterministic by the
    same comparison, and one that returns a constant must pass;
  * `go nodes N` (hard limit) on the same build must NOT overrun, which is the contrast that makes a soft overrun
    meaningful rather than a harness artefact.

usage: softnodes_probe.py <pc-exe> <outdir>
"""
import json
import os
import re
import stat
import sys

import chess

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
# positions from real games (G set of the swarm, first two), plus startpos as a neutral control
POS = {
    "G1": "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1",
    "G2": "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1",
    "startpos": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
}


def run(exe, opts, fen, go):
    e = Engine(exe, opts=list(opts))
    try:
        e.position(fen)
        r = e.search(go, 600)
        lines = [x for x in e.since(0) if x.startswith("info depth")]
    finally:
        e.close()
    deepest, with_pv = None, 0
    for ln in lines:
        m = re.search(r"depth (\d+)", ln)
        if m:
            d = int(m.group(1))
            deepest = d if deepest is None else max(deepest, d)
            if " pv " in ln:
                with_pv += 1
    return {"bestmove": r["bestmove"], "score": r["score"], "nodes": r["nodes"],
            "depth_lines": len(lines), "deepest_depth": deepest, "lines_with_pv": with_pv,
            "hang": r["hang"]}


print(f"exe {PC}")
print(f"settings PC20, Threads 1, Hash 16 — the PC's self-play path")
print()

# ---------------- planted determinism controls -------------------------------------------------
FAKE_RANDOM = r'''#!/usr/bin/env python3
import sys, random
for line in sys.stdin:
    c=line.strip()
    if c=="uci":
        print("id name PLANTED-RANDOM",flush=True)
        print("option name Threads type spin default 1 min 1 max 256",flush=True)
        print("option name OwnBook type check default false",flush=True)
        print("uciok",flush=True)
    elif c=="isready": print("readyok",flush=True)
    elif c.startswith("go"):
        n=random.randint(1800,2200)
        print(f"info depth 5 seldepth 8 score cp 30 nodes {n} nps 1 hashfull 0 time 1 pv e2e4",flush=True)
        print("bestmove e2e4",flush=True)
'''
FAKE_STABLE = FAKE_RANDOM.replace("import sys, random", "import sys").replace(
    "n=random.randint(1800,2200)", "n=2000")


def fake(name, body):
    p = os.path.join(OUT, name)
    open(p, "w").write(body)
    os.chmod(p, 0o755)
    return p


print("== planted controls: the determinism detector must fire on a random engine and stay quiet on a stable one")
for label, path in (("RANDOM", fake("planted_random.py", FAKE_RANDOM)),
                    ("STABLE", fake("planted_stable.py", FAKE_STABLE))):
    outs = [run(path, [], POS["G1"], "go softnodes 2000") for _ in range(5)]
    nodes = {o["nodes"] for o in outs}
    moved = len({o["bestmove"] for o in outs})
    print(f"  {label:7s} nodes seen {sorted(nodes)}  distinct moves {moved}  -> "
          f"{'NON-DETERMINISTIC (correctly flagged)' if len(nodes) > 1 else 'deterministic'}")
    if label == "RANDOM":
        assert len(nodes) > 1, "detector failed to see planted nondeterminism — abort"
    else:
        assert len(nodes) == 1, "detector wrongly flagged a stable engine — abort"
print("  -> detector shown able to fire and to stay quiet.")
print()

rows = []
for pname, fen in POS.items():
    for N in (500, 2000, 5000, 20000):
        outs = [run(PC, PC20, fen, f"go softnodes {N}") for _ in range(5)]
        nodes = [o["nodes"] for o in outs]
        scores = [o["score"] for o in outs]
        moves = [o["bestmove"] for o in outs]
        depths = [o["deepest_depth"] for o in outs]
        det = len(set(nodes)) == 1 and len(set(scores)) == 1 and len(set(moves)) == 1
        overrun = (nodes[0] - N) / N * 100.0
        rows.append({"pos": pname, "softnodes": N, "nodes": nodes, "scores": scores, "moves": moves,
                     "deepest": depths, "deterministic": det,
                     "overrun_pct": round(overrun, 1),
                     "lines_with_pv": outs[0]["lines_with_pv"],
                     "depth_lines": outs[0]["depth_lines"]})
        print(f"{pname:9s} softnodes {N:6d}: nodes {nodes[0]:7d} ({overrun:+6.1f}% past N)  "
              f"depth {depths[0]}  pv-lines {outs[0]['lines_with_pv']}/{outs[0]['depth_lines']}  "
              f"{scores[0]:8s} {moves[0]:6s}  {'DETERMINISTIC 5/5' if det else 'VARIES: ' + str(nodes)}")
    print()

print("== contrast: the HARD limit on the same build/position (must not overrun)")
for N in (2000, 5000):
    outs = [run(PC, PC20, POS["G1"], f"go nodes {N}") for _ in range(3)]
    print(f"  go nodes {N}: nodes {[o['nodes'] for o in outs]}  "
          f"{'no overrun' if all(o['nodes'] <= N for o in outs) else 'OVERRUN'}")
    rows.append({"pos": "G1", "hard_nodes": N, "nodes": [o["nodes"] for o in outs]})

with open(os.path.join(OUT, "softnodes.json"), "w") as f:
    json.dump({"exe": PC, "rows": rows}, f, indent=1)
print("\nwrote softnodes.json")
