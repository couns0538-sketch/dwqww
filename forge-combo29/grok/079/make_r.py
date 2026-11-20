#!/usr/bin/env python3
"""Random legal games with SEED = seat * 100 + 1.

A position is kept every 7 plies after ply 8, and only while the game is
still going. The terminal position of a finished game is not kept. Games
that end before ply 8 add nothing.
"""

import random
from pathlib import Path

import chess

HERE = Path(__file__).resolve().parent
SEAT = int(Path.home().joinpath("grok_seat.txt").read_text().strip())
SEED = SEAT * 100 + 1
WANT = 400


def main() -> None:
    rng = random.Random(SEED)
    kept: list[str] = []
    games = 0
    dropped_short = 0
    while len(kept) < WANT:
        board = chess.Board()
        games += 1
        took = 0
        ply = 0
        while not board.is_game_over(claim_draw=True) and ply < 240 and len(kept) < WANT:
            board.push(rng.choice(list(board.legal_moves)))
            ply += 1
            if ply >= 8 and (ply - 8) % 7 == 0 and not board.is_game_over(claim_draw=True):
                kept.append(board.fen())
                took += 1
        if took == 0:
            dropped_short += 1
    out = HERE / "R.fens"
    out.write_text("\n".join(kept) + "\n", encoding="utf-8")
    print(f"seed {SEED} games {games} short_dropped {dropped_short} positions {len(kept)} file {out.name}")


if __name__ == "__main__":
    main()
