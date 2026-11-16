#!/usr/bin/env python3
"""pawns_test.py EXE -- tests the hypothesis from raw/mechanism_diff.txt: does the difference between MY
boundary (moves with depth) and seat 25's boundary (fixed at 99) come down to whether the search can REACH
clock 100, i.e. whether the position has pawns/captures that reset the counter?

Design: take seat 25's board and progressively strip the pawns, keeping a legal position each time, and measure
whether the clock boundary moves with depth. If the hypothesis is right, the boundary should start fixed (with
pawns) and become depth-tracking (without them).
"""
import re
import subprocess
import sys

import chess

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-rel/forge"
S14 = ["setoption name Threads value 1", "setoption name Hash value 16",
       "setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
       "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
       "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
       "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
       "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
       "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
       "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true"]

THEIR = "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 0 1"


def strip_pawns(fen):
    """remove every pawn, keep the rest; return a legal FEN or None"""
    b = chess.Board(fen)
    for sq, piece in list(b.piece_map().items()):
        if piece.piece_type == chess.PAWN:
            b.remove_piece_at(sq)
    b.castling_rights = chess.BB_EMPTY
    b.ep_square = None
    b.clear_stack()
    b.halfmove_clock = 0
    b.fullmove_number = 1
    if not b.is_valid():
        return None
    return b.fen()


def with_clock(fen, c):
    q = fen.split()
    q[4] = str(c)
    return " ".join(q)


def run(fen, depth):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)
    out = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    send("uci")
    for o in S14:
        send(o); send("isready")
    send("ucinewgame"); send("isready")
    send(f"position fen {fen}"); send("isready")
    send(f"go depth {depth}")
    while True:
        line = p.stdout.readline()
        if line == "":
            break
        line = line.rstrip("\n")
        out.append(line)
        if any(b in line for b in ("unknown option", "invalid value", "invalid FEN")):
            send("quit")
            p.kill()
            return None
        if line.startswith("bestmove"):
            break
    send("quit")
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    pv = [l for l in out if re.search(r"\binfo\b.*\bpv\b", l)]
    if not pv:
        return None
    m = re.search(r"score (mate|cp) (-?\d+)", pv[-1])
    return f"{m.group(1)} {m.group(2)}" if m else None


def boundary(fen, depth):
    """lowest clock in 60..100 that scores cp 0"""
    for c in range(60, 101):
        sc = run(with_clock(fen, c), depth)
        if sc is None:
            return "PARSE-FAIL"
        if sc == "cp 0":
            return c
    return ">100"


pawnless = strip_pawns(THEIR)
if pawnless is None:
    print("could not make a legal pawnless version of seat 25's board")
    sys.exit(1)

b = chess.Board(THEIR)
print(f"exe: {EXE}")
print(f"seat 25's board  ({b.piece_map().__len__()} pieces, 12 pawns): {THEIR}")
print(f"pawnless version ({chess.Board(pawnless).piece_map().__len__()} pieces, 0 pawns): {pawnless}")
print()
print("| board | depth 4 | depth 6 | depth 8 | depth 10 | clock+depth at d10 |")
print("|---|---|---|---|---|---|")
for label, fen in (("seat 25 (with pawns)", THEIR), ("pawnless", pawnless)):
    vals = []
    for d in (4, 6, 8, 10):
        vals.append(boundary(fen, d))
    last = vals[-1]
    cd = (last + 10) if isinstance(last, int) else "-"
    print(f"| {label} | {vals[0]} | {vals[1]} | {vals[2]} | {vals[3]} | {cd} |")
print()
print("Hypothesis test: if the boundary is CONSTANT across depths for the pawned board but FALLS with depth for")
print("the pawnless one, the difference is about reaching the counter, as raw/mechanism_diff.txt proposed.")
print("If both are constant, or both fall, the hypothesis is wrong and I will say so.")
