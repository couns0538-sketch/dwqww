#!/usr/bin/env python3
"""check_05F14.py EXE : check seat 05's S-F14 claim about MY board.

Seat 05's S-F14 says (paraphrased): the fifty-move boundary is POSITION-dependent, not one rule; and
specifically "seat 25's 21-piece middlegame sits flat at 99 for d6..d12" while "the SAME middlegame with all
12 pawns removed sits flat at 100 for d4..d10".

That is a claim ABOUT MY BOARD (the r4rk1/pp1b1ppp/... position). It is also the family file 6 reclassified, so
it is description, not defect. But the specific numbers are checkable and worth confirming or refuting:
  C1  is the board a 21-piece middlegame, and does it score cp 0 at counter 99 for depths 6..12 on the PC build?
  C2  with all pawns removed, does the same board score cp 0 at counter 100 (not 99) for depths 4..10?
If both hold, S-F14's position-dependence claim reproduces on a build and setting it was not measured on.
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
MID = "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - {c} 1"


def run(fen, depth):
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
    last = None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            last = s
        if s.startswith("bestmove"):
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    m = re.search(r"score (cp|mate) (-?\d+)", last or "")
    return (m.group(0) if m else "?")


b = chess.Board(MID.format(c=0))
print(f"board: {b.fen()}")
print(f"pieces on the board: {len(b.piece_map())} (seat 05 says 21-piece middlegame)")
print("  ->", "CONSISTENT" if len(b.piece_map()) == 21 else f"NOT 21, it has {len(b.piece_map())}")
print()
print("C1: this board at counter 99, depths 6..12 (seat 05 says 'sits flat at 99')")
ok1 = True
for d in range(6, 13):
    sc = run(MID.format(c=99), d)
    flat = sc == "score cp 0"
    ok1 &= flat
    print(f"   depth {d:>2}: {sc:>10} {'flat cp 0' if flat else '<-- NOT flat'}")
print(f"   C1 verdict: {"CONFIRMED flat" if ok1 else "NOT confirmed as flat"}")
print()

# C2: remove all pawns from that board
pawnless = chess.Board(None)
for sq, pc in b.piece_map().items():
    if pc.piece_type != chess.PAWN:
        pawnless.set_piece_at(sq, pc)
pawnless.turn = b.turn
pawnless.clear_stack()
print(f"C2: same board with all pawns removed: {pawnless.fen()}")
print(f"   pieces now: {len(pawnless.piece_map())}")
print("   seat 05 says this sits flat at COUNTER 100 for depths 4..10 (not 99).")
for c in (99, 100):
    for d in range(4, 11):
        sc = run(pawnless.fen().replace(" 0 1", f" {c} 1"), d)
        print(f"   counter {c}, depth {d:>2}: {sc}")
    print()
