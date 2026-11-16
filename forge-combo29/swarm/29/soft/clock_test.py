#!/usr/bin/env python3
"""PC-path job: the clock the owner's PC actually uses -- `go wtime 6000 btime 6000 winc 60 binc 60` --
on the PC r15 build under PC20, Threads 1, Hash 16.

File 6 names this as one of the four things the PC really does (its strength matches), so a defect here counts most.

Measures, per position, from a monotonic clock around the go->bestmove exchange:
  - wall time, and whether the engine overran the time it allocated to itself,
  - whether the move is legal and the process exited cleanly,
  - whether the search is deterministic (same move twice) at Threads 1.

Threads are 1 throughout, per the swarm rule: scores from >1 thread are not trustworthy.
"""
import subprocess
import sys
import time

EXE = sys.argv[1]
FENS = [l.strip() for l in open(sys.argv[2]) if l.strip()]
WTIME, WINC = 6000, 60
REPS = int(sys.argv[3]) if len(sys.argv) > 3 else 2

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def go_clock(fen):
    """One fresh process, one clocked go, wall time from sending `go` to reading `bestmove`."""
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

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
        if line.startswith("readyok"):
            break
    send(f"position fen {fen}")
    t0 = time.monotonic()
    send(f"go wtime {WTIME} btime {WTIME} winc {WINC} binc {WINC}")
    depths = []
    bm = None
    for line in p.stdout:
        if line.startswith("info depth"):
            depths.append(line.rstrip())
        if line.startswith("bestmove"):
            bm = line.split()[1]
            break
    ms = (time.monotonic() - t0) * 1000.0
    send("quit")
    p.wait(timeout=120)
    if bm is None:
        raise SystemExit(f"ABORT: no bestmove for {fen} -- hanging search")
    if not depths:
        raise SystemExit(f"ABORT: no info depth for {fen} -- nothing measured")
    f = depths[-1].split()
    return {
        "ms": ms,
        "depth": int(f[2]),
        "nodes": int(f[f.index("nodes") + 1]),
        "score": tuple(f[f.index("score") + 1:f.index("score") + 3]),
        "move": bm,
    }


def legal(fen, mv):
    import chess
    b = chess.Board(fen)
    if mv == "0000":
        return not any(b.legal_moves)
    return chess.Move.from_uci(mv) in b.legal_moves


print(f"PC r15 build, PC20, Threads 1, Hash 16, clock {WTIME}+{WINC}ms, {len(FENS)} positions x {REPS} reps")
print()
print("| pos | rep | wall ms | depth | nodes | score | move | legal |")
print("|---|---|---|---|---|---|---|---|")
times = []
moves = {}
bad = 0
for i, fen in enumerate(FENS, 1):
    for r in range(REPS):
        g = go_clock(fen)
        ok = legal(fen, g["move"])
        if not ok:
            bad += 1
        times.append(g["ms"])
        moves.setdefault(i, set()).add(g["move"])
        print(f"| {i} | {r+1} | {g['ms']:.0f} | {g['depth']} | {g['nodes']} | {g['score'][0]} {g['score'][1]} | "
              f"{g['move']} | {'YES' if ok else '**NO**'} |")
times.sort()
nondet = [i for i, s in moves.items() if len(s) > 1]
print()
print(f"wall ms: min {times[0]:.0f}  median {times[len(times)//2]:.0f}  max {times[-1]:.0f}  "
      f"(budget {WTIME} ms)")
print(f"searches over the 6000 ms budget: {sum(1 for t in times if t > WTIME)} of {len(times)}")
print(f"illegal or missing moves: {bad}")
print(f"positions whose move differed between reps (Threads 1, so this would be a real nondeterminism): {nondet or 'none'}")
