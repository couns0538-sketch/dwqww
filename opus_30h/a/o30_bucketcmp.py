#!/usr/bin/env python3
"""o30_bucketcmp.py <evals lock> <evals net> <fens.txt> [--names lock,net] - Opus 30-h job: does a bucketed net
carry SEAMS the lock net does not have? (own code; numpy + python-chess for the board facts)
The lock net has one output bucket and one king bucket, so its corrections have no steps where a capture changes the
piece-count bucket or a king move changes its rank group. A fine-tuned KB4 / OB8 net started with all buckets as copies;
after training, adjacent buckets can differ in their MEAN correction. Per output bucket (OB8 by piece count) and per side-
to-move king bucket (rank4), this prints rows, mean(net - lock), sd, and the step between adjacent buckets' means.
Per-position losses (S31) cannot see such steps; search sees them at every trade / king move across a bucket edge.
Inputs: one integer per line per FEN (v2_eval_*.exe output, side-to-move cp; ERR lines dropped), the FEN list."""
import argparse

import chess
import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('a')
    ap.add_argument('b')
    ap.add_argument('fens')
    ap.add_argument('--names', default='lock,net')
    a = ap.parse_args()
    na, nb = a.names.split(',')
    ra = [l.strip() for l in open(a.a)]
    rb = [l.strip() for l in open(a.b)]
    fens = [l.strip() for l in open(a.fens) if l.strip()]
    if not (len(ra) == len(rb) == len(fens)):
        raise SystemExit(f'line counts differ: {len(ra)} / {len(rb)} / {len(fens)}')
    ob, kb, d = [], [], []
    for x, y, f in zip(ra, rb, fens):
        if x == 'ERR' or y == 'ERR':
            continue
        board = chess.Board(f)
        pieces = chess.popcount(board.occupied)
        ob.append(min(7, max(pieces - 2, 0) * 8 // 32))
        ksq = board.king(board.turn)
        rel_rank = chess.square_rank(ksq) if board.turn == chess.WHITE else 7 - chess.square_rank(ksq)
        kb.append(0 if rel_rank == 0 else 1 if rel_rank == 1 else 2 if rel_rank <= 3 else 3)
        d.append(int(y) - int(x))
    ob, kb, d = np.array(ob), np.array(kb), np.array(d, np.float64)
    print(f'{nb} - {na}: positions {len(d)}, mean {d.mean():+.2f} cp, sd {d.std():.2f} cp')
    for title, g, labels in (('output bucket (OB8, pieces incl. kings)', ob, [f'{b}' for b in range(8)]),
                             ('side-to-move king (rank4)', kb, ['rank 1', 'rank 2', 'rank 3-4', 'rank 5-8'])):
        print(f'\n{title}: bucket, rows, mean diff (cp), sd, step to the previous bucket')
        prev = None
        for i, lab in enumerate(labels):
            m = g == i
            if m.sum() < 2:
                print(f'  {lab:8} {int(m.sum()):6}  -')
                continue
            mu = d[m].mean()
            step = '' if prev is None else f'{mu - prev:+.2f}'
            print(f'  {lab:8} {int(m.sum()):6}  {mu:+7.2f}  {d[m].std():6.2f}  {step}')
            prev = mu


if __name__ == '__main__':
    main()
