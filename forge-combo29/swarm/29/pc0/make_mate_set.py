#!/usr/bin/env python3
"""Build a MATE-HEAVY position set, which is what the S-F23 truncation question needs.

Strategy: generate positions where a mate is likely (heavy material imbalance with the stronger side to move), then
keep only those where the engine itself reports a mate score at depth 12 under S14. That gives a set where the
truncation rate has a real denominator instead of 19-20 lucky hits in 100 random positions.

Positions are built deterministically from a fixed seed so the set is reproducible.
"""
import random
import subprocess
import sys

EXE = sys.argv[1]
OUT = sys.argv[2]
TARGET = int(sys.argv[3]) if len(sys.argv) > 3 else 40
SEED = 2911

import chess

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]


def score_of(exe, fen):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    def s(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    s("uci")
    for l in p.stdout:
        if l.startswith("uciok"):
            break
    s("setoption name Hash value 16")
    s("setoption name Threads value 1")
    for k, v in S14:
        s(f"setoption name {k} value {v}")
    s("isready")
    for l in p.stdout:
        if l.startswith("readyok"):
            break
    s(f"position fen {fen}")
    s("go depth 12")
    last = None
    for l in p.stdout:
        if l.startswith("info depth"):
            last = l.rstrip()
        if l.startswith("bestmove"):
            break
    s("quit")
    p.wait(timeout=300)
    if last is None:
        return None, None
    f = last.split()
    i = f.index("score")
    return f[i + 1], int(f[i + 2])


rng = random.Random(SEED)
found = []
tried = 0
while len(found) < TARGET and tried < 4000:
    tried += 1
    # stronger side: keep the black king alone-ish against a material advantage
    b = chess.Board(None)
    b.clear()
    b.set_piece_at(chess.square(rng.randrange(8), rng.randrange(8)), chess.Piece(chess.KING, chess.WHITE))
    ksq_black = chess.square(rng.randrange(8), rng.randrange(8))
    if ksq_black == b.king(chess.WHITE):
        continue
    b.set_piece_at(ksq_black, chess.Piece(chess.KING, chess.BLACK))
    # add a queen + rook + a couple of pieces for white, sometimes a defender for black
    for _ in range(rng.randint(2, 3)):
        for _try in range(20):
            sq = chess.square(rng.randrange(8), rng.randrange(8))
            if b.piece_at(sq) is None and sq != b.king(chess.WHITE):
                b.set_piece_at(sq, chess.Piece(rng.choice([chess.QUEEN, chess.ROOK, chess.BISHOP]), chess.WHITE))
                break
    if rng.random() < 0.5:
        for _try in range(20):
            sq = chess.square(rng.randrange(8), rng.randrange(8))
            if b.piece_at(sq) is None:
                b.set_piece_at(sq, chess.Piece(rng.choice([chess.PAWN, chess.KNIGHT]), chess.BLACK))
                break
    b.turn = chess.WHITE
    if not b.is_valid():
        continue
    if b.is_checkmate() or b.is_stalemate():
        continue
    if not any(b.legal_moves):
        continue
    fen = b.fen()
    kind, n = score_of(EXE, fen)
    if kind == "mate":
        found.append(fen)
        print(f"{len(found)}: mate {n}  {fen}", flush=True)

open(OUT, "w").write("\n".join(found) + "\n")
print(f"\nwrote {len(found)} mate positions to {OUT} after {tried} candidates")
if not found:
    raise SystemExit("ABORT: no mate positions found -- set would be empty")
