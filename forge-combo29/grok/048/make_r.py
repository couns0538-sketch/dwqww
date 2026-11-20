#!/usr/bin/env python3
"""300 positions for set R.

SEED = seat * 100 + 1. python-chess plays random legal games. A game that
reaches a terminal position (including a claimable 50-move or threefold draw)
is dropped. From a game that is still going at ply 60, keep the FENs at
ply 8, 15, 22, ... (every 7 plies from ply 8).
"""
import random
from pathlib import Path

import chess

SEAT = int(Path("/home/ubuntu/grok_seat.txt").read_text().strip())
SEED = SEAT * 100 + 1
WANT = 300
rng = random.Random(SEED)
kept = []
used = 0
dropped = 0
while len(kept) < WANT:
    board = chess.Board()
    ply = 0
    taken = []
    ended = False
    while ply < 60:
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        move = rng.choice(list(board.legal_moves))
        board.push(move)
        ply += 1
        if ply >= 8 and (ply - 8) % 7 == 0:
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            taken.append(board.fen())
    if ended or board.is_game_over(claim_draw=True):
        dropped += 1
        continue
    used += 1
    kept.extend(taken)

kept = kept[:WANT]
out = Path(__file__).resolve().parent / "R300.fens"
out.write_text("\n".join(kept) + "\n")
meta = out.with_suffix(".meta.txt")
meta.write_text(
    f"seed={SEED}\nseat={SEAT}\ngames_kept={used}\ngames_dropped={dropped}\n"
    f"positions={len(kept)}\nrule=ply 8 then every 7 plies, stop at ply 60, "
    f"drop a game that ends including claimable draws\n"
)
print(meta.read_text())
