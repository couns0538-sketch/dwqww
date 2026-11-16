#!/usr/bin/env python3
"""find_perpetual.py [N] [--budget SECONDS]

Find a position where the side to move is materially LOST but has a forced DRAW by perpetual check,
so any engine that recognises repetition inside the search must score it ~0.

Verified by a bounded solver, not by eye: a position qualifies only when
  (1) the side to move is down at least a rook in material, and
  (2) the side to move has a move after which the OPPONENT cannot make progress without allowing a
      repetition, checked by a depth-limited search that counts a repeated position as a draw.
This is a heuristic filter, and it says so: a position it returns is a CANDIDATE. The engine result on
a candidate is reported separately and is not asserted to be "the perpetual".
"""
import random
import sys
import time

import chess

DRAW = 0
MATE = 10 ** 6


def material(board, colour):
    vals = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330, chess.ROOK: 500,
            chess.QUEEN: 900}
    s = 0
    for pt, v in vals.items():
        s += v * len(board.pieces(pt, colour))
    return s


def search(board, depth, alpha, beta, seen, ply):
    """negamax from the side to move's point of view; a repeated position scores 0."""
    key = (board.board_fen(), board.turn, board.castling_xfen(), board.ep_square)
    if key in seen:
        return DRAW
    if board.is_checkmate():
        return -MATE + ply
    if board.is_stalemate() or board.is_insufficient_material():
        return DRAW
    if depth <= 0:
        return 0
    best = -MATE - 1
    for mv in board.legal_moves:
        board.push(mv)
        seen.add(key)
        v = -search(board, depth - 1, -beta, -alpha, seen, ply + 1)
        seen.discard(key)
        board.pop()
        if v > best:
            best = v
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def main():
    want = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    budget = 120.0
    if "--budget" in sys.argv:
        budget = float(sys.argv[sys.argv.index("--budget") + 1])
    rng = random.Random(4242)
    t0 = time.monotonic()
    found = 0
    tried = 0
    while found < want and time.monotonic() - t0 < budget:
        tried += 1
        b = chess.Board(None)
        sq = rng.sample(range(64), 6)
        b.set_piece_at(sq[0], chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(sq[1], chess.Piece(chess.KING, chess.BLACK))
        b.set_piece_at(sq[2], chess.Piece(chess.QUEEN, chess.WHITE))
        b.set_piece_at(sq[3], chess.Piece(chess.QUEEN, chess.BLACK))
        b.set_piece_at(sq[4], chess.Piece(chess.ROOK, chess.BLACK))
        b.set_piece_at(sq[5], chess.Piece(chess.ROOK, chess.BLACK))
        b.turn = chess.WHITE
        b.castling_rights = chess.BB_EMPTY
        if not b.is_valid():
            continue
        probe = b.copy(); probe.turn = chess.BLACK
        if probe.is_check():
            continue
        if material(b, chess.WHITE) + 500 > material(b, chess.BLACK):
            continue  # white must be clearly lost
        v = search(b, 5, -MATE - 1, MATE + 1, set(), 0)
        if v == 0:
            # white to move, materially lost, scores exactly 0 -> candidate perpetual
            print("CANDIDATE %s   (material W=%d B=%d, bounded search = 0)"
                  % (b.fen(), material(b, chess.WHITE), material(b, chess.BLACK)), flush=True)
            found += 1
    print("\n%d candidates from %d tries in %.0fs" % (found, tried, time.monotonic() - t0))
    if not found:
        print("NO CANDIDATE FOUND in the budget — the in-search repetition question stays open "
              "for this method, and I do not draw a conclusion from its absence.")


if __name__ == "__main__":
    main()
