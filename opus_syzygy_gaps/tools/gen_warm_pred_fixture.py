#!/usr/bin/env python3
"""gen_warm_pred_fixture.py - two-position warm rows: a root stored at clock 0 is read at an inner node of a later search (R3 finding 6).

usage: <venv python> -I -B gen_warm_pred_fixture.py <tables> <f1.clock.tsv> <out.tsv> [--per-root 3] [--max-clock 89] [--seed 61] [--plies 1]
Input rows: "<P at clock 0>\t<later clock c>\t<class at c>". Kept: P's side to move loses at clock 0 with a table loss, and class at c is not a loss. Output rows: "<P at clock 0>\t<Q>" with Q a position
one reversible move before P (plies 2: two moves before P) at clock c - plies, c <= --max-clock, so that the entry of P can be read at clock c, inside the search of Q. For tb_claims with TB_CLAIMS_WARM=2.
"""
import argparse
import random
import sys

import chess
import chess.syzygy


def predecessors(b, clock):
    # positions one reversible move before b, with the opponent of b's side to move to move
    mover = not b.turn
    for sq, piece in b.piece_map().items():
        if piece.color != mover or piece.piece_type == chess.PAWN:
            continue
        for frm in chess.SquareSet(chess.BaseBoard.attacks(b, sq)):
            if b.piece_at(frm) is not None:
                continue
            q = b.copy(stack=False)
            q.remove_piece_at(sq)
            q.set_piece_at(frm, piece)
            q.turn = mover
            q.ep_square = None
            q.halfmove_clock = clock
            q.fullmove_number = max(1, clock // 2 + 1)
            if not q.is_valid():
                continue
            m = chess.Move(frm, sq)
            if m in q.legal_moves:
                yield q


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tables')
    ap.add_argument('rows')
    ap.add_argument('out')
    ap.add_argument('--per-root', type=int, default=3)
    ap.add_argument('--max-clock', type=int, default=89)
    ap.add_argument('--seed', type=int, default=61)
    ap.add_argument('--plies', type=int, default=1)
    a = ap.parse_args()
    rnd = random.Random(a.seed)
    n_roots = n_rows = 0
    with chess.syzygy.open_tablebase(a.tables) as tb, open(a.out, 'w', encoding='utf-8', newline='\n') as f:
        for line in open(a.rows, encoding='utf-8'):
            fen, c, cls = line.rstrip('\n').split('\t')
            c = int(c)
            if cls != 'other' or c > a.max_clock:
                continue
            p = chess.Board(fen)
            if tb.probe_wdl(p) != -2:
                continue
            frontier = [p]
            for ply in range(a.plies):
                next_frontier = []
                for b in frontier:
                    next_frontier.extend(predecessors(b, c - ply - 1))
                frontier = next_frontier
            if not frontier:
                continue
            n_roots += 1
            rnd.shuffle(frontier)
            for q in frontier[:a.per_root]:
                f.write(fen + '\t' + q.fen() + '\n')
                n_rows += 1
    print('roots', n_roots, 'rows', n_rows)
    return 0


if __name__ == '__main__':
    sys.exit(main())
