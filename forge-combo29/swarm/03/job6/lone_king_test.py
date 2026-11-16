#!/usr/bin/env python3
"""lone_king_test.py BMFILE FENFILE OUT : is the divergence EXACTLY the set of positions with a lone king at the root?

The r15 patch's FORGE_FIX_BARE_KING_LMR_CAP is gated on `root_bare_king_` (src/search.cpp: `bare_king_lmr_cap =
!bare_king_mode && root_bare_king_ && ...`), i.e. it only acts when the ROOT position has a side owning nothing but
its king. My earlier material buckets were a proxy for that; this tests the actual condition.

A position "has a lone king" when one side's occupied squares equal exactly its king's square.

Also reports, for the positions with a lone king, whether the divergence is one of them, so the claim can be stated
as a set equality (all-and-only) or refuted.
"""
import sys

import chess

bmfile, fenfile, out = sys.argv[1], sys.argv[2], sys.argv[3]
fens = [l.strip().split("\t")[-1] for l in open(fenfile) if l.strip()]
rows = {}
for line in open(bmfile):
    p = line.rstrip("\n").split("\t")
    if len(p) >= 4 and p[0].isdigit():
        rows[int(p[0])] = p

lone, nonlone = [], []
for idx in sorted(rows):
    b = chess.Board(fens[idx])
    is_lone = (b.occupied_co[chess.WHITE] == b.pieces(chess.KING, chess.WHITE) or
               b.occupied_co[chess.BLACK] == b.pieces(chess.KING, chess.BLACK))
    (lone if is_lone else nonlone).append(idx)

diff = [i for i in sorted(rows) if rows[i][3] == "DIFF"]
lone_diff = [i for i in diff if i in lone]
nonlone_diff = [i for i in diff if i in nonlone]

lines = [
    f"positions measured: {len(rows)}",
    f"positions with a lone king at the root: {len(lone)}  -> indices {lone}",
    f"positions with no lone king at the root: {len(nonlone)}",
    f"differing positions: {diff}",
    "",
    f"differing AND lone-king root: {len(lone_diff)} of {len(lone)}"
    f"   ({', '.join(str(i) for i in lone_diff) if lone_diff else 'none'})",
    f"differing AND NOT lone-king root: {len(nonlone_diff)} of {len(nonlone)}"
    f"   ({', '.join(str(i) for i in nonlone_diff) if nonlone_diff else 'none'})",
    "",
]
if set(diff) == set(lone_diff) and len(diff) > 0:
    lines.append("VERDICT: the differing set is EXACTLY a subset of the lone-king-root positions, and every "
                 "difference lies there.")
elif len(diff) == 0:
    lines.append("VERDICT: no differences to explain.")
else:
    lines.append("VERDICT: the differing set is NOT confined to lone-king-root positions.")

# per-position detail for the lone-king roots
lines.append("")
lines.append("| idx | lone king side | base bm | pc bm | verdict |")
lines.append("|---|---|---|---|---|")
for idx in lone:
    b = chess.Board(fens[idx])
    side = "white" if b.occupied_co[chess.WHITE] == b.pieces(chess.KING, chess.WHITE) else "black"
    lines.append(f"| {idx} | {side} | {rows[idx][1]} | {rows[idx][2]} | {rows[idx][3]} |")

open(out, "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
