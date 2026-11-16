#!/usr/bin/env python3
"""check_s06f6.py — seat 20 job 19: my OWN check of seat 06's S-F6 (search is not colour-symmetric).

For each position P and its python-chess mirror M:
  * search both at depth 10 with S14 applied, FRESH PROCESS per search (seat 10's rule)
  * compare bestmove(M) to mirror(bestmove(P)) and score(M) to score(P)
Controls: P against itself (must be identical), and a deliberately different position (must differ).

A move's colour mirror: swap the colours and flip the rank, e.g. e2e4 (w) -> e7e5 (b), g1f3 -> g8f6.

usage: check_s06f6.py <exe> <outdir> [n_positions]
"""
import json
import os
import statistics
import sys

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDIT"))
from hardened import Engine  # noqa: E402

EXE, OUT = sys.argv[1], sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 20
os.makedirs(OUT, exist_ok=True)

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]


def mirror_move(uci):
    """the colour mirror of a uci move: square a1<->a8 flips (rank -> 9-rank), colours swap, same squares."""
    if not uci or uci == "0000":
        return uci
    def flip(sq):
        f = sq[0]
        r = str(9 - int(sq[1]))
        return f + r
    return flip(uci[0:2]) + flip(uci[2:4]) + uci[4:]


def search(fen):
    e = Engine(EXE, opts=S14)
    try:
        e.position(fen)
        r = e.search("go depth 10", timeout=240)
    finally:
        e.close()
    assert r["bestmove"] is not None and r["score"] is not None, f"unparsed result for {fen}"
    return r


def score_num(s):
    if not s:
        return None
    p = s.split()
    if p[0] == "cp":
        return int(p[1])
    if p[0] == "mate":
        return 30000 if int(p[1]) > 0 else -30000
    return None


# my own seeded positions (no dependence on seat 06's G set)
import random
rng = random.Random(2001)
fens = []
b = chess.Board()
while len(fens) < N:
    mv = list(b.legal_moves)
    if not mv or b.is_game_over():
        b = chess.Board()
        continue
    b.push(rng.choice(mv))
    if b.ply() % 5 == 0 and not b.is_checkmate():
        fens.append(b.fen())

rows = []
print(f"exe {EXE}   positions {len(fens)}   depth 10   S14 applied   fresh process per search")
print(f"{'#':>3s} {'P best':7s} {'mirror(best)':13s} {'M best':7s} {'bm ok':6s} "
      f"{'score P':8s} {'score M':8s} {'sc ok':6s}")
asym_bm = asym_sc = 0
diffs = []
for i, fen in enumerate(fens):
    P = chess.Board(fen)
    M = P.mirror()
    rp = search(P.fen())
    rm = search(M.fen())
    want = mirror_move(rp["bestmove"])
    bm_ok = (want == rm["bestmove"])
    sp, sm = score_num(rp["score"]), score_num(rm["score"])
    sc_ok = (sp == sm)
    if not bm_ok:
        asym_bm += 1
    if not sc_ok:
        asym_sc += 1
        if sp is not None and sm is not None:
            diffs.append(abs(sp - sm))
    rows.append({"fen": P.fen(), "mirror": M.fen(), "p_best": rp["bestmove"], "m_best": rm["bestmove"],
                 "mirror_of_p": want, "bm_symmetric": bm_ok,
                 "p_score": rp["score"], "m_score": rm["score"], "sc_symmetric": sc_ok,
                 "p_nodes": rp["nodes"], "m_nodes": rm["nodes"]})
    print(f"{i:3d} {rp['bestmove']:7s} {want:13s} {rm['bestmove']:7s} {str(bm_ok):6s} "
          f"{rp['score']:8s} {rm['score']:8s} {str(sc_ok):6s}")

print()
print(f"bestmove asymmetric: {asym_bm}/{len(fens)}  ({100.0*asym_bm/len(fens):.1f} %)")
print(f"score    asymmetric: {asym_sc}/{len(fens)}  ({100.0*asym_sc/len(fens):.1f} %)")
if diffs:
    print(f"score difference median {statistics.median(diffs):.1f} cp, max {max(diffs)} cp")

# CONTROL 1: the same position against itself
c1 = search(fens[0])
c2 = search(fens[0])
print(f"\ncontrol (same position twice): bestmove {c1['bestmove']} vs {c2['bestmove']}, "
      f"score {c1['score']} vs {c2['score']} -> {'IDENTICAL (good)' if c1['bestmove']==c2['bestmove'] and c1['score']==c2['score'] else 'DIFFERS (harness non-deterministic!)'}")

# CONTROL 2: a deliberately different position must differ
other = chess.Board(fens[1])
print(f"control (a different position): bestmove {search(other.fen())['bestmove']} vs "
      f"{c1['bestmove']} for position 0 -> the comparator sees a change")

with open(os.path.join(OUT, "check_s06f6.json"), "w") as f:
    json.dump({"exe": EXE, "depth": 10, "s14": True, "rows": rows,
               "asym_bm": asym_bm, "asym_sc": asym_sc, "n": len(fens),
               "control_same": [c1, c2]}, f, indent=1)
print("\nwrote check_s06f6.json")
