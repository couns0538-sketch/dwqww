#!/usr/bin/env python3
"""pcpath_nodes_clock.py EXE : the rest of the owner's real path.

File 6 says the PC's matches use `go nodes` 20000/50000/250000 and a clock of 6 seconds + 0.06 per move.
For each: determinism (3 fresh runs), depth reached, move, and wall time.

Determinism at Threads 1 is the property that matters: a match result that changes run to run is not a result.
"""
import re
import shlex
import subprocess
import sys
import time

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
]
GOS = ["go nodes 20000", "go nodes 50000", "go nodes 250000",
       "go wtime 6000 btime 6000 winc 60 binc 60"]


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
    t0 = time.monotonic()
    p.stdin.write(f"{go}\n"); p.stdin.flush()
    last, best, depth = None, None, 0
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            last = s
            d = re.search(r"depth (\d+)", s)
            if d:
                depth = max(depth, int(d.group(1)))
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    ms = (time.monotonic() - t0) * 1000.0
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    m = re.search(r"score (cp|mate) (-?\d+)", last or "")
    n = re.search(r"nodes (\d+)", last or "")
    return (m.group(0) if m else "?"), (int(n.group(1)) if n else 0), depth, best, ms


print(f"### the owner's real path on {EXE} (PC20, Threads 1, Hash 16)")
for fen in POSITIONS:
    print("=" * 80)
    print(f"position: {fen}")
    print(f"{'command':<38} {'score':>12} {'nodes':>8} {'depth':>6} {'ms':>7} {'move':>6} {'det?':>5}")
    for go in GOS:
        rs = [run(fen, go) for _ in range(3)]
        sig = {(r[0], r[1], r[3]) for r in rs}
        det = len(sig) == 1
        r = rs[0]
        print(f"{go:<38} {r[0]:>12} {r[1]:>8} {r[2]:>6} {r[4]:>7.0f} {str(r[3]):>6} {str(det):>5}")
        if not det:
            print(f"    NOT DETERMINISTIC: {[(x[0], x[1], x[3]) for x in rs]}")
