#!/usr/bin/env python3
"""Random legal games from python-chess. SEED = seat * 100 + 1.
One position every 7 plies starting at ply 8. A game that ends is dropped.
"""
import random
import sys
from pathlib import Path

import chess

SEED = 2501
TARGET = 300
# Plies 8, 15, ..., 71. A game must reach the last of these without ending.
TAKE_PLIES = list(range(8, 72, 7))
LAST_PLY = TAKE_PLIES[-1]


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("R.fens")
    rng = random.Random(SEED)
    kept_games = 0
    dropped = 0
    fens: list[str] = []
    while len(fens) < TARGET:
        board = chess.Board()
        taken: list[str] = []
        ended = False
        while board.ply() < LAST_PLY:
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            moves = list(board.legal_moves)
            if not moves:
                ended = True
                break
            board.push(rng.choice(moves))
            if board.ply() in TAKE_PLIES:
                taken.append(board.fen())
        if ended or board.is_game_over(claim_draw=True) or len(taken) != len(TAKE_PLIES):
            dropped += 1
            continue
        kept_games += 1
        fens.extend(taken)
    fens = fens[:TARGET]
    out.write_text("".join(fen + "\n" for fen in fens))
    note = out.with_suffix(".meta")
    note.write_text(
        f"seed {SEED}\n"
        f"target {TARGET}\n"
        f"kept_games {kept_games}\n"
        f"dropped_games {dropped}\n"
        f"positions {len(fens)}\n"
        f"take_plies {' '.join(str(p) for p in TAKE_PLIES)}\n"
        f"python-chess {chess.__version__}\n"
    )
    print(f"positions {len(fens)} kept_games {kept_games} dropped_games {dropped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
