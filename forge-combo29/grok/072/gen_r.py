#!/usr/bin/env python3
"""Random legal games from SEED. Keep a game only when it does not end.

One position every 7 plies from ply 8 through ply 78. Games that reach a
terminal position (including claimable draws) are dropped.
"""
import random
from pathlib import Path

import chess

SEED = 7201
NEED = 300
MAX_PLY = 78
OUT = Path(__file__).resolve().parent / "R.fens"

def main() -> None:
    rng = random.Random(SEED)
    kept: list[str] = []
    games = 0
    dropped = 0
    while len(kept) < NEED:
        games += 1
        board = chess.Board()
        samples: list[str] = []
        ended = False
        for ply in range(1, MAX_PLY + 1):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            move = rng.choice(list(board.legal_moves))
            board.push(move)
            if ply >= 8 and (ply - 8) % 7 == 0:
                if board.is_game_over(claim_draw=True):
                    ended = True
                    break
                samples.append(board.fen())
        if ended or len(samples) == 0:
            dropped += 1
            continue
        for fen in samples:
            if len(kept) >= NEED:
                break
            kept.append(fen)
    OUT.write_text("\n".join(kept) + "\n")
    print(f"wrote {len(kept)} fens to {OUT}")
    print(f"games_started {games} games_dropped {dropped} seed {SEED}")

if __name__ == "__main__":
    main()
