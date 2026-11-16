#!/usr/bin/env python3
"""experiment4.py EXE : count how many ROOT MOVES the search actually evaluates at clock 99 vs clock 98.

Experiment 1 showed pv_len stays 1 on the breaking board and grows on the fine board. Experiment 3 showed the
reset moves ARE searchable in isolation. So the question is: how many of the 27 root moves does the root
actually get through before it settles on score 0?

There is a committed counter for exactly this: the engine's root move effort. If unavailable, count via
`searchmoves` on the full move list one at a time and compare each move's own score with the root's 0.

This script takes the practical route: for EVERY legal root move, do a restricted depth-6 search and record
the score. Then compare with the unrestricted root score. If the root reports 0 while the individual moves
report a spread of values including large positives, then the root's 0 is not the maximum of its children —
which is the defect, stated exactly.
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
FEN = sys.argv[2] if len(sys.argv) > 2 else "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 99 1"
DEPTH = 6


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
    p.stdin.write(f"{go}\n"); p.stdin.flush()
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
    toks = (last or "").split()
    pv = toks[toks.index("pv") + 1:] if "pv" in toks else []
    return ((m.group(1), int(m.group(2))) if m else None), best, len(pv)


b = chess.Board(FEN)
print(f"FEN {FEN}")
print(f"clock {b.halfmove_clock}, legal {b.legal_moves.count()}")
root_sc, root_bm, root_pv = run(f"go depth {DEPTH}")
print(f"UNRESTRICTED root: score {root_sc}, bestmove {root_bm}, pv {root_pv} plies")
print()
print("each root move searched ALONE (restricted), same depth, same settings:")
scores = []
for m in b.legal_moves:
    sc, bm, pv = run(f"go depth {DEPTH} searchmoves {m.uci()}")
    is_reset = b.is_capture(m) or b.piece_type_at(m.from_square) == chess.PAWN
    scores.append((m.uci(), sc, is_reset))
    mark = "reset" if is_reset else "quiet"
    print(f"  {m.uci():<6} {mark:<6} -> {str(sc):>12}  pv {pv}")

vals = [s for _, s, _ in scores if s and s[0] == "cp"]
print()
if vals:
    best_child = max(vals, key=lambda x: x[1])
    print(f"best single-move score seen: {best_child}   |  root reports: {root_sc}")
    if root_sc and best_child[1] != root_sc[1]:
        print("DEFECT CONFIRMED: the root's reported score is NOT the best score among its own children.")
    else:
        print("root score equals the best child score: consistent")
