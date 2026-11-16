#!/usr/bin/env python3
"""predict_test.py EXE : a prediction from the mechanism, then the test.

If the mechanism is right (a CLAIMABLE fifty-move draw scored as forced), then:
  P-a  at clock 100 with reset moves available, the engine must ALSO report cp 0 for a lost position,
       because the same clock-100 child test fires - and the opponent there can still decline.
  P-b  at clock 100 with NO reset move available to either side, cp 0 is CORRECT (the draw really is forced
       because nobody can reset), so the engine's 0 there is right.
  P-c  at clock 99 the fault must scale with how many quiet moves exist: a position where MOST moves are quiet
       collapses to 0, and a position where the good moves are resets must NOT (that is board V3, which scored
       597).

A prediction confirmed on all three is strong support for the diagnosis; any failure means the diagnosis is
incomplete.
"""
import re
import shlex
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
        ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE = sys.argv[1]


def run(fen, depth=8):
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
    p.stdin.write(f"go depth {depth}\n"); p.stdin.flush()
    last, best = None, None
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
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    m = re.search(r"score (cp|mate) (-?\d+)", last or "")
    n = re.search(r"nodes (\d+)", last or "")
    return ((m.group(1), int(m.group(2))) if m else None), best, (int(n.group(1)) if n else 0)


def resets_of(fen):
    b = chess.Board(fen)
    return sum(1 for m in b.legal_moves
               if b.is_capture(m) or b.piece_type_at(m.from_square) == chess.PAWN), b


CASES = [
    ("P-a clock 100, resets available, lost position", "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 100 1"),
    ("P-b clock 100, NO reset possible (K+R vs K+R, kings boxed)", "4k3/8/8/8/8/8/8/R3K2r w - - 100 1"),
    ("P-c board V3 clock 99, resets available (was 597)", "r4rk1/pp1b1ppp/4p3/4P3/8/P1P5/1P2N1PP/R2R2K1 w - - 99 1"),
    ("    board A clock 99 (the breaking one)", "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 99 1"),
    ("    board A clock 0 (baseline value)", "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 0 1"),
]

print(f"{'case':<58} {'resets':>6} {'score':>12} {'nodes':>7} best")
for name, fen in CASES:
    r, b = resets_of(fen)
    sc, bm, nd = run(fen)
    print(f"{name:<58} {r:>6} {str(sc):>12} {nd:>7} {bm}")

print()
print("Reading of the predictions:")
print("  P-a: clock 100 with resets available should ALSO be cp 0 (same clock-100 child test).")
print("  P-b: clock 100 with no reset possible -> cp 0 is CORRECT there.")
print("  P-c: V3 (good moves are resets) should stay non-zero; board A should be 0 and clock 0 clearly negative.")
