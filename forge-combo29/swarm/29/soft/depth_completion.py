#!/usr/bin/env python3
"""Q2 of the softnodes area, tested properly rather than assumed: does a `go softnodes N` search stop at a
COMPLETED iteration?

Method: run the same position with `go softnodes N` and with `go depth D` for the D it reported, on fresh processes.
If softnodes stopped at a completed depth, the final score, node count and move must equal the plain depth-D search
-- EXCEPT that the plain search may continue past D (it does not stop at D if nothing stops it, so use D exactly).

A mismatch means the softnodes search ended mid-iteration at a depth that a plain search reaches differently, which
would be the defect this question is looking for.
"""
import subprocess, sys

EXE = sys.argv[1]
FENS = [l.strip() for l in open(sys.argv[2]) if l.strip()]
NS = [2000, 20000, 50000]

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def go(fen, cmd):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    def send(s):
        p.stdin.write(s + "\n"); p.stdin.flush()
    send("uci")
    for line in p.stdout:
        if line.startswith("uciok"): break
    send("setoption name Hash value 16"); send("setoption name Threads value 1")
    for k, v in PC20: send(f"setoption name {k} value {v}")
    send("isready")
    for line in p.stdout:
        if line.startswith("readyok"): break
    send(f"position fen {fen}")
    send(cmd)
    last = None; bm = None
    for line in p.stdout:
        if line.startswith("info depth"): last = line.rstrip()
        if line.startswith("bestmove"): bm = line.split()[1]; break
    send("quit"); p.wait(timeout=120)
    if last is None: raise SystemExit(f"ABORT: no info line for {cmd}")
    f = last.split()
    return {
        "depth": int(f[2]),
        "nodes": int(f[f.index("nodes") + 1]),
        "score": tuple(f[f.index("score") + 1:f.index("score") + 3]),
        "move": bm,
        "pv": tuple(f[f.index("pv") + 1:]) if "pv" in f else (),
    }


print("Does `go softnodes N` stop at a COMPLETED depth? Compared against `go depth D` at its own D.")
bad = 0
for fen in FENS:
    print(f"\n=== {fen[:56]}")
    for n in NS:
        s = go(fen, f"go softnodes {n}")
        d = go(fen, f"go depth {s['depth']}")
        same = (s["score"] == d["score"] and s["move"] == d["move"] and s["pv"] == d["pv"])
        if not same: bad += 1
        print(f"  softnodes {n:>6} -> depth {s['depth']:>2} nodes {s['nodes']:>6} score {s['score']} move {s['move']}")
        print(f"  go depth {s['depth']:>2}       -> depth {d['depth']:>2} nodes {d['nodes']:>6} score {d['score']} move {d['move']}  "
              f"{'IDENTICAL' if same else '*** DIFFERENT ***'}")
        if not same and s["pv"] != d["pv"]:
            print(f"      softnodes pv {s['pv'][:6]}")
            print(f"      depth pv    {d['pv'][:6]}")
print()
print(f"MID-ITERATION STOPS (softnodes result not reproducible by a plain depth search): {bad}")
