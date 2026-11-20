#!/usr/bin/env python3
"""Random legal games with SEED. Games that end before ply 80 are dropped.
One position is taken every 7 plies after ply 8 (plies 15, 22, ..., 78)."""
import pathlib
import random
import sys

import chess

SEED = 9001
PLY_CAP = 80
FIRST_PLY = 15
STEP = 7
NEED = 300


def main() -> int:
    need = int(sys.argv[1]) if len(sys.argv) > 1 else NEED
    rng = random.Random(SEED)
    kept: list[str] = []
    games_kept = 0
    games_dropped = 0
    while len(kept) < need:
        board = chess.Board()
        while board.ply() < PLY_CAP:
            if board.is_game_over(claim_draw=True):
                break
            board.push(rng.choice(list(board.legal_moves)))
        if board.ply() < PLY_CAP or board.is_game_over(claim_draw=True):
            games_dropped += 1
            continue
        games_kept += 1
        replay = chess.Board()
        stack = list(board.move_stack)
        for move in stack:
            replay.push(move)
            ply = replay.ply()
            if ply >= FIRST_PLY and (ply - FIRST_PLY) % STEP == 0 and ply < PLY_CAP:
                kept.append(replay.fen())
                if len(kept) >= need:
                    break
    folder = pathlib.Path(__file__).resolve().parent
    out = folder / "set_R.fen"
    out.write_text("\n".join(kept[:need]) + "\n")
    print(f"set_R.fen positions {need} games_kept {games_kept} games_dropped {games_dropped} seed {SEED}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
