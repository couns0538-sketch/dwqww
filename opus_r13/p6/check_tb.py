#!/usr/bin/env python3
"""check_tb.py - R13 P6 (own code): Syzygy WDL / DTZ check of the ported prober against an independent prober.

usage: python -I -B check_tb.py gen <tables dir> <out_prefix> [--n 200] [--cursed 20] [--seed 13601]
       python -I -B check_tb.py compare <out_prefix> <tb_probe output>
gen: seeded random legal 5-man positions (material taken from the 5-man WDL tables present, pawns off the back ranks, no
castling / en passant, halfmove clock 0, side to move random, python-chess Board.is_valid), plus --cursed positions whose
WDL is +-1 (cursed win / blessed loss: the 50-move cases). Writes <prefix>.fens and <prefix>.oracle ("wdl dtz" per FEN) from
python-chess's own prober (chess.syzygy, GPL-3.0, used here as an independent test oracle only; nothing copied into Forge).
compare: WDL must match exactly on every FEN; DTZ must match exactly, or within 1 where the engine reports the stored DTZ as
rounded (DTZ tables store some values halved). Exit 1 on any mismatch or NA; prints the counts.
"""
import argparse
import glob
import os
import random
import sys

import chess
import chess.syzygy

PIECES = {'K': chess.KING, 'Q': chess.QUEEN, 'R': chess.ROOK, 'B': chess.BISHOP, 'N': chess.KNIGHT, 'P': chess.PAWN}


def random_position(rng, material):
    white, black = material.split('v')
    while True:
        board = chess.Board(None)
        squares = rng.sample(range(64), len(white) + len(black))
        ok = True
        for letters, colour in ((white, chess.WHITE), (black, chess.BLACK)):
            for letter in letters:
                sq = squares.pop()
                if letter == 'P' and chess.square_rank(sq) in (0, 7):
                    ok = False
                board.set_piece_at(sq, chess.Piece(PIECES[letter], colour))
        if not ok:
            continue
        board.turn = rng.choice([chess.WHITE, chess.BLACK])
        board.castling_rights = 0
        board.ep_square = None
        board.halfmove_clock = 0
        if board.is_valid():
            return board


def gen(a):
    rng = random.Random(a.seed)
    materials = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(a.tables, '*.rtbw')))
    five = [m for m in materials if len(m.replace('v', '')) == 5]
    if not five:
        raise SystemExit('no 5-man WDL tables found')
    out_fens, out_oracle = [], []
    with chess.syzygy.open_tablebase(a.tables) as tb:
        while len(out_fens) < a.n:
            board = random_position(rng, rng.choice(five))
            out_fens.append(board.fen())
            out_oracle.append(f'{tb.probe_wdl(board)} {tb.probe_dtz(board)}')
        cursed = 0
        tries = 0
        while cursed < a.cursed and tries < 200000:
            tries += 1
            board = random_position(rng, rng.choice(five))
            wdl = tb.probe_wdl(board)
            if abs(wdl) != 1:
                continue
            out_fens.append(board.fen())
            out_oracle.append(f'{wdl} {tb.probe_dtz(board)}')
            cursed += 1
    for ext, rows in (('.fens', out_fens), ('.oracle', out_oracle)):
        if os.path.exists(a.out + ext):
            raise SystemExit(f'refusing to overwrite {a.out + ext}')
        with open(a.out + ext, 'w', newline='\n') as fh:
            fh.write(''.join(r + '\n' for r in rows))
    print(f'{len(out_fens)} positions ({cursed} cursed / blessed after {tries} tries) from {len(five)} 5-man materials -> {a.out}')


def compare(a):
    oracle = [l.split() for l in open(a.out + '.oracle')]
    engine = [l.split() for l in open(a.engine)]
    if len(oracle) != len(engine):
        print(f'FAIL: {len(oracle)} oracle rows, {len(engine)} engine rows')
        sys.exit(1)
    wdl_ok = dtz_exact = dtz_rounded = 0
    bad = []
    for i, (o, e) in enumerate(zip(oracle, engine)):
        if e == ['NA']:
            bad.append((i, 'NA', o, e))
            continue
        ow, od, ew, ed, er = int(o[0]), int(o[1]), int(e[0]), int(e[1]), int(e[2])
        if ow != ew:
            bad.append((i, 'wdl', o, e))
            continue
        wdl_ok += 1
        if od == ed:
            dtz_exact += 1
        elif er and abs(od - ed) <= 1:
            dtz_rounded += 1
        else:
            bad.append((i, 'dtz', o, e))
    cursed = sum(1 for o in oracle if abs(int(o[0])) == 1)
    print(f'{len(oracle)} positions ({cursed} with WDL +-1): WDL {wdl_ok}/{len(oracle)} equal, DTZ {dtz_exact} exact + '
          f'{dtz_rounded} within 1 where the engine reports a rounded DTZ, {len(bad)} mismatches')
    for b in bad[:10]:
        print('  mismatch', b)
    sys.exit(1 if bad else 0)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    g = sub.add_parser('gen')
    g.add_argument('tables')
    g.add_argument('out')
    g.add_argument('--n', type=int, default=200)
    g.add_argument('--cursed', type=int, default=20)
    g.add_argument('--seed', type=int, default=13601)
    c = sub.add_parser('compare')
    c.add_argument('out')
    c.add_argument('engine')
    a = ap.parse_args()
    gen(a) if a.cmd == 'gen' else compare(a)


if __name__ == '__main__':
    main()
