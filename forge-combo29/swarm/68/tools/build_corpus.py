#!/usr/bin/env python3
"""Build a position corpus that produces mate scores.

Mates do not appear in quiet middlegame positions at match depths. They appear
in two places, and the corpus has to contain both or the screen has nothing to
grade:

  * sparse endgames, where a cp score can turn into a mate at greater depth
    (the measured effect is 18/73 sparse vs 0/73 full-material at the same
    depths);
  * already-decided positions a few plies before mate, reachable from real games.

The generator plays random legal games from random openings and keeps a position
when a quick material count says it is materially lopsided and sparse. That is a
filter for "likely to contain a forced mate", not a claim that it does. Whether
it does is what the verifier decides -- the filter only picks candidates.
"""
import json
import random
import sys

import chess

PIECE_VALUE = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
               chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}


def material(b):
    tot = {chess.WHITE: 0, chess.BLACK: 0}
    for sq, pc in b.piece_map().items():
        tot[pc.color] += PIECE_VALUE[pc.piece_type]
    return tot


def main():
    target = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    out_path = sys.argv[2] if len(sys.argv) > 2 else "corpus.fen"
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 6801
    rng = random.Random(seed)

    kept = []
    seen = set()
    attempts = 0
    max_attempts = target * 400
    while len(kept) < target and attempts < max_attempts:
        attempts += 1
        b = chess.Board()
        # random opening so the games differ
        for _ in range(rng.randint(4, 14)):
            if b.is_game_over():
                break
            b.push(rng.choice(list(b.legal_moves)))
        # then random play to the endgame
        plies = rng.randint(40, 130)
        for _ in range(plies):
            if b.is_game_over():
                break
            moves = list(b.legal_moves)
            if not moves:
                break
            # bias toward captures so material gets lopsided
            caps = [m for m in moves if b.is_capture(m)]
            b.push(rng.choice(caps if caps and rng.random() < 0.55 else moves))
        if b.is_game_over():
            continue
        if b.is_check():
            continue  # keep the corpus to non-check roots; a mate label there is a different case
        m = material(b)
        diff = abs(m[chess.WHITE] - m[chess.BLACK])
        pieces = len(b.piece_map())
        # lopsided and sparse: where mates live
        if diff >= 5 and pieces <= 12:
            fen = b.fen()
            if fen in seen:
                continue
            seen.add(fen)
            kept.append(fen)

    with open(out_path, "w") as f:
        for fen in kept:
            f.write(fen + "\n")
    print(f"attempts {attempts}, kept {len(kept)} of target {target}")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
