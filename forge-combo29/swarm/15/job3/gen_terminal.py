#!/usr/bin/env python3
"""gen_terminal.py OUTDIR [N]

Generates N checkmated and N stalemated root positions by SEARCHING random legal positions
with python-chess, so nothing is typed by hand and every position is verified by python-chess
before it is written. Deterministic from a fixed seed so the set is reproducible.
"""
import os
import random
import sys

import chess


def random_endgame(rng):
    """A random sparse position with kings, a queen and/or rooks, mostly quiet."""
    board = chess.Board(None)
    squares = list(range(64))
    rng.shuffle(squares)
    wk, bk = squares.pop(), squares.pop()
    if chess.square_distance(wk, bk) == 0:
        return None
    board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
    n_extra = rng.choice([1, 1, 1, 2, 2, 3])
    colour = rng.choice([chess.WHITE, chess.BLACK])
    for _ in range(n_extra):
        pt = rng.choice([chess.QUEEN, chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT])
        board.set_piece_at(squares.pop(), chess.Piece(pt, colour))
        if rng.random() < 0.35:
            colour = not colour
    board.turn = rng.choice([chess.WHITE, chess.BLACK])
    board.castling_rights = chess.BB_EMPTY
    return board


def main():
    outdir = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    os.makedirs(outdir, exist_ok=True)
    rng = random.Random(1501)
    mate, stale = [], []
    guard = 0
    while (len(mate) < n or len(stale) < n) and guard < 4000000:
        guard += 1
        b = random_endgame(rng)
        if b is None or not b.is_valid():
            continue
        # the side NOT to move must not be in check
        probe = b.copy()
        probe.turn = not b.turn
        if probe.is_check():
            continue
        if b.is_checkmate():
            if len(mate) < n and b.fen() not in mate:
                mate.append(b.fen())
        elif b.is_stalemate():
            if len(stale) < n and b.fen() not in stale:
                stale.append(b.fen())
    if len(mate) < n or len(stale) < n:
        raise SystemExit("only found %d mates, %d stalemates in %d tries" % (len(mate), len(stale), guard))
    for name, lst, pred in (("mate10.fens", mate, "is_checkmate"), ("stale10.fens", stale, "is_stalemate")):
        with open(os.path.join(outdir, name), "w", encoding="utf-8") as fh:
            for f in lst:
                b = chess.Board(f)
                assert b.is_valid() and getattr(b, pred)(), (f, pred)
                fh.write(f + "\n")
        print("%-14s %d positions, all verified %s" % (name, len(lst), pred))
    print("tries: %d" % guard)


if __name__ == "__main__":
    main()
