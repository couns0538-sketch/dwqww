#!/usr/bin/env python3
"""gen_fens.py - seeded random legal positions by material name. Stdlib only, own code (position rules as in the OSS
scout's t5_gen_fens.py: distinct squares, pawns off ranks 1/8, kings not adjacent, side not to move not in check, no
castling, clock 0 unless --clock is given).

usage: python -I -B gen_fens.py <tables dir> <out.fens> --n N --seed S [--min-pieces 5] [--max-pieces 5] [--clock C]
       [--pawns-only] [--ep]
--ep writes positions with a just-played double pawn push and an en passant square: the side to move has a pawn next to
the pushed pawn. Legality of the capture is checked later by the oracle (has_legal_en_passant).
"""
import argparse
import glob
import os
import random
import sys

KNIGHT = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]
ROOK = [(1, 0), (-1, 0), (0, 1), (0, -1)]
BISHOP = [(1, 1), (1, -1), (-1, 1), (-1, -1)]


def attacks(board, sq, piece, white, target):
    f, r = sq % 8, sq // 8
    tf, tr = target % 8, target // 8
    if piece == 'N':
        return (tf - f, tr - r) in KNIGHT
    if piece == 'K':
        return max(abs(tf - f), abs(tr - r)) == 1
    if piece == 'P':
        return tr - r == (1 if white else -1) and abs(tf - f) == 1
    dirs = (ROOK if piece in 'RQ' else []) + (BISHOP if piece in 'BQ' else [])
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


def in_check(board, white_king):
    ksq = next(s for s, (p, w) in board.items() if p == 'K' and w == white_king)
    return any(w != white_king and attacks(board, s, p, w, ksq) for s, (p, w) in board.items())


def fen_of(board, stm_white, ep='-', clock=0):
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
            row += v[0] if v[1] else v[0].lower()
        rows.append(row + (str(empty) if empty else ''))
    return '/'.join(rows) + (' w' if stm_white else ' b') + f' - {ep} {clock} 1'


def kings_ok(board):
    k = [s for s, (p, _) in board.items() if p == 'K']
    return len(k) == 2 and max(abs(k[0] % 8 - k[1] % 8), abs(k[0] // 8 - k[1] // 8)) > 1


def plain_position(rng, material, clock):
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
        if not ok or not kings_ok(board):
            continue
        stm = rng.random() < 0.5
        if in_check(board, not stm):
            continue
        return fen_of(board, stm, clock=clock)


def ep_position(rng, material):
    """Side to move has a pawn beside the opponent's just double-pushed pawn. None if the material cannot do it."""
    wpart, bpart = material.split('v')
    if 'P' not in wpart or 'P' not in bpart:
        return None
    for _ in range(2000):
        stm = rng.random() < 0.5
        file_pushed = rng.randrange(8)
        side = rng.choice([-1, 1])
        file_cap = file_pushed + side
        if not 0 <= file_cap < 8:
            continue
        rank = 3 if stm else 4  # black pawn just went to rank 5 (index 4) when black pushed; see below
        # white to move: black pushed from index 6 to index 4; white's capturing pawn on index 4; ep square index 5
        # black to move: white pushed from index 1 to index 3; black's capturing pawn on index 3; ep square index 2
        rank = 4 if stm else 3
        ep_rank = 5 if stm else 2
        start_rank = 6 if stm else 1
        pushed = rank * 8 + file_pushed
        capper = rank * 8 + file_cap
        board = {pushed: ('P', not stm), capper: ('P', stm)}
        rest_w = list(wpart)
        rest_b = list(bpart)
        rest_w.remove('P')
        rest_b.remove('P')
        forbidden = {pushed, capper, ep_rank * 8 + file_pushed, start_rank * 8 + file_pushed}
        ok = True
        for letters, white in ((rest_w, True), (rest_b, False)):
            for p in letters:
                for _try in range(50):
                    s = rng.randrange(64)
                    if s in board or s in forbidden or (p == 'P' and s // 8 in (0, 7)):
                        continue
                    board[s] = (p, white)
                    break
                else:
                    ok = False
        if not ok or not kings_ok(board) or in_check(board, not stm):
            continue
        ep = 'abcdefgh'[file_pushed] + str(ep_rank + 1)
        return fen_of(board, stm, ep=ep)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tables')
    ap.add_argument('out')
    ap.add_argument('--n', type=int, required=True)
    ap.add_argument('--seed', type=int, required=True)
    ap.add_argument('--min-pieces', type=int, default=3)
    ap.add_argument('--max-pieces', type=int, default=5)
    ap.add_argument('--clock', type=int, default=0)
    ap.add_argument('--pawns-only', action='store_true')
    ap.add_argument('--ep', action='store_true')
    ap.add_argument('--materials', default='', help='comma list, replaces the material filter')
    ap.add_argument('--clock-list', default='', help='comma list of clocks, one chosen per position')
    a = ap.parse_args()
    a.clocks = [int(x) for x in a.clock_list.split(',')] if a.clock_list else []
    if os.path.exists(a.out):
        sys.exit(f'refusing: {a.out} exists')
    mats = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(a.tables, '*.rtbw')))
    mats = [m for m in mats if a.min_pieces <= len(m.replace('v', '')) <= a.max_pieces]
    if a.pawns_only or a.ep:
        mats = [m for m in mats if 'P' in m]
    if a.ep:
        mats = [m for m in mats if all('P' in side for side in m.split('v'))]
    if a.materials:
        mats = a.materials.split(',')
    if not mats:
        sys.exit('no materials')
    rng = random.Random(a.seed)
    written = 0
    with open(a.out, 'w', encoding='ascii', newline='\n') as f:
        while written < a.n:
            m = rng.choice(mats)
            fen = ep_position(rng, m) if a.ep else plain_position(rng, m, rng.choice(a.clocks) if a.clocks else a.clock)
            if fen:
                f.write(fen + '\n')
                written += 1
    print(f'wrote {written} FENs from {len(mats)} materials (seed {a.seed}) to {a.out}')


if __name__ == '__main__':
    main()
