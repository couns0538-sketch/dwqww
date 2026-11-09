#!/usr/bin/env python3
"""gen_special_fixtures.py - adversarial root fixtures, python-chess for legality only (expected values come from oracle_chess.py).

usage: python -I -B gen_special_fixtures.py <tables dir> <out prefix> [--seed 21] [--n 4000]
Writes:
  <prefix>.promo.fens   pawns one step from promotion, both colours, promotion or capture-promotion legal; clocks 0, 60, 98, 99
  <prefix>.ep.fens      a legal en passant capture on the board, clock 0 (a double push just happened)
  <prefix>.rep.fens     lines "<fen> moves ...": two reversible move pairs that return to the start (second occurrence),
                        then once more (third occurrence of the start, a draw at the root), or one pair less (a move can make the third)
  <prefix>.castle.fens  castling rights on the board, 3-5 pieces: the tablebase path must stay out
  <prefix>.clock100.fens  clocks 100, 101, 149, 150: the root is already drawn for the engine
"""
import argparse
import glob
import os
import random
import sys

import chess


def random_board(rng, material, stm=None):
    w, b = material.split('v')
    for _ in range(4000):
        board = chess.Board(None)
        squares = rng.sample(range(64), len(w) + len(b))
        ok = True
        for letters, colour in ((w, chess.WHITE), (b, chess.BLACK)):
            for letter in letters:
                s = squares.pop()
                if letter == 'P' and chess.square_rank(s) in (0, 7):
                    ok = False
                board.set_piece_at(s, chess.Piece.from_symbol(letter if colour else letter.lower()))
        if not ok:
            continue
        board.turn = rng.random() < 0.5 if stm is None else stm
        if board.is_valid():
            return board
    return None


def promo_board(rng, material):
    w, b = material.split('v')
    if 'P' not in w and 'P' not in b:
        return None
    for _ in range(4000):
        side = chess.WHITE if ('P' in w and (('P' not in b) or rng.random() < 0.5)) else chess.BLACK
        board = chess.Board(None)
        rank7 = 6 if side == chess.WHITE else 1
        pawn_sq = chess.square(rng.randrange(8), rank7)
        board.set_piece_at(pawn_sq, chess.Piece(chess.PAWN, side))
        wl = list(w)
        bl = list(b)
        (wl if side == chess.WHITE else bl).remove('P')
        ok = True
        for letters, colour in ((wl, chess.WHITE), (bl, chess.BLACK)):
            for letter in letters:
                for _try in range(40):
                    s = rng.randrange(64)
                    if board.piece_at(s) is None and not (letter == 'P' and chess.square_rank(s) in (0, 7)):
                        board.set_piece_at(s, chess.Piece.from_symbol(letter if colour else letter.lower()))
                        break
                else:
                    ok = False
        if not ok:
            continue
        board.turn = side
        if board.is_valid() and any(m.promotion for m in board.legal_moves):
            return board
    return None


def ep_board(rng, material):
    w, b = material.split('v')
    if 'P' not in w or 'P' not in b:
        return None
    for _ in range(4000):
        board = random_board(rng, material)
        if board is None:
            return None
        stm = board.turn
        rank = 4 if stm == chess.WHITE else 3
        file_pushed = rng.randrange(8)
        file_cap = file_pushed + rng.choice((-1, 1))
        if not 0 <= file_cap < 8:
            continue
        pushed = chess.square(file_pushed, rank)
        capper = chess.square(file_cap, rank)
        # move one pawn of each side onto the two squares
        mine = [s for s in chess.SQUARES if board.piece_at(s) == chess.Piece(chess.PAWN, stm)]
        theirs = [s for s in chess.SQUARES if board.piece_at(s) == chess.Piece(chess.PAWN, not stm)]
        board.remove_piece_at(mine[0])
        board.remove_piece_at(theirs[0])
        if board.piece_at(pushed) is not None or board.piece_at(capper) is not None:
            continue
        ep = chess.square(file_pushed, 5 if stm == chess.WHITE else 2)
        start = chess.square(file_pushed, 6 if stm == chess.WHITE else 1)
        if board.piece_at(ep) is not None or board.piece_at(start) is not None:
            continue
        board.set_piece_at(pushed, chess.Piece(chess.PAWN, not stm))
        board.set_piece_at(capper, chess.Piece(chess.PAWN, stm))
        board.ep_square = ep
        if board.is_valid() and board.has_legal_en_passant():
            return board
    return None


