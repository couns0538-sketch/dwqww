#!/usr/bin/env python3
"""clock_onset.py EXE LABEL : find the exact clock at which the draw shortcut starts, on the PC build.

S-F3 fires at clock 99. Is 99 the FIRST clock at which it fires, or does it start earlier and I only
happened to test 98 and 99? Sweep clock 90..100 on one board under PC20, Threads 1, Hash 16, depth 10, and
report score + nodes for each. A shortcut shows as a sudden collapse in nodes AND a score of exactly 0.

Interpretation of the real rule: with halfmove clock c, the fifty-move draw happens when the clock REACHES
100, i.e. after (100 - c) more non-resetting plies. A position at clock c is NOT drawn if any line contains a
capture or pawn move before then. So score 0 is only right if all lines are non-resetting.
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
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE, LABEL = sys.argv[1], sys.argv[2]
TPL = sys.argv[3] if len(sys.argv) > 3 else \
    "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - {c} 1"
DEPTH = int(sys.argv[4]) if len(sys.argv) > 4 else 10


def run(fen):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14 + PC20_EXTRA:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"go depth {DEPTH}\n"); p.stdin.flush()
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


print(f"### {LABEL} — clock onset sweep, Threads 1, Hash 16, depth {DEPTH}")
print(f"{'clock':>5} {'score':>12} {'nodes':>8} {'best':>6} {'resets':>7}  note")
for c in range(90, 101):
    fen = TPL.format(c=c)
    sc, bm, nd = run(fen)
    b = chess.Board(fen)
    resets = sum(1 for m in b.legal_moves
                 if b.is_capture(m) or b.piece_type_at(m.from_square) == chess.PAWN)
    note = ""
    if sc == ("cp", 0):
        note = "DRAW ANSWER"
        if c < 100:
            note += " one-or-more plies EARLY" if resets else " (no reset moves: could be a real draw line)"
    print(f"{c:>5} {str(sc):>12} {nd:>8} {str(bm):>6} {resets:>7}  {note}")
