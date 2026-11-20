#!/usr/bin/env python3
"""Random legal games from python-chess. SEED = seat * 100 + 1.

After ply 8, keep a FEN every 7 plies. A game that has ended is not sampled.
"""
import random
import sys
from pathlib import Path

import chess

SEED = 86 * 100 + 1
NEED = 300


def main() -> int:
    out = Path(sys.argv[1])
    rng = random.Random(SEED)
    kept: list[str] = []
    games = 0
    while len(kept) < NEED:
        board = chess.Board()
        games += 1
        ply = 0
        while not board.is_game_over(claim_draw=True):
            if ply >= 8 and (ply - 8) % 7 == 0:
                kept.append(board.fen())
                if len(kept) >= NEED:
                    break
            board.push(rng.choice(list(board.legal_moves)))
            ply += 1
            if ply > 600:
                break
    out.write_text("\n".join(kept) + "\n")
    print(f"seed {SEED} games {games} positions {len(kept)} file {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
