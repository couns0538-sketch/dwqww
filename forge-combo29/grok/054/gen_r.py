#!/usr/bin/env python3
"""Random legal games with python-chess. SEED, SEED+1, ... one seed per game.

A position is kept at ply 8 and every 7 plies after that. A game that ends
(mate, stalemate, or a claimable draw) before ply 80 is dropped whole.
"""

import random
import sys
from pathlib import Path

import chess

SEED = 5401
CAP_PLY = 80
WANT = 300


def main() -> int:
    out = Path(sys.argv[1])
    kept_fens: list[str] = []
    game = 0
    dropped = 0
    kept = 0
    while len(kept_fens) < WANT:
        rng = random.Random(SEED + game)
        board = chess.Board()
        samples: list[str] = []
        ended = False
        while board.ply() < CAP_PLY:
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            move = rng.choice(list(board.legal_moves))
            board.push(move)
            ply = board.ply()
            if ply >= 8 and (ply - 8) % 7 == 0 and not board.is_game_over(claim_draw=True):
                samples.append(board.fen())
        game += 1
        if ended or board.is_game_over(claim_draw=True) or board.ply() < CAP_PLY:
            dropped += 1
            continue
        kept += 1
        kept_fens.extend(samples)
    kept_fens = kept_fens[:WANT]
    out.write_text("".join(fen + "\n" for fen in kept_fens), encoding="utf-8")
    print(f"games_started {game}")
    print(f"games_dropped {dropped}")
    print(f"games_kept {kept}")
    print(f"positions {len(kept_fens)}")
    print(f"first_seed {SEED}")
    print(f"last_seed {SEED + game - 1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
