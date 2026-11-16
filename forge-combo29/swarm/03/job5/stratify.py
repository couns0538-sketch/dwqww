#!/usr/bin/env python3
"""stratify.py BMFILE FENFILE OUT : is the 4-of-200 move divergence concentrated in endgames?

The r15 patch contains FORGE_FIX_BARE_KING_LMR_CAP and FORGE_FIX_BARE_KING_ONE_THREAD, i.e. deliberate changes to
lone-king / low-material search. If the differing moves pile up in low-material positions, the divergence is
consistent with those intentional fixes rather than with a broken move generator. This script splits the 200
positions by total material and reports the divergence rate per bucket, with a Fisher exact test for
"divergence is independent of the endgame bucket" (two-sided, computed by hand — no SciPy here).
"""
import json
import math
import sys

import chess

bmfile, fenfile, out = sys.argv[1], sys.argv[2], sys.argv[3]
fens = [l.strip().split("\t")[-1] for l in open(fenfile) if l.strip()]
rows = {}
for line in open(bmfile):
    p = line.rstrip("\n").split("\t")
    if len(p) >= 4 and p[0].isdigit():
        rows[int(p[0])] = p

VAL = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}


def material_nonking(board):
    tot = 0
    for pt, v in VAL.items():
        tot += v * (len(board.pieces(pt, chess.WHITE)) + len(board.pieces(pt, chess.BLACK)))
    return tot


buckets = {"endgame <= 12 (non-king material)": [0, 0], "middlegame 13..24": [0, 0], "heavy 25+": [0, 0]}
for idx in sorted(rows):
    fen = fens[idx]
    b = chess.Board(fen)
    mat = material_nonking(b)
    key = ("endgame <= 12 (non-king material)" if mat <= 12
           else "middlegame 13..24" if mat <= 24 else "heavy 25+")
    buckets[key][0] += 1
    if rows[idx][3] == "DIFF":
        buckets[key][1] += 1

lines = ["| material bucket | positions | differing moves | rate |", "|---|---|---|---|"]
for k, (n, d) in buckets.items():
    lines.append(f"| {k} | {n} | {d} | {100.0*d/n if n else 0:.1f} % |")

# Fisher exact, endgame vs rest
e_n, e_d = buckets["endgame <= 12 (non-king material)"]
r_n = sum(v[0] for k, v in buckets.items() if k != "endgame <= 12 (non-king material)")
r_d = sum(v[1] for k, v in buckets.items() if k != "endgame <= 12 (non-king material)")


def hyper(a, b, c, d, n):
    return math.comb(a + b, a) * math.comb(c + d, c) / math.comb(n, a + c)


def fisher(a, b, c, d):
    n = a + b + c + d
    p0 = hyper(a, b, c, d, n)
    tot = 0.0
    for x in range(0, min(a + b, a + c) + 1):
        y = a + b - x
        z = a + c - x
        w = d - (a - x)
        if y < 0 or z < 0 or w < 0:
            continue
        p = hyper(x, y, z, w, n)
        if p <= p0 + 1e-12:
            tot += p
    return tot


p = fisher(e_d, e_n - e_d, r_d, r_n - r_d)
lines.append("")
lines.append(f"endgame {e_d}/{e_n} vs rest {r_d}/{r_n}; two-sided Fisher exact p = {p:.4f}")
lines.append("(p is descriptive: the bucket was chosen after seeing the data, so it is not a pre-registered test)")
open(out, "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
