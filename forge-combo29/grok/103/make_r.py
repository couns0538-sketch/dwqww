#!/usr/bin/env python3
"""Random legal games with python-chess. SEED = seat * 100 + 1.

A game that ends before ply 80 is dropped entirely. From a game that is still
going at ply 79, one FEN is kept every 7 plies after ply 8 (plies 15, 22, ...).
The terminal position is never written, because an ended game is dropped.
"""
import random
import sys
from pathlib import Path

import chess


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: make_r.py SEED COUNT OUT", file=sys.stderr)
        return 2
    seed = int(sys.argv[1])
    count = int(sys.argv[2])
    out = Path(sys.argv[3])
    rng = random.Random(seed)
    kept = []
    started = 0
    dropped = 0
    while len(kept) < count:
        started += 1
        board = chess.Board()
        samples = []
        ended = False
        for ply in range(1, 80):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            move = rng.choice(list(board.legal_moves))
            board.push(move)
            if ply > 8 and (ply - 8) % 7 == 0 and not board.is_game_over(claim_draw=True):
                samples.append(board.fen())
        if ended or len(samples) == 0:
            dropped += 1
            continue
        kept.extend(samples)
        if started > 200000:
            raise SystemExit(f"too many games, kept {len(kept)}")
    kept = kept[:count]
    out.write_text("\n".join(kept) + "\n")
    print(f"seed={seed} started={started} dropped={dropped} kept={len(kept)} file={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
