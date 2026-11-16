#!/usr/bin/env python3
"""clock_determinism.py EXE : is a CLOCK-based search deterministic? (checks my own S-F26 claim)

S-F26 says: "`go nodes 20000/50000/250000` and `go wtime 6000 winc 60` are all 3/3 reproducible in score, node
count and move". The softnodes_clock test just showed det=False twice for the clock row. A clock-based stop is
inherently time-dependent (it stops when the wall clock says so), so nodes SHOULD vary; what might stay fixed is
the move and possibly the score.

This measures 6 runs and reports, per field, how many distinct values appear:
  score, nodes, depth, move
and says which of those my S-F26 claim was wrong about.
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
FENS = [
    "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4",
    "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1",
]
RUNS = 6
GOS = ["go wtime 6000 btime 6000 winc 60 binc 60", "go nodes 20000", "go softnodes 2000"]


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
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    m = re.search(r"score (cp|mate) (-?\d+)", last or "")
    n = re.search(r"nodes (\d+)", last or "")
    return {"score": m.group(0) if m else "?", "nodes": int(n.group(1)) if n else 0,
            "depth": depth, "move": best, "ms": round(ms)}


print(f"### determinism by field, {RUNS} runs each — PC r15/PC20, Threads 1, Hash 16")
for fen in FENS:
    print("=" * 84)
    print(f"position: {fen}")
    for go in GOS:
        rs = [run(fen, go) for _ in range(RUNS)]
        print(f"  {go}")
        for field in ("score", "nodes", "depth", "move", "ms"):
            vals = [r[field] for r in rs]
            distinct = len(set(vals))
            tag = "DETERMINISTIC" if distinct == 1 else f"{distinct} DISTINCT VALUES"
            print(f"     {field:<6} {tag:<22} {sorted(set(map(str,vals)))[:4]}")
