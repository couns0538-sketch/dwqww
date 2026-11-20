#!/usr/bin/env python3
"""Random legal games with SEED 1101.

A game is played to ply 80. If it is over at any point, including on the ply-80
move, the whole game is dropped. From a game that is still going, one FEN is
kept at ply 8 and every 7 plies after that (8, 15, 22, ...).
"""
import random
import sys
from pathlib import Path

import chess

SEED = 1101
PLY_CAP = 80
FIRST_PLY = 8
STRIDE = 7
NEED = 300


def main():
    out = Path(sys.argv[1])
    rng = random.Random(SEED)
    fens = []
    kept = 0
    dropped = 0
    while len(fens) < NEED:
        board = chess.Board()
        while len(board.move_stack) < PLY_CAP and not board.is_game_over(claim_draw=True):
            board.push(rng.choice(list(board.legal_moves)))
        if board.is_game_over(claim_draw=True) or len(board.move_stack) < PLY_CAP:
            dropped += 1
            continue
        kept += 1
        sample = chess.Board()
        for ply, move in enumerate(board.move_stack, start=1):
            sample.push(move)
            if ply >= FIRST_PLY and (ply - FIRST_PLY) % STRIDE == 0:
                fens.append(sample.fen())
                if len(fens) >= NEED:
                    break
    out.write_text("\n".join(fens) + "\n")
    print(f"wrote {len(fens)} dropped_games {dropped} kept_games {kept} seed {SEED}")


if __name__ == "__main__":
    main()