def rep_line(rng, material):
    for _ in range(400):
        board = random_board(rng, material)
        if board is None:
            return None
        start = board.copy()
        moves = []
        for _pair in range(2):
            a = [m for m in board.legal_moves if not board.is_zeroing(m)]
            if not a:
                break
            m1 = rng.choice(a)
            board.push(m1)
            b = [m for m in board.legal_moves if not board.is_zeroing(m)]
            if not b:
                board.pop()
                break
            m2 = rng.choice(b)
            board.push(m2)
            back1 = chess.Move(m1.to_square, m1.from_square)
            if back1 not in board.legal_moves:
                board.pop()
                board.pop()
                break
            board.push(back1)
            back2 = chess.Move(m2.to_square, m2.from_square)
            if back2 not in board.legal_moves:
                board.pop()
                board.pop()
                board.pop()
                break
            board.push(back2)
            moves += [m1, m2, back1, back2]
        if len(moves) == 8 and board.board_fen() == start.board_fen() and board.turn == start.turn:
            return start.fen(), [m.uci() for m in moves]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tables')
    ap.add_argument('prefix')
    ap.add_argument('--seed', type=int, default=21)
    ap.add_argument('--n', type=int, default=4000)
    a = ap.parse_args()
    for ext in ('promo', 'ep', 'rep', 'castle', 'clock100'):
        if os.path.exists(f'{a.prefix}.{ext}.fens'):
            sys.exit(f'refusing: {a.prefix}.{ext}.fens exists')
    rng = random.Random(a.seed)
    mats = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(a.tables, '*.rtbw')))
    pawn = [m for m in mats if 'P' in m]
    both = [m for m in mats if all('P' in s for s in m.split('v'))]
    nop = [m for m in mats if 'P' not in m and len(m.replace('v', '')) >= 3]
    with open(a.prefix + '.promo.fens', 'w', newline='\n') as f:
        written = 0
        while written < a.n:
            b = promo_board(rng, rng.choice(pawn))
            if b:
                b.halfmove_clock = rng.choice((0, 0, 60, 98, 99))
                b.fullmove_number = b.halfmove_clock // 2 + 1
                f.write(b.fen() + '\n')
                written += 1
    with open(a.prefix + '.ep.fens', 'w', newline='\n') as f:
        written = 0
        while written < a.n // 2:
            b = ep_board(rng, rng.choice(both))
            if b:
                f.write(b.fen(en_passant='legal') + '\n')
                written += 1
    with open(a.prefix + '.rep.fens', 'w', newline='\n') as f:
        written = 0
        while written < a.n // 2:
            r = rep_line(rng, rng.choice(mats))
            if r:
                fen, moves = r
                keep = rng.choice((8, 6, 4))  # 8: start repeated once more available; 6, 4: a move may complete a repetition
                f.write(f'{fen} moves {" ".join(moves[:keep])}\n')
                written += 1
    with open(a.prefix + '.castle.fens', 'w', newline='\n') as f:
        written = 0
        while written < a.n // 8:
            m = rng.choice([x for x in mats if 'R' in x.split('v')[0] and len(x.replace('v', '')) <= 5])
            b = random_board(rng, m)
            if b is None:
                continue
            rooks = [s for s in chess.SQUARES if b.piece_at(s) == chess.Piece(chess.ROOK, chess.WHITE)]
            king = next(s for s in chess.SQUARES if b.piece_at(s) == chess.Piece(chess.KING, chess.WHITE))
            if b.piece_at(chess.E1) is not None or b.piece_at(chess.H1) is not None:
                continue
            b.remove_piece_at(king)
            b.remove_piece_at(rooks[0])
            b.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
            b.set_piece_at(chess.H1, chess.Piece(chess.ROOK, chess.WHITE))
            b.castling_rights = chess.BB_H1
            if b.is_valid():
                f.write(b.fen() + '\n')
                written += 1
    with open(a.prefix + '.clock100.fens', 'w', newline='\n') as f:
        written = 0
        while written < a.n // 8:
            b = random_board(rng, rng.choice(nop + pawn))
            if b is None or b.is_checkmate() or b.is_stalemate():
                continue
            b.halfmove_clock = rng.choice((100, 101, 149, 150))
            b.fullmove_number = b.halfmove_clock // 2 + 1
            f.write(b.fen() + '\n')
            written += 1
    print('fixtures written with seed', a.seed)


if __name__ == '__main__':
    main()
