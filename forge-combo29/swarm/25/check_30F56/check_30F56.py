#!/usr/bin/env python3
"""check_30F56.py EXE : is a self-play game reproducible across processes from the same start?

Seat 30's 30-F56: "a game from a given start is reproducible across processes (identical SHA of the move list);
the sample size of a fixed-depth match is the number of OPENINGS, not the number of games."

The first half is testable directly and cheaply, and it matters because it decides whether a self-play match can be
analysed as N independent games or only as N/2 independent openings (both colours from each start).
My S-F30/S-F31 played games at `go nodes 20000` deterministically; this asks the specific question: SAME move list
byte-for-byte when replayed in a fresh process?

Test: play a short game from one start twice, in two separate processes, and compare the move lists exactly.
Also do it from a SECOND start, to make sure reproducibility is not luck with one board.
"""
import hashlib
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
STARTS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
]
PLIES = 14


def one_move(fen):
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
    p.stdin.write("go nodes 20000\n"); p.stdin.flush()
    best = None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        p.kill()
    return best


def play_game(start):
    b = chess.Board(start)
    moves = []
    for _ in range(PLIES):
        if b.is_game_over(claim_draw=True):
            break
        mv = one_move(b.fen())
        if not mv or mv == "0000":
            break
        try:
            m = chess.Move.from_uci(mv)
        except ValueError:
            break
        if m not in b.legal_moves:
            break
        b.push(m)
        moves.append(mv)
    return moves


print("### 30-F56: is a self-play game reproducible across fresh processes?")
for start in STARTS:
    g1 = play_game(start)
    g2 = play_game(start)
    h1 = hashlib.sha256(" ".join(g1).encode()).hexdigest()[:16]
    h2 = hashlib.sha256(" ".join(g2).encode()).hexdigest()[:16]
    print()
    print(f"start: {start}")
    print(f"  run 1 ({len(g1)} plies): {' '.join(g1)}")
    print(f"  run 2 ({len(g2)} plies): {' '.join(g2)}")
    print(f"  sha run1={h1}  run2={h2}  IDENTICAL={h1 == h2}")
