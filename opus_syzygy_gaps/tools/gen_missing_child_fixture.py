#!/usr/bin/env python3
"""gen_missing_child_fixture.py - boundary roots whose walk meets a missing table (review of the walk's cap, test first).

usage: <venv python> -I -B gen_missing_child_fixture.py step1 <out.fens> [--n 20000] [--seed 51] [--material KQvKR]
       <venv python> -I -B gen_missing_child_fixture.py step2 <step1.fens> <tb_root.out> <out.fens>
step1: random legal positions of one material at clock 0. Run tb_root on them with the full 3-4 piece folder.
step2: for each root whose best table move has a rounded distance d < 100, the same position at clock 100 - d: that move then sits exactly on the
       hundredth half-move, so SyzygyRootExact bit 2 has to walk it. Run on a folder without the capture child (`out/tb/nochild`): the walk fails on the
       missing table in every round, cheaply, for as long as the budget lasts.
"""
import argparse
import random
import sys

import chess


def step1(a):
    rnd = random.Random(a.seed)
    white, black = a.material.split('v')
    out = set()
    while len(out) < a.n:
        b = chess.Board(None)
        b.turn = rnd.random() < 0.5
        squares = rnd.sample(range(64), len(white) + len(black))
        for ch, sq in zip(white, squares):
            b.set_piece_at(sq, chess.Piece.from_symbol(ch.upper()))
        for ch, sq in zip(black, squares[len(white):]):
            b.set_piece_at(sq, chess.Piece.from_symbol(ch.lower()))
        if not b.is_valid() or b.is_game_over():
            continue
        out.add(b.fen())
    with open(a.a, 'w', encoding='utf-8', newline='\n') as f:
        for fen in sorted(out):
            f.write(fen + '\n')
    print('roots', len(out))


def step2(a):
    fens = [l.strip() for l in open(a.a, encoding='utf-8') if l.strip()]
    rows = 0
    with open(a.c, 'w', encoding='utf-8', newline='\n') as f:
        for fen, line in zip(fens, open(a.b, encoding='utf-8')):
            p = line.rstrip('\n').split('\t')
            if p[1] != 'ok' or p[6] == '-':
                continue
            moves = [m.split(':') for m in p[6].split()]
            top = [m for m in moves if int(m[1]) == max(int(x[1]) for x in moves)]
            rounded = [m for m in top if m[3] == '1' and abs(int(m[2])) < 100]
            if not rounded:
                continue
            d = abs(int(rounded[0][2]))
            parts = fen.split()
            parts[4] = str(100 - d)
            parts[5] = str((100 - d) // 2 + 1)
            f.write(' '.join(parts) + '\n')
            rows += 1
    print('rows', rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('step', choices=['step1', 'step2'])
    ap.add_argument('a')
    ap.add_argument('b', nargs='?')
    ap.add_argument('c', nargs='?')
    ap.add_argument('--n', type=int, default=20000)
    ap.add_argument('--seed', type=int, default=51)
    ap.add_argument('--material', default='KQvKR')
    a = ap.parse_args()
    if a.step == 'step1':
        step1(a)
    else:
        step2(a)
    return 0


if __name__ == '__main__':
    sys.exit(main())
