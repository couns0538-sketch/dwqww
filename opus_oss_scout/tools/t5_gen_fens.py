#!/usr/bin/env python3
"""t5_gen_fens.py - OSS scout trial T5: seeded random legal 3-5 piece positions for a tablebase prober comparison.

usage: python -I -B t5_gen_fens.py <tables dir> <out.fens> [--n 50000] [--seed 20261106] [--max-pieces 5]
Materials come from the *.rtbw names in <tables dir> (e.g. KRPvKR), uniformly at random. Each position: pieces on
distinct random squares, pawns off ranks 1 and 8, kings not adjacent, side to move random, the side NOT to move is not
in check (otherwise the position is illegal), no castling, no en passant, halfmove clock 0. Stdlib only (no GPL code).
"""
import glob
import os
import random
import sys

KNIGHT = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]
KING = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
ROOK_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
BISHOP_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]


def attacks(board, sq, piece, white, target):
    """True if `piece` (upper-case letter) of colour `white` standing on sq attacks square target."""
    f, r = sq % 8, sq // 8
    tf, tr = target % 8, target // 8
    if piece == 'N':
        return (tf - f, tr - r) in KNIGHT
    if piece == 'K':
        return max(abs(tf - f), abs(tr - r)) == 1
    if piece == 'P':
        dr = 1 if white else -1
        return tr - r == dr and abs(tf - f) == 1
    dirs = []
    if piece in 'RQ':
        dirs += ROOK_DIRS
    if piece in 'BQ':
        dirs += BISHOP_DIRS
    for df, dr in dirs:
        cf, cr = f + df, r + dr
        while 0 <= cf < 8 and 0 <= cr < 8:
            c = cr * 8 + cf
            if c == target:
                return True
            if board.get(c) is not None:
                break
            cf += df
            cr += dr
    return False


def in_check(board, white_king_side):
    """Is the king of colour white_king_side attacked?"""
    ksq = next(s for s, (p, w) in board.items() if p == 'K' and w == white_king_side)
    for s, (p, w) in board.items():
        if w != white_king_side and attacks(board, s, p, w, ksq):
            return True
    return False


def fen_of(board, white_to_move):
    rows = []
    for r in range(7, -1, -1):
        row, empty = '', 0
        for f in range(8):
            v = board.get(r * 8 + f)
            if v is None:
                empty += 1
                continue
            if empty:
                row += str(empty)
                empty = 0
            p, w = v
            row += p if w else p.lower()
        if empty:
            row += str(empty)
        rows.append(row)
    return '/'.join(rows) + (' w' if white_to_move else ' b') + ' - - 0 1'


def random_position(rng, material):
    wpart, bpart = material.split('v')
    while True:
        squares = rng.sample(range(64), len(wpart) + len(bpart))
        board, ok = {}, True
        for letters, white in ((wpart, True), (bpart, False)):
            for p in letters:
                s = squares.pop()
                if p == 'P' and s // 8 in (0, 7):
                    ok = False
                board[s] = (p, white)
        if not ok:
            continue
        kings = [s for s, (p, w) in board.items() if p == 'K']
        if len(kings) != 2 or max(abs(kings[0] % 8 - kings[1] % 8), abs(kings[0] // 8 - kings[1] // 8)) <= 1:
            continue
        stm_white = rng.random() < 0.5
        if in_check(board, not stm_white):  # the side not to move may not be in check
            continue
        return fen_of(board, stm_white)


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    tables, out = argv[0], argv[1]
    n, seed, maxp = 50000, 20261106, 5
    i = 2
    while i < len(argv):
        if argv[i] == '--n':
            n = int(argv[i + 1])
        elif argv[i] == '--seed':
            seed = int(argv[i + 1])
        elif argv[i] == '--max-pieces':
            maxp = int(argv[i + 1])
        i += 2
    mats = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(tables, '*.rtbw')))
    mats = [m for m in mats if 3 <= len(m.replace('v', '')) <= maxp]
    if not mats:
        sys.exit('no tables found')
    rng = random.Random(seed)
    with open(out, 'w', encoding='ascii', newline='\n') as f:
        for _ in range(n):
            f.write(random_position(rng, rng.choice(mats)) + '\n')
    print(f'wrote {n} FENs from {len(mats)} materials (seed {seed}) to {out}')


if __name__ == '__main__':
    main(sys.argv[1:])
