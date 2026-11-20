#!/usr/bin/env python3
"""Random legal games from python-chess.

Seat seed is 8001. Game i is Random(8001 + i). A game that ends before ply 64
is dropped. From a game that reaches ply 64, one FEN is kept every 7 plies
after ply 8 (plies 15, 22, 29, 36, 43, 50, 57).
"""
import pathlib
import random
import sys

import chess

SEED = 8001
TARGET = 300
MAX_PLY = 64
OUT = pathlib.Path(__file__).resolve().parent / "R.fens"


def main() -> None:
    positions: list[str] = []
    games = 0
    dropped = 0
    while len(positions) < TARGET:
        rng = random.Random(SEED + games)
        games += 1
        board = chess.Board()
        ended = False
        for _ply in range(MAX_PLY):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            board.push(rng.choice(list(board.legal_moves)))
        if ended or board.is_game_over(claim_draw=True):
            dropped += 1
            continue
        replay = chess.Board()
        for ply, move in enumerate(board.move_stack, start=1):
            replay.push(move)
            if ply >= 15 and (ply - 15) % 7 == 0:
                positions.append(replay.fen())
                if len(positions) >= TARGET:
                    break
    text = "\n".join(positions[:TARGET]) + "\n"
    OUT.write_text(text)
    print(f"wrote {TARGET} fens from {games} games, dropped {dropped}, file {OUT}")


if __name__ == "__main__":
    sys.exit(main())
