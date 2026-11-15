#!/usr/bin/env python3
"""Job 2 positions: 30 positions as the job asks.

20 "ordinary middlegame" positions: the job says "from the UHO opening file after
8 random plies".  There is no UHO file in this repository and none on this
machine (searched), so I say so and use a documented substitute: legal random
games from the start position, taking the position after 8 random plies (16
half-moves), keeping only positions that are not terminal and have >= 20 men.
Every position is written out with its seed so any case can be replayed.

5 bare endings: king and knight (or king and bishop) against king, both colours.
5 positions with fewer than 8 men: random legal piece sets totalling < 8 men,
both kings present, no side in check, not terminal.
"""

import json
import random
import sys

import chess

OUT = sys.argv[1] if len(sys.argv) > 1 else "positions30.json"
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 20261116

rng = random.Random(SEED)


def play_random(plies, seed):
    r = random.Random(seed)
    b = chess.Board()
    played = []
    for _ in range(plies):
        moves = list(b.legal_moves)
        if not moves:
            return None, played
        m = r.choice(moves)
        b.push(m)
        played.append(m.uci())
    return b, played


middlegame = []
tries = 0
while len(middlegame) < 20 and tries < 4000:
    tries += 1
    seed = 100000 + tries
    b, played = play_random(16, seed)
    if b is None or b.is_game_over() or b.is_check() or len(b.piece_map()) < 20:
        continue
    middlegame.append({"fen": b.fen(), "kind": "middlegame", "plies": 16, "seed": seed,
                       "moves": played})

bare = []
for colour in (chess.WHITE, chess.BLACK):
    for minor in (chess.KNIGHT, chess.BISHOP):
        for k in range(2):
            if len(bare) >= 5:
                break
            while True:
                sqs = rng.sample(range(64), 3)
                b = chess.Board(None)
                b.set_piece_at(sqs[0], chess.Piece(chess.KING, chess.WHITE))
                b.set_piece_at(sqs[1], chess.Piece(chess.KING, chess.BLACK))
                b.set_piece_at(sqs[2], chess.Piece(minor, colour))
                b.turn = colour
                b.halfmove_clock = 0
                b.fullmove_number = 40
                if not b.is_valid():
                    continue
                if b.is_check() or b.is_checkmate() or b.is_stalemate():
                    continue
                break
            bare.append({"fen": b.fen(), "kind": "bare", "moves": []})

small = []
while len(small) < 5:
    n_extra = rng.choice([2, 3, 4])          # total men 4..6 (< 8)
    kinds = [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.PAWN, chess.QUEEN]
    sqs = rng.sample(range(64), 2 + n_extra)
    b = chess.Board(None)
    b.set_piece_at(sqs[0], chess.Piece(chess.KING, chess.WHITE))
    b.set_piece_at(sqs[1], chess.Piece(chess.KING, chess.BLACK))
    for i in range(n_extra):
        colour = chess.WHITE if rng.random() < 0.5 else chess.BLACK
        kind = rng.choice(kinds)
        b.set_piece_at(sqs[2 + i], chess.Piece(kind, colour))
    b.turn = chess.WHITE if rng.random() < 0.5 else chess.BLACK
    b.halfmove_clock = 0
    b.fullmove_number = 40
    if not b.is_valid() or b.is_check() or b.is_checkmate() or b.is_stalemate():
        continue
    if len(b.piece_map()) >= 8:
        continue
    small.append({"fen": b.fen(), "kind": "small", "moves": []})

positions = middlegame + bare + small
json.dump({"seed": SEED, "note": "no UHO file available; middlegame = 8 random plies x2 from startpos",
           "positions": positions}, open(OUT, "w"), indent=1)
for p in positions:
    print(p["kind"], p["fen"])
print("total", len(positions))
