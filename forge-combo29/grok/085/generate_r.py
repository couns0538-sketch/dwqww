#!/usr/bin/env python3
"""Random legal games with python-chess. SEED = seat * 100 + 1.

A game is played to MAX_PLY. If it ends before that (checkmate, stalemate,
insufficient material, or a claimable fifty-move or threefold draw), the whole
game is dropped. From a game that reaches MAX_PLY, one FEN is kept every 7
plies starting at ply 8.
"""
import random
import sys

import chess

SEED = 8501
MAX_PLY = 50
TARGET = 300


def main() -> int:
    out = sys.argv[1]
    rng = random.Random(SEED)
    kept: list[str] = []
    used = 0
    dropped = 0
    while len(kept) < TARGET:
        board = chess.Board()
        fens: list[str] = []
        ended = False
        for _ply in range(1, MAX_PLY + 1):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            moves = list(board.legal_moves)
            if not moves:
                ended = True
                break
            board.push(rng.choice(moves))
            fens.append(board.fen())
            if board.is_game_over(claim_draw=True):
                ended = True
                break
        if ended or len(fens) < MAX_PLY:
            dropped += 1
            continue
        used += 1
        ply = 8
        while ply <= MAX_PLY and len(kept) < TARGET:
            kept.append(fens[ply - 1])
            ply += 7
    with open(out, "w", encoding="utf-8") as handle:
        handle.write("\n".join(kept) + "\n")
    print(f"positions {len(kept)} games_used {used} games_dropped {dropped} seed {SEED}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
