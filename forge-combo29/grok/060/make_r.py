#!/usr/bin/env python3
"""Random legal games. Seed is seat * 100 + 1.

One position every 7 plies after ply 8 (plies 15, 22, 29, ...).
A game that reaches a terminal position is dropped and none of its
positions are kept. Games are cut at ply 80 while still ongoing.
"""
import random
import sys
import chess

SEED = 6001
TARGET = 300
CUT = 80


def main():
    out_path = sys.argv[1]
    rng = random.Random(SEED)
    kept = []
    started = 0
    dropped = 0
    while len(kept) < TARGET:
        started += 1
        board = chess.Board()
        taken = []
        ended = False
        ply = 0
        while ply < CUT:
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            move = rng.choice(list(board.legal_moves))
            board.push(move)
            ply += 1
            if ply > 8 and (ply - 8) % 7 == 0:
                taken.append(board.fen())
        if ended or not taken:
            dropped += 1
            continue
        kept.extend(taken)
    kept = kept[:TARGET]
    with open(out_path, "w", encoding="utf-8") as handle:
        for fen in kept:
            handle.write(fen + "\n")
    print("seed", SEED)
    print("kept", len(kept))
    print("games_started", started)
    print("games_dropped", dropped)


if __name__ == "__main__":
    main()
