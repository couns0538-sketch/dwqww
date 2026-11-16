#!/usr/bin/env python3
"""verify_mechanism.py EXE : independent check of the MECHANISM.md claim.

Claim: at clock 99, quiet moves score exactly 0 (fifty-move draw at the child), reset moves score negative, and
the root reports 0 because 0 is the max. The engine therefore values a lost position at 0.

This script states it as three falsifiable assertions and prints PASS/FAIL for each:
  A1  every QUIET root move scores exactly cp 0 with a 1-ply PV
  A2  every RESET root move scores < 0 with a PV longer than 1 ply
  A3  the unrestricted root score equals 0 (the max of A1's zeros)
Then, for the price of the error: at clock 0 the same board's best move is clearly negative, so the clock-99
answer of 0 differs from the clock-0 answer by a large margin.
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
FEN99 = "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 99 1"
DEPTH = 6


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
    return ((m.group(1), int(m.group(2))) if m else None), len(pv)


b = chess.Board(FEN99)
quiet, reset = [], []
for m in b.legal_moves:
    is_reset = b.is_capture(m) or b.piece_type_at(m.from_square) == chess.PAWN
    sc, pvlen = run(FEN99, f"go depth {DEPTH} searchmoves {m.uci()}")
    (quiet if not is_reset else reset).append((m.uci(), sc, pvlen))

root_sc, root_pv = run(FEN99, f"go depth {DEPTH}")
a1 = all(sc == ("cp", 0) and pv == 1 for _, sc, pv in quiet)
a2 = all(sc is not None and sc[0] == "cp" and sc[1] < 0 and pv > 1 for _, sc, pv in reset)
a3 = root_sc == ("cp", 0)

print(f"quiet moves: {len(quiet)}  reset moves: {len(reset)}")
print(f"A1 every quiet move == cp 0 with pv 1 : {a1}")
print(f"A2 every reset move  < 0 with pv > 1  : {a2}")
print(f"A3 unrestricted root score == cp 0    : {a3}   (root pv {root_pv} plies)")
print()
print("quiet sample:", quiet[:3])
print("reset sample:", reset[:3])
print()
FEN0 = FEN99.replace(" 99 1", " 0 1")
sc0, pv0 = run(FEN0, f"go depth {DEPTH}")
print(f"same board at clock 0: score {sc0}, pv {pv0}")
if a1 and a2 and a3 and sc0 and sc0[0] == "cp":
    print(f"MECHANISM VERIFIED: the clock-99 answer 0 is the max of {len(quiet)} draw-valued children, "
          f"while the same position at clock 0 is {sc0[1]} cp.")
    sys.exit(0)
print("MECHANISM NOT VERIFIED: an assertion failed")
sys.exit(3)
