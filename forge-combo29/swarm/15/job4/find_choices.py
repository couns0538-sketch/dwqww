#!/usr/bin/env python3
"""find_choices.py [N] : find positions where the losing side has two moves that lose in
DIFFERENT numbers of plies. That is the test the previous check could not make: if the engine's
mate distance is wrong, it may pick the shorter defence.

Searches sparse random endgames (python-chess), keeps positions where the side to move is losing
and at least two legal moves lose in different, small numbers of plies. Prints FEN plus the
per-move loss plies, so the engine's choice can be scored afterwards.
"""
import random
import sys

import chess

INF = 10 ** 6


def attacker_mates(board, plies):
    if board.is_checkmate():
        return 0
    if plies <= 0:
        return None
    if not any(board.legal_moves):
        return None
    best = None
    for mv in board.legal_moves:
        board.push(mv)
        if board.is_checkmate():
            board.pop()
            return 1
        sub = defender_holds(board, plies - 1)
        board.pop()
        if sub is not None and (best is None or sub + 1 < best):
            best = sub + 1
    return best


def defender_holds(board, plies):
    if plies <= 0:
        return None
    moves = list(board.legal_moves)
    if not moves:
        return None
    worst = 0
    for mv in moves:
        board.push(mv)
        if board.is_checkmate():
            board.pop()
            return None
        sub = attacker_mates(board, plies - 1)
        board.pop()
        if sub is None:
            return None
        worst = max(worst, sub + 1)
    return worst


def mate_in(board, maxp):
    for n in range(1, maxp + 1, 2):
        if attacker_mates(board, n) is not None:
            return n
    return None


def main():
    want = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    rng = random.Random(1501)
    found = []
    tries = 0
    while len(found) < want and tries < 300000:
        tries += 1
        b = chess.Board(None)
        sq = list(range(64))
        rng.shuffle(sq)
        wk, bk = sq.pop(), sq.pop()
        if chess.square_distance(wk, bk) == 0:
            continue
        b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        colour = rng.choice([chess.WHITE, chess.BLACK])
        for _ in range(rng.choice([2, 2, 3])):
            pt = rng.choice([chess.QUEEN, chess.ROOK, chess.ROOK])
            b.set_piece_at(sq.pop(), chess.Piece(pt, colour))
            if rng.random() < 0.5:
                colour = not colour
        b.turn = rng.choice([chess.WHITE, chess.BLACK])
        b.castling_rights = chess.BB_EMPTY
        if not b.is_valid():
            continue
        probe = b.copy()
        probe.turn = not b.turn
        if probe.is_check():
            continue
        if len(list(b.legal_moves)) < 2:
            continue
        # is the side to move lost? then every move must lose, at some distance
        losses = {}
        ok = True
        for mv in list(b.legal_moves):
            nb = b.copy()
            nb.push(mv)
            m = mate_in(nb, 9)
            if m is None:
                ok = False
                break
            losses[mv.uci()] = m
        if not ok or len(losses) < 2:
            continue
        if len(set(losses.values())) < 2:
            continue  # all equal: cannot distinguish
        found.append((b.fen(), dict(sorted(losses.items()))))
        print("%s   losses(plies after the move): %s" % (b.fen(), found[-1][1]), flush=True)
    print("\nfound %d positions with DIFFERING loss lengths in %d tries" % (len(found), tries))


if __name__ == "__main__":
    main()
