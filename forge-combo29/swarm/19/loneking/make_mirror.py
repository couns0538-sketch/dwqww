#!/usr/bin/env python3
"""make_mirror.py SEED OUT N : the MIRROR sample — positions where the side with ONLY A KING is to move.

19-F54 tested lone-king endings with the side that HAS material to move (the side which can throw a win away).
The mirror is the harder question for a searcher: the bare king must find the drawing resource, and any other
move simply loses. In a drawn-or-lost ending, choosing a move that hands the opponent a forced win is a
RESULT defect; with no tablebases the detectable case is "the engine's move lets the opponent mate at once
while an alternative does not", plus the terminal case "the engine's move is already stalemate/mate".
"""
import random
import sys

import chess

seed = int(sys.argv[1])
out = sys.argv[2]
want = int(sys.argv[3]) if len(sys.argv) > 3 else 40
rng = random.Random(seed)

SOURCES = ["/tmp/set_G.epd",
           "/agent/repos/dwqww/forge-combo29/swarm/19/job1b/R_1911.fens"]
HEAVY = (chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN)


def heavy(b, colour):
    return sum(len(b.pieces(pt, colour)) for pt in HEAVY)


starts = []
for path in SOURCES:
    try:
        for line in open(path):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            fen = line.split(";")[0].strip()
            try:
                b = chess.Board(fen)
            except ValueError:
                continue
            if b.is_valid():
                starts.append(fen)
    except OSError:
        pass

seen = set()
cand = []
for fen in starts:
    b = chess.Board(fen)
    for _ in range(200):
        if b.is_game_over():
            break
        wh, bh = heavy(b, chess.WHITE), heavy(b, chess.BLACK)
        if (wh == 0) != (bh == 0):
            stm_heavy = wh if b.turn == chess.WHITE else bh
            # MIRROR: the side to move is the BARE KING
            if stm_heavy == 0 and b.legal_moves.count() > 0:
                key = " ".join(b.fen().split()[:4])
                if key not in seen:
                    seen.add(key)
                    cand.append(b.fen())
        moves = list(b.legal_moves)
        if not moves:
            break
        b.push(rng.choice(moves))

n = min(want, len(cand))
picked = rng.sample(cand, n) if len(cand) > n else cand
with open(out, "w") as fh:
    fh.write("\n".join(picked) + "\n")
print("lone-king candidates with the BARE KING to move (deduped): %d ; sampled %d (seed %d)"
      % (len(cand), len(picked), seed))
