#!/usr/bin/env python3
"""psqt_isolation.py EXE OUT.txt : is the left-right asymmetry explained by the PSQT tables alone?

Method: compare two positions that are left-right mirrors of each other and have NO pieces other than kings
and pawns, then repeat with one knight, one bishop, one rook, one queen. For a PSQT-only evaluation the
difference must equal the PSQT difference of the mirrored piece squares, which this script reads straight
out of the engine's own params table (src/eval_params_table.inc). If the sign and magnitude of the measured
delta matches the table's prediction, the term is named and proven.
"""
import re
import subprocess
import sys

import chess
import mirror_lr as M

EXE, OUT = sys.argv[1], sys.argv[2]
TABLE = "/agent/repos/base/forge-combo29/src/eval_params_table.inc"

TABLE_ROWS = {}
for line in open(TABLE):
    m = re.match(r"/\* (\d+) (\w+)\[(\d+)\] \*/ S\((-?\d+), (-?\d+)\)", line.strip())
    if m:
        TABLE_ROWS[(m.group(2), int(m.group(3)))] = (int(m.group(4)), int(m.group(5)))

PIECE_KEY = {chess.PAWN: "PawnPsqt", chess.KNIGHT: "KnightPsqt", chess.BISHOP: "BishopPsqt",
             chess.ROOK: "RookPsqt", chess.QUEEN: "QueenPsqt", chess.KING: "KingPsqt"}


def psqt_mg(piece_type, square, colour):
    """White contributes +table[sq]; black contributes -table[sq ^ 56] (eval.cpp:434-435 is the NNUE
    accumulator; the hand-crafted term uses the same relative-square convention, see eval.cpp:622-623)."""
    rel = square if colour == chess.WHITE else square ^ 56
    val = TABLE_ROWS[(PIECE_KEY[piece_type], rel)][0]
    return val if colour == chess.WHITE else -val


CASES = [
    ("kings only", "4k3/8/8/8/8/8/8/4K3 w - - 0 1"),
    ("kings+K d1", "4k3/8/8/8/8/8/8/3NK3 w - - 0 1"),
    ("kings+N b1", "4k3/8/8/8/8/8/8/1N2K3 w - - 0 1"),
    ("kings+B c1", "4k3/8/8/8/8/8/8/2B1K3 w - - 0 1"),
    ("kings+R a1", "4k3/8/8/8/8/8/8/R3K3 w - - 0 1"),
    ("kings+Q d1", "4k3/8/8/8/8/8/8/3QK3 w - - 0 1"),
]

eng = M.Engine(EXE)
lines = []
for label, fen in CASES:
    b = chess.Board(fen)
    lr = b.transform(chess.flip_horizontal)
    a1, a2 = M.parse(eng.ev(fen)), M.parse(eng.ev(lr.fen()))
    diffs = [k for k in ("hce", "nnue", "total") if a1[k] != a2[k]]
    # PSQT prediction for hce, summed over every piece on the board
    pred = 0
    for sq, piece in b.piece_map().items():
        pred += psqt_mg(piece.piece_type, sq, piece.color)
    pred_lr = 0
    for sq, piece in lr.piece_map().items():
        pred_lr += psqt_mg(piece.piece_type, sq, piece.color)
    lines.append(
        f"{label:14s} {fen}\n"
        f"   hce {a1['hce']:5d} vs lr {a2['hce']:5d}  delta {a1['hce']-a2['hce']:5d}"
        f"   psqt-sum {pred:5d} vs {pred_lr:5d}  psqt-delta {pred-pred_lr:5d}"
        f"   diffs {diffs or 'none'}")
eng.quit()
text = "\n".join(lines) + "\n"
print(text)
with open(OUT, "w") as fh:
    fh.write(text)
