#!/usr/bin/env python3
"""Random legal games with SEED. Keep a game only if it does not end by ply 120.
Take one FEN every 7 plies after ply 8. Write the first 300."""
import random
import sys
from pathlib import Path

import chess

SEED = 3001
PLY_CAP = 120
WANT = 300


def main() -> None:
    out = Path(sys.argv[1])
    rng = random.Random(SEED)
    kept: list[str] = []
    games = 0
    dropped = 0
    while len(kept) < WANT:
        games += 1
        board = chess.Board()
        taken: list[str] = []
        ended = False
        for ply in range(1, PLY_CAP + 1):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            moves = list(board.legal_moves)
            board.push(rng.choice(moves))
            if ply >= 8 and (ply - 8) % 7 == 0:
                taken.append(board.fen())
        if ended or board.is_game_over(claim_draw=True):
            dropped += 1
            continue
        kept.extend(taken)
    kept = kept[:WANT]
    out.write_text("\n".join(kept) + "\n")
    print(f"games_started={games} dropped={dropped} kept_positions={len(kept)} seed={SEED}")


if __name__ == "__main__":
    main()
