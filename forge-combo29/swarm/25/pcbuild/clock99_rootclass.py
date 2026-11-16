#!/usr/bin/env python3
"""clock99_rootclass.py EXE : is V1's clock-99 answer a ROOT draw classification?

Evidence for a root shortcut: the score is 0 at EVERY depth from 1, with a 1-ply PV, and node counts grow
only linearly (30, 58, 87, 115...) i.e. no tree is searched — that is the shape of the `root_drawn` early
return in src/search.cpp:2251-2271, not of a normal search.

The source's root test is `board.halfmove_clock() >= 100`, which CANNOT be true at clock 99. So either
(a) this build reads a different clock than the FEN's halfmove field, or
(b) a different root condition (repetition / insufficient material) is true on V1.

Test both:
  * What clock does the engine see? Put the SAME board at clock 0/50/99/100 and check whether the answer
    pattern tracks the 99/100 boundary (it did earlier: 98 normal, 99 zero) — so it does see the clock.
  * Is V1 a repetition or insufficient-material root? Ask python-chess: is_repetition / is_repetition(2) /
    is_insufficient_material on the FEN.
  * Decisive: give the engine V1 at clock 99 with a DIFFERENT halfmove field but the SAME board — done.
  * And: does the PC build's FORGE_FIX_ROOT_DRAWN change it? (Both builds break, so no.)
Prints all of it; no claim beyond what the numbers say.
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
EXE = sys.argv[1]
BOARD = "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - {c} 1"


def run(fen, depth=6):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name OwnBook value false\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"go depth {depth}\n"); p.stdin.flush()
    infos, best = [], None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            infos.append(s)
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return infos, best


print("python-chess view of V1 at clock 99:")
b = chess.Board(BOARD.format(c=99))
print(f"  is_repetition()      = {b.is_repetition()}")
print(f"  is_repetition(2)     = {b.is_repetition(2)}")
print(f"  is_insufficient()    = {b.is_insufficient_material()}")
print(f"  halfmove_clock       = {b.halfmove_clock}")
print(f"  is_game_over()       = {b.is_game_over()}")
print()

print("engine answer shape at several clocks (depth 6, so the node growth is comparable):")
print(f"{'clock':>6} {'score':>10} {'nodes':>7} {'pvlen':>6} {'shape'}")
for c in (0, 50, 95, 98, 99, 100):
    infos, best = run(BOARD.format(c=c), depth=6)
    m = re.search(r"score (cp|mate) (-?\d+)", infos[-1]) if infos else None
    n = re.search(r"nodes (\d+)", infos[-1]) if infos else None
    toks = infos[-1].split() if infos else []
    pv = toks[toks.index("pv") + 1:] if "pv" in toks else []
    nodes = int(n.group(1)) if n else 0
    shape = "ROOT-SHORTCUT (no tree)" if nodes < 400 else "normal search"
    print(f"{c:>6} {m.group(0) if m else '?':>10} {nodes:>7} {len(pv):>6} {shape}")
