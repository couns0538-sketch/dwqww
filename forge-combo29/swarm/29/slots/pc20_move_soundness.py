#!/usr/bin/env python3
"""Is the PC20 tree SMALLER because it prunes soundly, or because it misses moves?

29-F40-F42 showed PC20 searches 12-20 % fewer nodes than S14 at match depths. That is only good news if the answer
is the same or better. This measures, on real-game positions at a fixed depth:
  1. how often the two regimes return the SAME bestmove,
  2. for positions where they differ, which move wins a head-to-head at a deeper fixed depth under S14
     (the neutral regime, so the tiebreak is not judged by the same switches that caused the difference).

Fresh process per search, Threads 1, Hash 16, drained to bestmove. Aborts if any search yields no bestmove.

Output: a summary table plus the list of disagreements with their head-to-head verdict, so a disagreement cannot be
silently counted as a win either way.
"""
import subprocess
import sys

EXE = sys.argv[1]
FENS = [l.strip() for l in open(sys.argv[2]) if l.strip()]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 40
DEPTH = int(sys.argv[4]) if len(sys.argv) > 4 else 12
JUDGE_DEPTH = DEPTH + 4

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def search(fen, settings, cmd):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    send("uci")
    for line in p.stdout:
        if line.startswith("uciok"):
            break
    send("setoption name Hash value 16")
    send("setoption name Threads value 1")
    for k, v in settings:
        send(f"setoption name {k} value {v}")
    send("isready")
    for line in p.stdout:
        if line.startswith("readyok"):
            break
    send(f"position fen {fen}")
    send(cmd)
    last = bm = None
    for line in p.stdout:
        if line.startswith("info depth"):
            last = line.rstrip()
        if line.startswith("bestmove"):
            bm = line.split()[1]
            break
    send("quit")
    p.wait(timeout=600)
    if bm is None or last is None:
        raise SystemExit(f"ABORT: incomplete search for {fen[:40]} under {cmd}")
    f = last.split()
    return bm, tuple(f[f.index("score") + 1:f.index("score") + 3])


fens = FENS[:N]
same = diff = 0
disagreements = []
for i, fen in enumerate(fens, 1):
    m14, s14 = search(fen, S14, f"go depth {DEPTH}")
    m20, s20 = search(fen, PC20, f"go depth {DEPTH}")
    if m14 == m20:
        same += 1
    else:
        diff += 1
        # Head-to-head: play each move under the NEUTRAL regime (S14) one ply deeper, and take the mover's score.
        # The engine reports the score for the side to move after the move is played, so negate it.
        r14 = search_after = None
        p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

        def send(c, p=p):
            p.stdin.write(c + "\n")
            p.stdin.flush()

        send("uci")
        for line in p.stdout:
            if line.startswith("uciok"):
                break
        send("setoption name Hash value 16")
        send("setoption name Threads value 1")
        for k, v in S14:
            send(f"setoption name {k} value {v}")
        send("isready")
        for line in p.stdout:
            if line.startswith("readyok"):
                break
        send(f"position fen {fen} moves {m14}")
        send(f"go depth {JUDGE_DEPTH - 1}")
        last = None
        for line in p.stdout:
            if line.startswith("info depth"):
                last = line.rstrip()
            if line.startswith("bestmove"):
                break
        f = last.split()
        sc14 = f[f.index("score") + 1:f.index("score") + 3]
        send(f"position fen {fen} moves {m20}")
        send(f"go depth {JUDGE_DEPTH - 1}")
        last = None
        for line in p.stdout:
            if line.startswith("info depth"):
                last = line.rstrip()
            if line.startswith("bestmove"):
                break
        f = last.split()
        sc20 = f[f.index("score") + 1:f.index("score") + 3]
        send("quit")
        p.wait(timeout=600)
        disagreements.append((i, fen, m14, s14, m20, s20, tuple(sc14), tuple(sc20)))

print(f"{len(fens)} positions, depth {DEPTH}, Threads 1, Hash 16; disagreements judged at depth {JUDGE_DEPTH - 1} under S14")
print()
print(f"| result | count | share |")
print("|---|---|---|")
print(f"| SAME bestmove | {same} | {100.0*same/len(fens):.1f} % |")
print(f"| DIFFERENT bestmove | {diff} | {100.0*diff/len(fens):.1f} % |")
if disagreements:
    print()
    print("| pos | S14 move (score) | PC20 move (score) | after S14 move | after PC20 move |")
    print("|---|---|---|---|---|")
    for i, fen, m14, s14, m20, s20, a, b in disagreements:
        print(f"| {i} | {m14} {s14[0]} {s14[1]} | {m20} {s20[0]} {s20[1]} | {a[0]} {a[1]} | {b[0]} {b[1]} |")
