#!/usr/bin/env python3
"""Find a position at halfmove 100 whose only mate-in-1 is delivered by a PAWN move.

Why this board: a pawn move resets the fifty-move counter, so after the pawn move the
position cannot be a fifty-move draw at all. If the engine still adjudicates the root as
drawn and plays a non-mating move, the >= 100 rule is wrong in the strongest possible case.

Brute force over small piece sets with python-chess: black king, white king, white pawn,
optionally one white rook/bishop/knight to confine the king; require that the ONLY mating
move is a pawn move.

usage: find_pawn_mate.py <outdir>
"""
import itertools
import json
import os
import sys

import chess


def only_pawn_mate(fen):
    """Return (board, mating_move) when exactly the mate-in-1 moves are pawn moves, else None."""
    try:
        board = chess.Board(fen)
    except ValueError:
        return None
    if not board.is_valid():
        return None
    mates = []
    for move in board.legal_moves:
        board.push(move)
        if board.is_checkmate():
            mates.append(move)
        board.pop()
    if not mates:
        return None
    if all(board.piece_at(m.from_square).piece_type == chess.PAWN for m in mates):
        return board, mates[0]
    return None


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    squares = range(64)
    found = []
    # black king in a corner-ish region, white king and a pawn, plus one minor/rook
    for bk, wk in itertools.product(squares, repeat=2):
        if bk == wk:
            continue
        if not (0 <= chess.square_file(bk) <= 3 and 4 <= chess.square_rank(bk) <= 7):
            continue  # black king in the a-d files, ranks 5-8: cheap pruning
        for wp in squares:
            if wp in (bk, wk):
                continue
            if chess.square_rank(wp) > 5:
                continue
            # one extra white piece, sometimes
            fens = []
            placement = {bk: "k", wk: "K", wp: "P"}
            fens.append(placement)
            found_here = False
            for extra_type, extra_letter in (("R", "R"), ("B", "B"), ("N", "N")):
                for sq in squares:
                    if sq in placement:
                        continue
                    p = dict(placement)
                    p[sq] = extra_letter
                    rows = []
                    for rank in range(7, -1, -1):
                        row = ""
                        empty = 0
                        for file in range(8):
                            sq2 = chess.square(file, rank)
                            if sq2 in p:
                                if empty:
                                    row += str(empty)
                                    empty = 0
                                row += p[sq2]
                            else:
                                empty += 1
                        if empty:
                            row += str(empty)
                        rows.append(row)
                    fens.append(p)
                    fen = "/".join(rows) + " w - - 100 1"
                    result = only_pawn_mate(fen)
                    if result is not None:
                        board, move = result
                        found.append({
                            "fen": board.fen(),
                            "mating_move": move.uci(),
                            "san": board.san(move),
                            "legal_moves": board.legal_moves.count(),
                        })
                        found_here = True
                        break
                if found_here:
                    break
            if found_here and len(found) >= 5:
                break
        if len(found) >= 5:
            break
    json.dump(found, open(os.path.join(outdir, "pawn_mates.json"), "w"), indent=1)
    for row in found:
        print(json.dumps(row))
    print("found", len(found))


if __name__ == "__main__":
    main()
