#!/usr/bin/env python3
"""Find boards that (a) have a mate available for the mover, (b) admit a castling-neutral 4-ply cycle, and
(c) whose threefold root validates. Then test base vs PC at depths 4/10/20."""
import re, subprocess, os, sys, itertools
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'job59'))
import chess
from validate import check_fixture, identity

def cycles(fen, limit=3):
    b = chess.Board(fen); target = identity(b); cf = b.castling_xfen() or '-'
    out = []
    def dfs(bb, path):
        if len(out) >= limit: return
        if len(path) == 4:
            if identity(bb) == target: out.append(list(path))
            return
        for m in bb.legal_moves:
            if bb.is_capture(m): continue
            bb.push(m)
            if (bb.castling_xfen() or '-') != cf or bb.is_check():
                bb.pop(); continue
            bb.pop(); bb.push(m)
            dfs(bb, path + [m.uci()])
            bb.pop()
    dfs(b, []); return out

# boards with plenty of quiet shuttles AND a forced mate nearby
CANDS = [
 "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1",
 "r5k1/5ppp/8/8/8/8/5PPP/6K1 w - - 0 1",
 "6k1/5ppp/8/8/8/8/5PPP/1R4K1 w - - 0 1",
 "8/8/8/5k2/8/8/5PPP/1R4K1 w - - 0 1",
 "3qk3/8/8/8/8/8/5PPP/3QK3 w - - 0 1",
 "4k3/8/8/8/8/8/8/R3K3 w Q - 0 1",
 "4k3/8/8/8/8/8/8/4K2R w K - 0 1",
 "1r4k1/5ppp/8/8/8/8/5PPP/1R4K1 w - - 0 1",
 "6k1/6pp/8/8/8/8/6PP/1R4K1 w - - 0 1",
 "6k1/5p1p/6p1/8/8/8/1R4PP/6K1 w - - 0 1",
]
print("| board | neutral cycles | usable? |")
print("|---|---|---|")
good = []
for fen in CANDS:
    b = chess.Board(fen)
    if not b.is_valid():
        print("| %s | INVALID | - |" % fen); continue
    cs = cycles(fen)
    usable = None
    for c in cs:
        moves = c * 2
        ok, msg = check_fixture(fen, moves, expect=3)
        if ok:
            usable = (c, moves); break
    print("| `%s` | %d | %s |" % (fen, len(cs), "**YES** " + " ".join(usable[0]) if usable else "no"))
    if usable: good.append((fen, usable[1]))
print()
print("usable boards:", len(good))
for fen, moves in good:
    print("  ", fen, "|", " ".join(moves))
import json
json.dump([(f, m) for f, m in good], open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "boards.json"), "w"))
