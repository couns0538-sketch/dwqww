#!/usr/bin/env python3
"""check_16F29.py EXE FENS : does varying the START fix self-play duplication?

SEAT 16's S-F29, which I am checking:
  Ten games from ten DIFFERENT real-game positions give TEN distinct final positions and TEN distinct move sequences,
  against 3-of-10 from a single fixed start. So the convergence was the fixed starting point, not a deeper search
  property - the advice is simply "vary the openings".

WHY I AM WELL PLACED TO CHECK THIS: my S-C36 confirmed games are byte-identical on replay from one start, and my S-C37
found the two COLOUR games from one opening are different but correlated. Seat 16's claim is the practical remedy on
top of both: different STARTINGS, not different colours, restore variety.

MY CHECK, using the match clock they used (6 s + 0.06):
  A  ten games from ONE start          -> how many distinct final positions / move sequences?
  B  ten games from TEN different starts -> how many distinct?
Fewer plies than their 40 to keep it affordable (I use 20), which is a deliberate difference I state.
"""
import hashlib
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
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE, FENS = sys.argv[1], sys.argv[2]
PLIES = 20


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
    for n, v in S14 + PC20_EXTRA:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("go wtime 6000 btime 6000 winc 60 binc 60\n"); p.stdin.flush()
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
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    return best


def play(start):
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
    return moves, b.fen()


fens = [l.split(";")[0].strip() for l in open(FENS) if l.strip()]
print(f"### 16-F29 check: does varying the START fix duplication? ({PLIES} plies/game, 6 s + 0.06 clock)")
print(f"PC20, Threads 1, Hash 16, fresh process per move")
print()

print("A: ten games from ONE start")
one = fens[0]
seqs_one, finals_one = set(), set()
illegal = 0
for i in range(10):
    moves, final = play(one)
    if not moves:
        illegal += 1
    seqs_one.add(hashlib.sha256(" ".join(moves).encode()).hexdigest()[:8])
    finals_one.add(final)
print(f"   start: {one}")
print(f"   distinct move sequences: {len(seqs_one)} of 10")
print(f"   distinct final positions: {len(finals_one)} of 10")

print()
print("B: ten games from TEN different starts")
seqs_ten, finals_ten = set(), set()
for i in range(10):
    moves, final = play(fens[i])
    seqs_ten.add(hashlib.sha256(" ".join(moves).encode()).hexdigest()[:8])
    finals_ten.add(final)
print(f"   distinct move sequences: {len(seqs_ten)} of 10")
print(f"   distinct final positions: {len(finals_ten)} of 10")

print()
print("seat 16 claim: single fixed start gives 3-of-10 distinct; varied starts give 10-of-10.")
print(f"my result: single start {len(seqs_one)}/10 ; varied starts {len(seqs_ten)}/10")
