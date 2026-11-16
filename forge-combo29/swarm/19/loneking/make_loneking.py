#!/usr/bin/env python3
"""make_loneking.py SEED OUT N : collect real lone-king endings by playing legal continuations from real
game positions, then sample N of them deterministically.

"Real" is stated precisely, because the word does work:
  - the STARTING positions are set G (353 positions taken from games) and, if present, my R_1911 set;
  - from each, one random legal game is played with python-chess until game over or 200 plies;
  - EVERY position along the way in which exactly one side has only its king is a candidate;
  - a candidate is kept only when the SIDE TO MOVE still has material (the interesting case: a side that can
    still win, or must not throw the win away).

So these are positions that arise in legal play from real game positions. They are NOT positions from human
games: a real game would have been resigned long before most of them. That distinction is stated in the report
and is the main limitation of the sample.

Deduplication is by the full FEN with counters zeroed, so the same board is not counted twice.
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
    n = 0
    for pt in HEAVY:
        n += len(b.pieces(pt, colour))
    return n


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
            # exactly one side is king-only
            stm_heavy = wh if b.turn == chess.WHITE else bh
            if stm_heavy > 0:      # the side to move still has material: the interesting case
                key = " ".join(b.fen().split()[:4])   # board + side + castling + ep, counters dropped
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
print("starts: %d ; lone-king candidates (deduped): %d ; sampled: %d (seed %d)"
      % (len(starts), len(cand), len(picked), seed))
print("written to", out)
