#!/usr/bin/env python3
"""clock99_mechanism.py EXE LABEL : narrow the clock-99 trigger empirically.

The two draw tests in the source (`is_draw` and `root_drawn`) both use `>= 100`, so neither can fire at 99.
This narrows down what actually does, by varying ONE property at a time on the same board at clock 99:

  V1  clock 99 with reset moves present            -> the break (known)
  V2  clock 99 with NO reset moves, quiet only     -> if 0 here too, it may be a legitimate non-resetting line
  V3  clock 99, board slightly changed (a pawn moved so a reset move exists) -> does it recover?
  V4  clock 100                                     -> correct draw, for comparison
  V5  clock 99 but with a capture that is FORCED (only legal move) -> the rule cannot draw, so 0 would be wrong

Also: is the 0 score accompanied by a PV that runs into the fifty-move horizon? Print the PV so the end of the
line can be inspected.
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
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE, LABEL = sys.argv[1], sys.argv[2]


def run(fen, depth=10):
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
    p.stdin.write(f"go depth {depth}\n"); p.stdin.flush()
    last, best = None, None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth") and " pv" in s:
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
    toks = (last or "").split()
    pv = toks[toks.index("pv") + 1:] if "pv" in toks else []
    return ((m.group(1), int(m.group(2))) if m else None), best, (int(n.group(1)) if n else 0), pv


import chess

CASES = [
    ("V1 clock 99, the known board", "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 99 1"),
    ("V4 clock 100 (correct draw)", "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 100 1"),
    ("V3 clock 99, a pawn still on its 2nd rank (more resets)", "r4rk1/pp1b1ppp/4p3/4P3/8/P1P5/1P2N1PP/R2R2K1 w - - 99 1"),
    ("V2 clock 99, kings+rooks only, NO reset move possible", "4k3/8/8/8/8/8/8/R3K2r w - - 99 1"),
]

for name, fen in CASES:
    b = chess.Board(fen)
    resets = sum(1 for m in b.legal_moves
                 if b.is_capture(m) or b.piece_type_at(m.from_square) == chess.PAWN)
    sc, bm, nd, pv = run(fen)
    print(f"### {name}")
    print(f"    FEN: {fen}")
    print(f"    legal {b.legal_moves.count()}, resetting moves {resets}")
    print(f"    -> score {sc}, nodes {nd}, bestmove {bm}, pv {len(pv)} plies")
    if pv:
        print(f"    pv: {' '.join(pv)}")
    print()
