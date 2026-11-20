#!/usr/bin/env python3
"""Random legal games with seed 3401 (seat 034 * 100 + 1).

One position every 7 plies after ply 8 (plies 8, 15, 22, 29, 36).
A game that ends before ply 36 is dropped. python-chess is_game_over(claim_draw=True)
counts checkmate, stalemate, insufficient material, the 50-move rule, and threefold repetition.
"""
import random
import chess

SEED = 3401
WANT = 300
SAMPLES = (8, 15, 22, 29, 36)


def main() -> None:
    rng = random.Random(SEED)
    out = []
    started = 0
    dropped = 0
    while len(out) < WANT:
        board = chess.Board()
        taken = []
        ended = False
        started += 1
        for ply in range(1, 37):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            board.push(rng.choice(list(board.legal_moves)))
            if ply in SAMPLES:
                taken.append(board.fen())
        if ended or len(taken) != len(SAMPLES):
            dropped += 1
            continue
        out.extend(taken)
    out = out[:WANT]
    print(f"games_started {started}")
    print(f"dropped {dropped}")
    print(f"kept_positions {len(out)}")
    for fen in out:
        print(fen)


if __name__ == "__main__":
    main()
