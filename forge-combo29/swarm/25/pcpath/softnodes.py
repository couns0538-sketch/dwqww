#!/usr/bin/env python3
"""softnodes.py EXE : the `go softnodes` question file 6 raises (new-area suggestion).

File 6's question, verbatim in effect: "`go softnodes N` on the PC build under PC20, Threads 1: is it
deterministic run to run (it must be), does it stop at a finished depth, and how far past N does it go?"

The owner's self-play uses `go softnodes 2000` (stops at the end of the first depth after 2,000 nodes). So
determinism here is a training-data property, not a cosmetic one.

Tests per position:
  T1  determinism: three runs of `go softnodes 2000` in three fresh processes -> identical score/nodes/move?
  T2  does it overshoot: the node count reported vs N, and the ratio
  T3  does it stop at a FINISHED depth: compare its nodes with the nodes of `go depth d` for the reported d
  T4  `go softnodes` with N where the search finishes all depths: what happens at a very large N
"""
import re
import shlex
import subprocess
import sys

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
        ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE = sys.argv[1]
POSITIONS = [
    "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4",
    "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1",
    "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 0 1",
]


def run(fen, go):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14 + PC20:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"{go}\n"); p.stdin.flush()
    last, best, depth = None, None, 0
    unknown = []
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if "unknown" in s.lower() or "invalid" in s.lower():
            unknown.append(s)
        if s.startswith("info depth"):
            last = s
            d = re.search(r"depth (\d+)", s)
            if d:
                depth = max(depth, int(d.group(1)))
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    m = re.search(r"score (cp|mate) (-?\d+)", last or "")
    n = re.search(r"nodes (\d+)", last or "")
    return (m.group(0) if m else "?"), (int(n.group(1)) if n else 0), depth, best, unknown


print(f"### go softnodes on {EXE}  (PC20, Threads 1, Hash 16)")
for fen in POSITIONS:
    print("=" * 76)
    print(f"position: {fen}")
    # T1 determinism
    runs = [run(fen, "go softnodes 2000") for _ in range(3)]
    sig = {(r[0], r[1], r[3]) for r in runs}
    print(f"  T1 three runs of softnodes 2000: {[(r[0], r[1], r[3]) for r in runs]}")
    print(f"     deterministic: {len(sig) == 1}   {'' if len(sig) == 1 else '<-- NOT DETERMINISTIC'}")
    if runs[0][4]:
        print(f"     engine complained: {runs[0][4][:2]}")
    # T2 overshoot
    sc, nodes, depth, bm, _ = runs[0]
    print(f"  T2 reported nodes {nodes} for N=2000  -> overshoot {nodes / 2000.0:.2f}x")
    # T3 finished depth: is `go depth 64` reached, or does it stop at a depth whose node count matches?
    print(f"  T3 stopped at depth {depth} (a depth limit would be 64)")
    for N in (2000, 20000, 50000, 250000):
        sc2, n2, d2, b2, _ = run(fen, f"go softnodes {N}")
        print(f"     softnodes {N:>6} -> {sc2:>10} nodes {n2:>8} depth {d2:>3} move {b2}"
              f"  overshoot {n2 / N:.2f}x")
