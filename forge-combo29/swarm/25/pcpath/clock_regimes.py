#!/usr/bin/env python3
"""clock_regimes.py EXE : the clock regimes I have not exercised, with the S-C15 determinism caveat in mind.

Regimes:
  R1 movestogo given            `go wtime 6000 btime 6000 movestogo 10`   (time manager uses a different formula)
  R2 increment only, no time    `go wtime 0 btime 0 winc 1000 binc 1000`   (pathological but legal)
  R3 very short clock           `go wtime 50 btime 50 winc 0 binc 0`       (must still answer, preferably legally)
  R4 time 0 no increment        `go wtime 0 btime 0 winc 0 binc 0`         (the extreme case)
For each: score, nodes, depth, move, wall time, and whether the move is LEGAL — the last is the only thing that
must hold for a match not to break.

Because S-C15 showed clock searches vary run to run in score/nodes, this runs 3 times per regime and reports the
MOVE stability separately from the score stability.
"""
import re
import shlex
import subprocess
import sys
import time

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
        ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE = sys.argv[1]
FEN = "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4"
REGIMES = [
    ("R1 movestogo 10", "go wtime 6000 btime 6000 movestogo 10"),
    ("R2 increment only", "go wtime 0 btime 0 winc 1000 binc 1000"),
    ("R3 very short 50ms", "go wtime 50 btime 50 winc 0 binc 0"),
    ("R4 zero time", "go wtime 0 btime 0 winc 0 binc 0"),
]


def run(go):
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
    p.stdin.write(f"position fen {FEN}\nisready\n"); p.stdin.flush(); until("readyok")
    t0 = time.monotonic()
    p.stdin.write(f"{go}\n"); p.stdin.flush()
    last, best = None, None
    try:
        while True:
            line = p.stdout.readline()
            if not line:
                break
            s = line.rstrip("\n")
            if s.startswith("info depth"):
                last = s
            if s.startswith("bestmove"):
                best = s.split()[-1]
                break
    except Exception:
        pass
    ms = (time.monotonic() - t0) * 1000.0
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=15)
    except subprocess.TimeoutExpired:
        p.kill()
    m = re.search(r"score (cp|mate) (-?\d+)", last or "")
    n = re.search(r"nodes (\d+)", last or "")
    d = re.search(r"depth (\d+)", last or "")
    return {"score": m.group(0) if m else "?", "nodes": int(n.group(1)) if n else 0,
            "depth": int(d.group(1)) if d else 0, "move": best, "ms": round(ms)}


b = chess.Board(FEN)
print(f"### clock regimes not yet exercised — PC r15/PC20, Threads 1, Hash 16")
print(f"position: {FEN}")
print()
print(f"{'regime':<20} {'score':>11} {'nodes':>7} {'dep':>4} {'ms':>6} {'move':>6} {'legal':>6} {'move-stable':>12}")
for name, go in REGIMES:
    rs = [run(go) for _ in range(3)]
    r = rs[0]
    legal = False
    if r["move"] and r["move"] != "0000":
        try:
            legal = chess.Move.from_uci(r["move"]) in b.legal_moves
        except ValueError:
            legal = False
    stable = len({x["move"] for x in rs}) == 1
    print(f"{name:<20} {r['score']:>11} {r['nodes']:>7} {r['depth']:>4} {r['ms']:>6} "
          f"{str(r['move']):>6} {str(legal):>6} {str(stable):>12}")
    if not legal:
        print(f"    NOT A LEGAL MOVE — investigate: {r['move']}")
