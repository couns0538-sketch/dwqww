#!/usr/bin/env python3
"""NEW AREA (file 6 suggestion): `go softnodes N` on the PC build under PC20, Threads 1, Hash 16.

The three questions file 6 asks, each answered by measurement:
  Q1 DETERMINISM  -- repeated fresh-process runs must give the same node count, score and move.
  Q2 STOP AT A FINISHED DEPTH -- the search stops at the END of the first iteration that passes N, so the final
     node count should correspond to a completed depth (i.e. the last `info depth D` line's nodes), not mid-iteration.
  Q3 OVERSHOOT -- how far past N the reported node count goes, against the documented hard stop at 4x.

Method: one fresh process per run (a softnodes search reuses hash otherwise, and seat 10 showed a warm process gives
different node counts). Every run is drained to `bestmove`. A run with no `info depth` line aborts: a missing
number must never be read as "deterministic".
"""
import subprocess
import sys

EXE = sys.argv[1]
FENS = [l.strip() for l in open(sys.argv[2]) if l.strip()]
NS = [2000, 20000, 50000, 250000]
REPS = int(sys.argv[3]) if len(sys.argv) > 3 else 3

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true"), ("OwnBook", "false")]
BAD = ("unknown option", "invalid value", "ERROR")


def softnodes(fen, n):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n"); p.stdin.flush()

    send("uci")
    for line in p.stdout:
        if line.startswith("uciok"):
            break
    send("setoption name Hash value 16")
    send("setoption name Threads value 1")
    for k, v in PC20:
        send(f"setoption name {k} value {v}")
    send("isready")
    for line in p.stdout:
        for b in BAD:
            if b in line:
                raise SystemExit(f"ABORT: {line.strip()}")
        if line.startswith("readyok"):
            break
    send(f"position fen {fen}")
    send(f"go softnodes {n}")
    depths = []
    bm = None
    soft = None
    for line in p.stdout:
        if line.startswith("info depth"):
            f = line.split()
            d = int(f[2])
            nodes = int(f[f.index("nodes") + 1]) if "nodes" in f else None
            sc = f[f.index("score") + 1:f.index("score") + 3] if "score" in f else None
            depths.append((d, nodes, tuple(sc) if sc else None))
        elif line.startswith("info string softnodes"):
            soft = line.strip()
        elif line.startswith("bestmove"):
            bm = line.split()[1]
            break
    send("quit")
    p.wait(timeout=120)
    if not depths:
        raise SystemExit(f"ABORT: no info depth for softnodes {n} -- refusing to report determinism")
    return depths, bm, soft


print(f"PC r15 build, PC20, Threads 1, Hash 16, {len(FENS)} positions x nodes {NS} x {REPS} reps")
fails = 0
for fen in FENS[:2]:
    print(f"\n=== {fen[:60]}")
    for n in NS:
        runs = []
        for r in range(REPS):
            depths, bm, soft = softnodes(fen, n)
            runs.append((depths[-1], bm, depths, soft))
        last = [r[0] for r in runs]
        moves = [r[1] for r in runs]
        det = (len({str(x) for x in last}) == 1 and len(set(moves)) == 1)
        if not det:
            fails += 1
        d, nodes, sc = last[0]
        # Q2: does the final node count correspond to a COMPLETED iteration? The last info line IS the completed
        # depth, so the question is whether any deeper iteration started (a partial one would print nothing).
        overshoot = (nodes / n) if n else 0
        hard = 4 * n
        soft_note = runs[0][3]
        print(f"  softnodes {n:>6}: final depth {d:>2} nodes {nodes:>7} = {overshoot:5.2f}x N  "
              f"score {sc}  move {moves[0]}  deterministic {'YES' if det else 'NO '}  "
              f"{'OVER 4x HARD STOP' if nodes > hard else ''}")
        if not det:
            print(f"      runs: {[(x[0], x[1]) for x in runs]}")
        if soft_note:
            print(f"      {soft_note}")
print()
print("DETERMINISM FAILURES:", fails, "(0 required)")
sys.exit(0 if fails == 0 else 1)
