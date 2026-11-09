#!/usr/bin/env python3
"""gen_zz2_fixture.py - roots two plies before a mutual zugzwang Z (review R2, finding 1): one ply before Z the null move cannot run, two plies before it can.
S to move at Z, S does not win; with the other side to move S wins. Root: S to move, S plays a quiet move, the other side plays a quiet move into Z.
Parents are not filtered beyond legality; the review's roots are always included.

usage: python -I -B gen_zz2_fixture.py <zz_found.tsv> <out.fens> [--per-zugzwang 60] [--seed 7]
"""
import argparse
import os
import random
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_zugzwang_fixture import predecessors  # noqa: E402

REVIEW_ROOTS = [
    '8/8/8/8/4N3/7N/5K2/4n2k w - - 0 1',
    '8/8/8/8/1n2N3/6K1/8/6Nk w - - 0 1',
    '8/8/3n4/N7/8/8/k1K5/3N4 w - - 0 1',
    '8/8/8/6N1/2N5/6K1/2n5/6k1 w - - 0 1',
    '8/8/8/6N1/8/6K1/n7/5Nk1 w - - 0 1',
    '8/8/8/8/1n2N3/6K1/3N4/7k w - - 0 1',
    '8/8/2n5/6N1/8/5K2/3N4/6k1 w - - 0 1',
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('found')
    ap.add_argument('out')
    ap.add_argument('--per-zugzwang', type=int, default=60)
    ap.add_argument('--seed', type=int, default=7)
    a = ap.parse_args()
    if os.path.exists(a.out):
        sys.exit(f'refusing: {a.out} exists')
    rng = random.Random(a.seed)
    seen = set(REVIEW_ROOTS)
    rows = list(REVIEW_ROOTS)
    for line in open(a.found, encoding='ascii'):
        z = chess.Board(line.split('\t')[0])
        n = 0
        for p1 in predecessors(rng, z):
            for p2 in predecessors(rng, p1):
                fen = p2.fen()
                if fen not in seen:
                    seen.add(fen)
                    rows.append(fen)
                    n += 1
                if n >= a.per_zugzwang:
                    break
            if n >= a.per_zugzwang:
                break
    with open(a.out, 'w', encoding='ascii', newline='\n') as f:
        f.write('\n'.join(rows) + '\n')
    print(f'roots {len(rows)}')


if __name__ == '__main__':
    main()
