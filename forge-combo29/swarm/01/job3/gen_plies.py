#!/usr/bin/env python3
"""swarm seat 01, job 3 generator: ONE continuous legal move list of >= 1000 plies from startpos.

The brief: "1,000 legal plies of a random game (no game end allowed by the driver: take back to the last
position that still had moves)".

Design, and why it terminates:
  * Every move is chosen at random among the legal moves whose result is NOT checkmate, NOT stalemate and
    not insufficient material. Repetition, the fifty-move counter and the seventy-five-move rule are
    CLAIMS, not legality blocks, so a shuffling game may legally continue through them — that is exactly
    how a list can reach 1,000 plies without ever ending.
  * If a position has no such move, the driver takes back one ply (the brief's "take back to the last
    position that still had moves") and forbids the move it just undid, so the same trap is never
    re-entered. A bound on total backtracks makes the loop provably finite.

Writes the ply list to <out>. Prints the ply count and the seed used.
Usage: gen_plies.py <out-file> [seed] [target]
"""
import random
import sys

import chess

SEED = 101
TARGET = 1000


def ends_game(board):
    return (board.is_checkmate() or board.is_stalemate()
            or board.is_insufficient_material())


def build(seed, target):
    rng = random.Random(seed)
    board = chess.Board()
    plies = []
    banned = {}          # ply index -> set of uci moves that failed there
    backtracks = 0
    while len(plies) < target:
        if backtracks > 200000:
            raise RuntimeError("backtrack limit")
        idx = len(plies)
        moves = list(board.legal_moves)
        rng.shuffle(moves)
        blocked = banned.setdefault(idx, set())
        chosen = None
        for m in moves:
            uci = m.uci()
            if uci in blocked:
                continue
            board.push(m)
            bad = ends_game(board)
            board.pop()
            if not bad:
                chosen = m
                break
        if chosen is not None:
            board.push(chosen)
            plies.append(chosen.uci())
            continue
        # dead end at this position: take back one ply and forbid what led here
        if not plies:
            raise RuntimeError("dead end at the start position")
        backtracks += 1
        last = plies.pop()
        banned.setdefault(len(plies), set()).add(last)
        board.pop()
    return plies


def main():
    out = sys.argv[1]
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else SEED
    target = int(sys.argv[3]) if len(sys.argv) > 3 else TARGET
    plies = build(seed, target)
    # prove the list is replayable and every intermediate position had a legal move
    b = chess.Board()
    for i, p in enumerate(plies):
        move = chess.Move.from_uci(p)
        assert move in b.legal_moves, "illegal at ply %d" % (i + 1)
        b.push(move)
        assert not ends_game(b), "game ended at ply %d" % (i + 1)
    with open(out, "w") as fh:
        fh.write(" ".join(plies) + "\n")
    print("plies %d seed %d target %d final_fen %s" % (len(plies), seed, target, b.fen()))


if __name__ == "__main__":
    main()
