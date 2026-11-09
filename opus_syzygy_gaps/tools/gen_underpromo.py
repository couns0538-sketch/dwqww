#!/usr/bin/env python3
"""gen_underpromo.py - roots whose only moves with the best class are underpromotions (queen promotion worse). python-chess oracle, seeded random search.

usage: python -I -B gen_underpromo.py <tables dir> <out.fens> [--want 300] [--tries 3000000] [--seed 31]
"""
import argparse
import glob
import os
import random
import sys

import chess
import chess.syzygy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_special_fixtures import promo_board  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tables')
    ap.add_argument('out')
    ap.add_argument('--want', type=int, default=300)
    ap.add_argument('--tries', type=int, default=3000000)
    ap.add_argument('--seed', type=int, default=31)
    a = ap.parse_args()
    if os.path.exists(a.out):
        sys.exit(f'refusing: {a.out} exists')
    tb = chess.syzygy.open_tablebase(a.tables)
    rng = random.Random(a.seed)
    mats = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(a.tables, '*.rtbw')))
    pawn = [m for m in mats if 'P' in m]
    found = 0
    tries = 0
    kinds = {}
    with open(a.out, 'w', encoding='ascii', newline='\n') as f:
        while found < a.want and tries < a.tries:
            tries += 1
            b = promo_board(rng, rng.choice(pawn))
            if b is None:
                continue
            vals = {}
            ok = True
            for m in list(b.legal_moves):
                b.push(m)
                try:
                    v = 2 if b.is_checkmate() else -tb.probe_wdl(b)
                except (chess.syzygy.MissingTableError, KeyError):
                    ok = False
                b.pop()
                if not ok:
                    break
                vals[m] = v
            if not ok or not vals:
                continue
            best = max(vals.values())
            top = [m for m, v in vals.items() if v == best]
            if all(m.promotion in (chess.ROOK, chess.BISHOP, chess.KNIGHT) for m in top):
                f.write(b.fen() + '\n')
                found += 1
                key = ''.join(sorted(chess.piece_symbol(m.promotion) for m in top))
                kinds[key] = kinds.get(key, 0) + 1
    print(f'found {found} in {tries} tries; only-best kinds {kinds}')


if __name__ == '__main__':
    main()
