#!/usr/bin/env python3
"""planted_zero.py EXE FENS OUT.txt : Opus's Rule 1 control for job 3.

The claim "N of M mirror pairs give the same score" is a ZERO-shaped result. Rule 1: the same comparator
must count a planted case. Here the planted case is a pair that is NOT a mirror: position A is searched, and
position B is a DIFFERENT legal position (A's board with the side to move kept and one pawn moved two squares).
The comparator must report "different" for every planted pair. If it does, its "same"/"different" verdict for
real mirror pairs means something.
"""
import sys

import chess
import search_mirror as S

EXE, FENS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
fens = [l.strip() for l in open(FENS) if l.strip()][:12]
meta = ["planted-zero control for job3"]
lines = []
ok = 0
for i, fen in enumerate(fens):
    b = chess.Board(fen)
    # plant: a legal position that is NOT the mirror - shift the first white pawn one file right
    planted = None
    for move in b.legal_moves:
        t = b.copy()
        t.push(move)
        if t.fen() != b.mirror().fen():
            planted = t
            break
    best_a, info_a, _ = S.search(EXE, fen, meta)
    best_b, info_b, _ = S.search(EXE, planted.fen(), meta)
    ka, va, _ = S.parse_info(info_a)
    kb, vb, _ = S.parse_info(info_b)
    same = (ka == kb and va == vb and best_a == best_b)
    if not same:
        ok += 1
    lines.append(f"{i}: A {fen} -> {best_a} {ka} {va} | planted {planted.fen()} -> {best_b} {kb} {vb} "
                 f"| comparator says same: {same}")
text = "\n".join(lines) + f"\n\nPLANTED PAIRS DETECTED AS DIFFERENT: {ok} of {len(lines)}\n"
print(text)
with open(OUT, "w") as fh:
    fh.write(text)
