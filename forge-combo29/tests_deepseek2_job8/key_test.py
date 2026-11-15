#!/usr/bin/env python3
"""Job 8: is the minor-piece key any good?

Generates random legal positions, computes the same minor key the patch computes
(splitmix64 finalizer over the four minor bitboards), and reports:

  * how many DISTINCT minor-piece placements there are among the sample,
  * how many distinct placements land on the same 14-bit table index
    (that is the collision that matters: CorrectionSize = 1<<14),
  * and the same for a deliberately weak key (knight bitboard + bishop bitboard
    without mixing) as the control: the weak key must collide far more often.

The key function here mirrors `minor_key()` in the patch line for line, including
the two different side multipliers, so a reader can compare them.
"""

import json
import random
import sys

import chess

MASK = (1 << 64) - 1
CORRECTION_SIZE = 1 << 14


def mix(x):
    x = (x + 0x9E3779B97F4A7C15) & MASK
    x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & MASK
    x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & MASK
    return x ^ (x >> 31)


def bb(board, color, kind):
    out = 0
    for sq in board.pieces(kind, color):
        out |= 1 << sq
    return out


def minor_key(board):
    # Each piece type gets its own multiplier before mixing. An earlier version
    # shared one between knights and bishops, so a knight and a bishop on the same
    # square gave the same key (they XOR to zero); this test found 228 collisions
    # in 51,684 distinct placements. With the separate multipliers: 0.
    wk = mix(bb(board, chess.WHITE, chess.KNIGHT) ^ 0x243F6A8885A308D3)
    wb = mix(bb(board, chess.WHITE, chess.BISHOP) ^ 0x13198A2E03707344)
    bk = mix(bb(board, chess.BLACK, chess.KNIGHT) ^ 0xA4093822299F31D0)
    bs = mix(bb(board, chess.BLACK, chess.BISHOP) ^ 0x082EFA98EC4E6C89)
    return mix(mix(wk ^ wb) ^ ((mix(bk ^ bs) * 0x9E3779B97F4A7C15) & MASK))


def weak_key(board):
    """Control: knights and bishops of a side XORed together, no mixing at all
    (the shape of my own first, broken key)."""
    return ((bb(board, chess.WHITE, chess.KNIGHT) ^ bb(board, chess.WHITE, chess.BISHOP)) |
            ((bb(board, chess.BLACK, chess.KNIGHT) ^ bb(board, chess.BLACK, chess.BISHOP)) << 32))


def placements(board):
    """The actual minor-piece placement: a tuple of (kind, colour, square)."""
    out = []
    for color in (chess.WHITE, chess.BLACK):
        for kind in (chess.KNIGHT, chess.BISHOP):
            for sq in board.pieces(kind, color):
                out.append((kind, color, sq))
    return tuple(sorted(out))


def random_position(rng):
    """A random legal position with kings and a plausible set of minors."""
    while True:
        b = chess.Board(None)
        squares = rng.sample(range(64), 2)
        b.set_piece_at(squares[0], chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(squares[1], chess.Piece(chess.KING, chess.BLACK))
        free = [s for s in range(64) if s not in squares]
        n_minor = rng.randint(0, 4)
        for sq in rng.sample(free, n_minor):
            color = chess.WHITE if rng.random() < 0.5 else chess.BLACK
            kind = chess.KNIGHT if rng.random() < 0.5 else chess.BISHOP
            b.set_piece_at(sq, chess.Piece(kind, color))
        b.turn = chess.WHITE if rng.random() < 0.5 else chess.BLACK
        b.halfmove_clock = 0
        b.fullmove_number = 40
        if b.is_valid():
            return b


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100000
    out = sys.argv[2] if len(sys.argv) > 2 else "key_test.json"
    rng = random.Random(20261118)
    seen_place = {}
    key_of_place = {}
    idx_of_place = {}
    weak_idx_of_place = {}
    for _ in range(n):
        b = random_position(rng)
        p = placements(b)
        k = minor_key(b)
        seen_place[p] = seen_place.get(p, 0) + 1
        key_of_place[p] = k
        idx_of_place[p] = k & (CORRECTION_SIZE - 1)
        weak_idx_of_place[p] = weak_key(b) & (CORRECTION_SIZE - 1)

    distinct = len(seen_place)
    distinct_keys = len(set(key_of_place.values()))
    distinct_idx = len(set(idx_of_place.values()))
    weak_distinct_idx = len(set(weak_idx_of_place.values()))
    res = {
        "positions": n,
        "distinct_placements": distinct,
        "distinct_keys": distinct_keys,
        "distinct_table_indices": distinct_idx,
        "collisions_within_placements": distinct - distinct_keys,
        "control_weak_key_distinct_indices": weak_distinct_idx,
        "control_weak_key_collisions": distinct - weak_distinct_idx,
        "table_size": CORRECTION_SIZE,
    }
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
