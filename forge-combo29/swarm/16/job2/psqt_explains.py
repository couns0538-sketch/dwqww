#!/usr/bin/env python3
"""psqt_explains.py EXE FENS OUT.txt : does the PSQT table explain the left-right hce delta?

For each FEN, under UseNNUE false (so hce only):
  measured = hce(fen) - hce(flip_horizontal(fen))
  predicted = psqt_sum(fen) - psqt_sum(flip(fen))   read from src/eval_params_table.inc
Then prints the correlation and how many positions the PSQT prediction gets the SIGN right for.
If PSQT dominates, correlation is high; a low correlation means other terms (pawn structure, shelter,
mobility) carry the asymmetry, and I must name them from the code instead of guessing.
"""
import re
import statistics
import sys

import chess
import mirror_lr as M

EXE, FENS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
TABLE = "/agent/repos/base/forge-combo29/src/eval_params_table.inc"
ROWS = {}
for line in open(TABLE):
    m = re.match(r"/\* (\d+) (\w+)\[(\d+)\] \*/ S\((-?\d+), (-?\d+)\)", line.strip())
    if m:
        ROWS[(m.group(2), int(m.group(3)))] = (int(m.group(4)), int(m.group(5)))
KEY = {chess.PAWN: "PawnPsqt", chess.KNIGHT: "KnightPsqt", chess.BISHOP: "BishopPsqt",
       chess.ROOK: "RookPsqt", chess.QUEEN: "QueenPsqt", chess.KING: "KingPsqt"}


def psqt_sum(board):
    total = 0
    for sq, piece in board.piece_map().items():
        rel = sq if piece.color == chess.WHITE else sq ^ 56
        v = ROWS[(KEY[piece.piece_type], rel)][0]
        total += v if piece.color == chess.WHITE else -v
    return total


class Eng(M.Engine):
    def __init__(self, exe):
        super().__init__(exe)
        self.send("setoption name UseNNUE value false")
        self.send("isready")
        self.check(self.read_until())


fens = [l.strip() for l in open(FENS) if l.strip()]
eng = Eng(EXE)
pairs = []
for fen in fens:
    b = chess.Board(fen)
    lr = b.transform(chess.flip_horizontal)
    a = M.parse(eng.ev(fen))["hce"]
    c = M.parse(eng.ev(lr.fen()))["hce"]
    pairs.append((a - c, psqt_sum(b) - psqt_sum(lr)))
eng.quit()

n = len(pairs)
mx = statistics.mean(p[0] for p in pairs)
my = statistics.mean(p[1] for p in pairs)
sxy = sum((x - mx) * (y - my) for x, y in pairs)
sxx = sum((x - mx) ** 2 for x, _ in pairs)
syy = sum((y - my) ** 2 for _, y in pairs)
r = sxy / (sxx * syy) ** 0.5 if sxx and syy else 0.0
sign_ok = sum(1 for x, y in pairs if (x > 0) == (y > 0) and x != 0 and y != 0)
nonzero = sum(1 for x, y in pairs if x != 0 and y != 0)
exact = sum(1 for x, y in pairs if x == y)

lines = [
    f"positions {n}",
    f"measured hce delta vs PSQT-predicted delta: correlation r = {r:.4f}",
    f"sign agreement: {sign_ok} of {nonzero} ({100.0*sign_ok/nonzero:.1f} %)",
    f"exactly equal: {exact} of {n}",
    f"measured |delta| median {statistics.median(abs(p[0]) for p in pairs)}  "
    f"PSQT |delta| median {statistics.median(abs(p[1]) for p in pairs)}",
    "",
    "first 10 pairs (measured, psqt):",
]
lines += [f"  {x:6d}  {y:6d}" for x, y in pairs[:10]]
text = "\n".join(lines) + "\n"
print(text)
with open(OUT, "w") as fh:
    fh.write(text)
