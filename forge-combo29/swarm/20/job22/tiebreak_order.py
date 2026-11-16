#!/usr/bin/env python3
"""tiebreak_order.py — seat 20 job 22: how does the engine break ties among equal-scored root moves?

The source (src/search.cpp:817-862) has TWO different tie rules in `pick_best`:
  * fewer than 4 moves left: a scalar loop with `score > best_score`, i.e. the FIRST move wins a tie;
  * 4 or more: an AVX2 chunk-max that takes `__builtin_ctz(mask)`, i.e. also the FIRST in chunk order, but the
    chunking permutes lanes (setr(1,3,5,7,0,2,4,6)), so a tie can resolve differently than a plain scalar loop.

The observable question I can settle without reading more code: at a fixed shallow depth, does the engine return the
FIRST legal move when several moves are equal? I test positions where many moves are provably equivalent (a lone
king shuffling) and a real position at depth 1-2 where ties are common.

usage: tiebreak_order.py <exe> <outdir>
"""
import json
import os
import sys

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDIT"))
from hardened import Engine  # noqa: E402

EXE, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

CASES = [
    ("KvK_lone_king", "8/8/8/8/8/8/8/K6k w - - 0 1"),
    ("KvK_second", "8/8/8/8/8/8/7k/K7 w - - 0 1"),
    ("KR_v_K", "3k4/8/8/R7/8/8/8/7K w - - 0 1"),
    ("startpos", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    ("italian", "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1"),
]

rows = []
print(f"exe {EXE}")
print(f"{'case':16s} {'depth':>5s} {'#legal':>6s} {'bestmove':9s} {'first legal':11s} {'= first?':8s} {'score':8s}")
for name, fen in CASES:
    b = chess.Board(fen)
    legal = [m.uci() for m in b.legal_moves]           # python-chess order (a1..h8 by from-square)
    for depth in (1, 2, 3):
        e = Engine(EXE)
        try:
            e.position(fen)
            r = e.search(f"go depth {depth}", 60)
        finally:
            e.close()
        assert r["bestmove"] and r["score"], f"unparsed for {name} d{depth} — refusing to record"
        isfirst = (r["bestmove"] == legal[0])
        rows.append({"case": name, "depth": depth, "n_legal": len(legal), "bestmove": r["bestmove"],
                     "first_legal": legal[0], "is_first": isfirst, "score": r["score"],
                     "bestmove_index": legal.index(r["bestmove"]) if r["bestmove"] in legal else None})
        print(f"{name:16s} {depth:5d} {len(legal):6d} {r['bestmove']:9s} {legal[0]:11s} "
              f"{str(isfirst):8s} {r['score']:8s}")

with open(os.path.join(OUT, "tiebreak_order.json"), "w") as f:
    json.dump({"exe": EXE, "rows": rows}, f, indent=1)
print("\nwrote tiebreak_order.json")
