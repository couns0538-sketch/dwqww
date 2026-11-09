#!/usr/bin/env python3
"""gen_zugzwang_fixture.py - roots that lead into mutual zugzwang, the positions where a null move can prove something false. python-chess oracle.

Z: position with S to move, S has non-pawn material, S does not win (wdl <= 0 for S), while with the other side to move S wins (the other side's wdl is -2).
A root is a predecessor of Z: the other side to move, one quiet non-pawn move away from Z, so Z is an interior node.
usage: python -I -B gen_zugzwang_fixture.py <tables dir> <in.fens> <out.fens> [--max 4000] [--seed 5]
"""
import argparse
import os
import random
import sys

import chess
import chess.syzygy


def predecessors(rng, z):
    y = not z.turn  # side that moved last
    squares = [s for s in chess.SquareSet(z.occupied_co[y]) if z.piece_type_at(s) != chess.PAWN]
    rng.shuffle(squares)
    for s in squares:
        q = z.piece_at(s)
        temp = z.copy(stack=False)
        temp.remove_piece_at(s)
        froms = [f for f in chess.SQUARES if temp.piece_at(f) is None and f != s]
        rng.shuffle(froms)
        for f in froms:
            root = temp.copy(stack=False)
            root.set_piece_at(f, q)
            root.turn = y
            root.ep_square = None
            root.castling_rights = chess.BB_EMPTY
            root.halfmove_clock = 0
            root.fullmove_number = 1
            if not root.is_valid():
                continue
            if chess.Move(f, s) in root.legal_moves:
                yield root


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tables')
    ap.add_argument('infile')
    ap.add_argument('out')
    ap.add_argument('--max', type=int, default=4000)
    ap.add_argument('--seed', type=int, default=5)
    a = ap.parse_args()
    if os.path.exists(a.out):
        sys.exit(f'refusing: {a.out} exists')
    tb = chess.syzygy.open_tablebase(a.tables)
    rng = random.Random(a.seed)
    written = zugzwangs = scanned = 0
    with open(a.out, 'w', encoding='ascii', newline='\n') as f:
        for line in open(a.infile, encoding='ascii'):
            if written >= a.max:
                break
            scanned += 1
            b = chess.Board(line.strip())
            if not (b.occupied_co[b.turn] & ~(b.pawns | b.kings)) or b.is_check() or b.is_game_over():
                continue
            flipped = b.copy(stack=False)
            flipped.turn = not b.turn
            if not flipped.is_valid() or flipped.is_game_over():
                continue
            try:
                if tb.probe_wdl(b) > 0 or tb.probe_wdl(flipped) != -2:
                    continue
            except (chess.syzygy.MissingTableError, KeyError):
                continue
            zugzwangs += 1
            n = 0
            for root in predecessors(rng, b):
                f.write(root.fen() + '\n')
                written += 1
                n += 1
                if n >= 3:
                    break
    print(f'scanned {scanned}, mutual zugzwangs {zugzwangs}, roots written {written}')


if __name__ == '__main__':
    main()
