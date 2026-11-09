#!/usr/bin/env python3
"""gen_warm_fixtures.py - inputs for warm_claims.py, from the 200k roots and their Fathom labels (python-chess venv).

clock file: roots with oracle wdl +-2 and |dtz| in [12, 60]: later clock c = 101 - |dtz| (so dtz + c = 101, not a certain result
at clock c), expected class 'other'. Also, as a control group, c = 99 - |dtz| (dtz + c = 99, expected class win / loss).
Roots stay at 5 pieces and the engine gets the 3-4 piece tables.

toggle file: six-piece roots whose capture leads to a cursed / blessed five-piece position: for each 5-piece position with oracle
wdl +-1 and side X to move, one piece q of the other side is moved back to a square it could have come from and an extra
piece of side X stands on q's square. Only legal positions with the capture legal are written. Engine: full 3-4-5 set.

usage: python -I -B gen_warm_fixtures.py <fens> <labels> <out prefix> [--max-clock 3000] [--max-toggle 400] [--seed 11]
"""
import argparse
import os
import random
import sys

import chess


def predecessors(rng, board):
    """Yield root boards from which a capture leads to `board` (same side to move as board after the capture)."""
    x = board.turn
    y = not x
    squares = [s for s in chess.SquareSet(board.occupied_co[y]) if board.piece_type_at(s) != chess.PAWN]
    rng.shuffle(squares)
    for s in squares:
        q = board.piece_at(s)
        # squares q could have come from: reverse attacks on an empty board position
        temp = board.copy(stack=False)
        temp.remove_piece_at(s)
        froms = []
        for f in chess.SQUARES:
            if temp.piece_at(f) is not None:
                continue
            t2 = temp.copy(stack=False)
            t2.set_piece_at(f, q)
            if t2.is_attacked_by(y, s) and s in t2.attacks(f):
                froms.append(f)
        rng.shuffle(froms)
        for f in froms[:6]:
            for extra in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN):
                root = temp.copy(stack=False)
                root.set_piece_at(f, q)
                root.set_piece_at(s, chess.Piece(extra, x))
                root.turn = y
                root.halfmove_clock = 0
                root.fullmove_number = 1
                root.ep_square = None
                root.castling_rights = chess.BB_EMPTY
                if not root.is_valid():
                    continue
                move = chess.Move(f, s)
                if move in root.legal_moves:
                    yield root


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('fens')
    ap.add_argument('labels')
    ap.add_argument('prefix')
    ap.add_argument('--max-clock', type=int, default=3000)
    ap.add_argument('--max-toggle', type=int, default=400)
    ap.add_argument('--seed', type=int, default=11)
    a = ap.parse_args()
    for ext in ('.clock.tsv', '.toggle.fens'):
        if os.path.exists(a.prefix + ext):
            sys.exit(f'refusing: {a.prefix + ext} exists')
    rng = random.Random(a.seed)
    clock_rows = []
    toggle_rows = []
    cursed = []
    for fen, lab in zip(open(a.fens, encoding='ascii'), open(a.labels, encoding='ascii')):
        fen = fen.strip()
        p = lab.split()
        if len(p) < 3 or p[2] != 'ok' or p[0] in ('NA', '99'):
            continue
        wdl, dtz = int(p[0]), int(p[1])
        d = abs(dtz)
        if abs(wdl) == 1:
            cursed.append(fen)
        elif abs(wdl) == 2 and 12 <= d <= 60:
            expect = 'win' if wdl > 0 else 'loss'
            clock_rows.append(f'{fen}\t{101 - d}\tother')
            clock_rows.append(f'{fen}\t{99 - d}\t{expect}')
    rng.shuffle(clock_rows)
    with open(a.prefix + '.clock.tsv', 'w', encoding='ascii', newline='\n') as f:
        for r in clock_rows[:a.max_clock]:
            f.write(r + '\n')
    rng.shuffle(cursed)
    for fen in cursed:
        board = chess.Board(fen)
        for root in predecessors(rng, board):
            toggle_rows.append(root.fen())
            break
        if len(toggle_rows) >= a.max_toggle:
            break
    with open(a.prefix + '.toggle.fens', 'w', encoding='ascii', newline='\n') as f:
        for r in toggle_rows:
            f.write(r + '\n')
    print(f'clock rows {min(len(clock_rows), a.max_clock)} of {len(clock_rows)}; toggle roots {len(toggle_rows)} from {len(cursed)} cursed')


if __name__ == '__main__':
    main()
