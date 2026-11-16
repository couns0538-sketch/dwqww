#!/usr/bin/env python3
"""make_terminal_fens.py : generates 10 real checkmate roots and 10 real stalemate roots.

Every FEN is CONSTRUCTED to be terminal and then VERIFIED with python-chess before it is written; a
FEN that does not verify is dropped and reported, never silently used (my first hand-written list had
9 of 20 non-terminal FENs, which is exactly the mistake this script exists to prevent).
"""
import random
import sys

import chess


def build(rng, want_mate, tries=200000):
    for _ in range(tries):
        # random sparse position: 2 kings + 1-2 enemy pieces
        b = chess.Board(None)
        sqs = rng.sample(range(64), rng.choice([3, 4]))
        b.set_piece_at(sqs[0], chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(sqs[1], chess.Piece(chess.KING, chess.BLACK))
        if len(sqs) > 2:
            pt = rng.choice([chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN])
            colour = rng.choice([chess.WHITE, chess.BLACK])
            b.set_piece_at(sqs[2], chess.Piece(pt, colour))
        if len(sqs) > 3:
            pt = rng.choice([chess.QUEEN, chess.ROOK])
            colour = rng.choice([chess.WHITE, chess.BLACK])
            b.set_piece_at(sqs[3], chess.Piece(pt, colour))
        b.turn = rng.choice([chess.WHITE, chess.BLACK])
        b.clear_stack()
        if not b.is_valid():
            continue
        # a terminal root must have no legal move at all, and be check (mate) or not (stalemate)
        if b.is_checkmate() and want_mate:
            return b
        if b.is_stalemate() and not want_mate:
            return b
    return None


def main():
    rng = random.Random(2501)
    for want_mate, name in ((True, "mate_roots"), (False, "stale_roots")):
        out = []
        guard = 0
        while len(out) < 10 and guard < 200:
            guard += 1
            b = build(rng, want_mate)
            if b is None:
                continue
            fen = b.fen()
            # verify again from the string, exactly as the runner will send it
            v = chess.Board(fen)
            ok = v.is_checkmate() if want_mate else v.is_stalemate()
            if not ok or v.legal_moves.count() != 0:
                print(f"  DROPPED (did not verify): {fen}")
                continue
            if fen in out:
                continue
            out.append(fen)
        path = f"/agent/repos/dwqww/forge-combo29/swarm/25/job3/{name}.fens"
        with open(path, "w") as f:
            for fen in out:
                f.write(fen + "\n")
        print(f"{name}: wrote {len(out)} verified terminal FENs -> {path}")
        if len(out) < 10:
            print(f"  WARNING: only {len(out)} found")


if __name__ == "__main__":
    main()
