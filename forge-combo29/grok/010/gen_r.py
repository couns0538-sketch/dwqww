#!/usr/bin/env python3
"""Random legal games from python-chess. SEED = seat * 100 + 1.

A game that ends under chess.Board.is_game_over(claim_draw=True) before 64 plies
is dropped, including a game that ends on the move that reaches ply 64.
From a game still going at ply 64, keep the positions at plies 8, 15, 22, 29,
36, 43, 50 and 57. Write the first 300 of those positions, in generation order.
"""
import os
import random

import chess

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = 1001
MAX_PLY = 64
WANT = 300
SAMPLE_AT = set(range(8, MAX_PLY, 7))


def main():
    rng = random.Random(SEED)
    kept_games = 0
    dropped_games = 0
    positions = []
    while len(positions) < WANT:
        board = chess.Board()
        samples = []
        dropped = False
        for ply in range(1, MAX_PLY + 1):
            if board.is_game_over(claim_draw=True):
                dropped = True
                break
            chosen = rng.choice(list(board.legal_moves))
            board.push(chosen)
            if board.is_game_over(claim_draw=True):
                dropped = True
                break
            if ply in SAMPLE_AT:
                samples.append(board.fen())
        if dropped:
            dropped_games += 1
            continue
        kept_games += 1
        positions.extend(samples)
    positions = positions[:WANT]
    fen_path = os.path.join(HERE, "set_R.fen")
    meta_path = os.path.join(HERE, "set_R.meta")
    with open(fen_path, "w", encoding="utf-8") as handle:
        for fen in positions:
            handle.write(fen + "\n")
    with open(meta_path, "w", encoding="utf-8") as handle:
        handle.write("seed %d\n" % SEED)
        handle.write("max_ply %d\n" % MAX_PLY)
        handle.write("sample_plies %s\n" % " ".join(str(p) for p in sorted(SAMPLE_AT)))
        handle.write("kept_games %d\n" % kept_games)
        handle.write("dropped_games %d\n" % dropped_games)
        handle.write("positions %d\n" % len(positions))
        handle.write("end_rule chess.Board.is_game_over(claim_draw=True)\n")
    print("positions %d kept_games %d dropped_games %d" % (len(positions), kept_games, dropped_games))


if __name__ == "__main__":
    main()
