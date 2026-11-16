#!/usr/bin/env python3
"""find_counter100.py [N]

Find positions where the ONLY mating move is a PAWN move or a CAPTURE, so the mating move resets the
halfmove clock and the mate is reachable even from counter 100.

A candidate qualifies only when, checked with python-chess:
  - the position is legal and not already over;
  - EXACTLY ONE legal move delivers checkmate;
  - that move is a pawn move OR a capture (either resets/interrupts the fifty-move count).

Prints FEN, the mating move, and why it qualifies. Deterministic from a fixed seed.
"""
import random
import sys

import chess


def only_mate(board):
    """-> list of (uci, is_pawn_move, is_capture) for moves that deliver immediate checkmate."""
    out = []
    for mv in board.legal_moves:
        pt = board.piece_type_at(mv.from_square)
        cap = board.is_capture(mv)
        board.push(mv)
        mated = board.is_checkmate()
        board.pop()
        if mated:
            out.append((mv.uci(), pt == chess.PAWN, cap))
    return out


def main():
    want = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    rng = random.Random(1501)
    pawn_cases, cap_cases = [], []
    tries = 0
    while (len(pawn_cases) < want or len(cap_cases) < want) and tries < 3000000:
        tries += 1
        b = chess.Board(None)
        n = rng.choice([4, 5, 5, 6])
        sq = rng.sample(range(64), n)
        # a spread of material so pawn and capture mates both occur
        pool = [chess.KING, chess.KING, chess.PAWN, chess.QUEEN, chess.ROOK, chess.PAWN]
        colours = [chess.WHITE, chess.BLACK, chess.WHITE, chess.WHITE, chess.WHITE, chess.WHITE]
        for i in range(n):
            b.set_piece_at(sq[i], chess.Piece(pool[i], colours[i]))
        b.turn = chess.WHITE
        b.castling_rights = chess.BB_EMPTY
        if not b.is_valid():
            continue
        probe = b.copy(); probe.turn = chess.BLACK
        if probe.is_check():
            continue
        mates = only_mate(b)
        if len(mates) != 1:
            continue
        uci, is_pawn, is_cap = mates[0]
        if is_pawn and len(pawn_cases) < want:
            pawn_cases.append((b.fen(), uci, is_pawn, is_cap))
        elif is_cap and not is_pawn and len(cap_cases) < want:
            cap_cases.append((b.fen(), uci, is_pawn, is_cap))
    print("PAWN-MOVE MATES (only mate is a pawn move):")
    for f, u, p, c in pawn_cases:
        print("  %-46s  mate move %-6s pawn=%s capture=%s" % (f, u, p, c))
    print()
    print("CAPTURE MATES (only mate is a non-pawn capture):")
    for f, u, p, c in cap_cases:
        print("  %-46s  mate move %-6s pawn=%s capture=%s" % (f, u, p, c))
    print()
    print("%d pawn cases, %d capture cases from %d tries" % (len(pawn_cases), len(cap_cases), tries))
    if len(pawn_cases) < want or len(cap_cases) < want:
        print("INCOMPLETE — fewer cases found than asked; stated rather than padded.")


if __name__ == "__main__":
    main()
