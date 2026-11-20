#!/usr/bin/env python3
"""Random legal games for position set R.

Decision: seat 041, SEED = 41 * 100 + 1 = 4101. Attempt i (0-based) draws
moves with random.Random(SEED + i), so each attempt has its own seed.
A game is played one legal move at a time. If python-chess says the game is
over at any ply (checkmate, stalemate, insufficient material, the fifty-move
rule, or threefold repetition), the whole game is dropped and no FEN from it
is kept. A game that reaches ply 71 without ending contributes the positions
at plies 15, 22, 29, 36, 43, 50, 57, 64 and 71. Those plies are after ply 8
and spaced 7 plies apart. Stop at 300 FENs.
"""
import random
import sys

import chess

SEED = 41 * 100 + 1
TARGET = 300
LAST_PLY = 71
SAMPLE = [ply for ply in range(1, LAST_PLY + 1) if ply > 8 and (ply - 8) % 7 == 0]


def main() -> None:
    out_path = sys.argv[1]
    fens: list[str] = []
    attempt = 0
    kept_games = 0
    dropped = 0
    while len(fens) < TARGET:
        rng = random.Random(SEED + attempt)
        board = chess.Board()
        ended = False
        while board.ply() < LAST_PLY:
            if board.is_game_over():
                ended = True
                break
            move = rng.choice(list(board.legal_moves))
            board.push(move)
        if ended or board.is_game_over() or board.ply() < LAST_PLY:
            dropped += 1
        else:
            kept_games += 1
            for ply in SAMPLE:
                board_at = chess.Board()
                for item in list(board.move_stack)[:ply]:
                    board_at.push(item)
                fens.append(board_at.fen())
                if len(fens) >= TARGET:
                    break
        attempt += 1
        if attempt > 100000:
            raise SystemExit("too many attempts")
    with open(out_path, "w", encoding="utf-8") as handle:
        for fen in fens[:TARGET]:
            handle.write(fen + "\n")
    print(f"SEED {SEED}")
    print(f"SAMPLE {SAMPLE}")
    print(f"attempts {attempt} kept_games {kept_games} dropped {dropped}")
    print(f"fens {min(TARGET, len(fens))} -> {out_path}")


if __name__ == "__main__":
    main()
