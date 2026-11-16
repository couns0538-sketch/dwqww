#!/usr/bin/env python3
"""controls.py EXE OUT.txt : controls for job 2 (left-right mirror).

A note that matters, and that I got wrong at first: a LEGAL position can never be its own left-right mirror,
because flip_horizontal maps d1->e1, so a lone white king can never be a fixed point. So "compare a symmetric
board with itself and expect 0" is not available as a control here. The controls that ARE valid:

  C1 identity: the same FEN sent twice -> the same eval line (the harness is deterministic, not random).
  C2 involution: flip(flip(FEN)) == FEN exactly (the mirror I use is a real involution, not a buggy transform).
  C3 antisymmetry of the harness: comparing A with flip(A) and then flip(A) with A must give deltas of equal
     size and OPPOSITE sign. If it does not, my comparison, not the engine, is asymmetric.
  C4 the colour-mirror control from job 1 still returns 0 (the harness is not "always different").
"""
import subprocess
import sys

import chess
import mirror_lr as M

EXE, OUT = sys.argv[1], sys.argv[2]
eng = M.Engine(EXE)
lines = []
fails = []


def add(text):
    lines.append(text)
    print(text)


POSITIONS = [
    "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1",
    "8/6k1/3p4/3P2PP/4KP2/4N3/8/8 w - - 0 1",
    "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1",
]

add("C1 identity: same FEN twice")
for fen in POSITIONS:
    a = M.parse(eng.ev(fen))
    b = M.parse(eng.ev(fen))
    ok = a == b
    add(f"  {fen}  {a} vs {b}  identical={ok}")
    if not ok:
        fails.append("C1 " + fen)

add("")
add("C2 involution: flip(flip(fen)) == fen")
for fen in POSITIONS:
    b = chess.Board(fen)
    twice = b.transform(chess.flip_horizontal).transform(chess.flip_horizontal)
    ok = twice.fen() == b.fen()
    add(f"  {fen} -> twice -> {twice.fen()}  identical={ok}")
    if not ok:
        fails.append("C2 " + fen)

add("")
add("C3 antisymmetry: delta(A, flipA) must be the exact negative of delta(flipA, A)")
for fen in POSITIONS:
    fa = chess.Board(fen).transform(chess.flip_horizontal).fen()
    a1, a2 = M.parse(eng.ev(fen)), M.parse(eng.ev(fa))
    b1, b2 = M.parse(eng.ev(fa)), M.parse(eng.ev(fen))
    d1 = {k: a1[k] - a2[k] for k in ("hce", "nnue", "total")}
    d2 = {k: b1[k] - b2[k] for k in ("hce", "nnue", "total")}
    ok = all(d1[k] == -d2[k] for k in d1)
    add(f"  {fen}\n    delta {d1}\n    reverse {d2}  exact negative={ok}")
    if not ok:
        fails.append("C3 " + fen)

add("")
add("C4 colour mirror still gives 0 (harness is not 'always different')")
for fen in POSITIONS:
    cm = chess.Board(fen).mirror().fen()
    a1, a2 = M.parse(eng.ev(fen)), M.parse(eng.ev(cm))
    d = [k for k in ("hce", "nnue", "total") if a1[k] != a2[k]]
    add(f"  {fen}  {a1} vs colour-mirror {a2}  diffs={d or 'none'}")
    if d:
        fails.append("C4 " + fen)

eng.quit()
add("")
add("CONTROLS_FAILED: " + (", ".join(fails) if fails else "none"))
with open(OUT, "w") as fh:
    fh.write("\n".join(lines) + "\n")
