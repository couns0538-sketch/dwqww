#!/usr/bin/env python3
"""positive_control.py : prove the harness REPORTS a difference when one exists.

A) TRUE PAIRS: three mirror pairs (Q vs Q, P vs p, R vs r) - must report 0 differences.
B) FORCED ASYMMETRY: same Engine, second FEN is a deliberately WRONG "mirror" (white queen on d1
   compared with a white queen on f1). The harness must report a difference, otherwise the
   "0 differences" of the main run would prove nothing.
Writes positive_control.txt.
"""
import io
import os

import chess

import mirror_eval as M

EXE = os.path.expanduser("~/builds/bld-release/forge")

pairs = [
    ("Q vs Q", "4k3/8/8/8/8/8/8/3QK3 w - - 0 1"),
    ("P vs p", "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1"),
    ("R vs r", "r3k3/8/8/8/8/8/8/R3K3 w - - 0 1"),
]

out = io.StringIO()
eng = M.Engine(EXE)
out.write("control A: true mirror pairs (must be EQUAL)\n")
for label, fen in pairs:
    mir = chess.Board(fen).mirror().fen()
    e1 = M.parse(eng.eval_fen(fen))
    e2 = M.parse(eng.eval_fen(mir))
    diffs = [k for k in ("hce", "nnue", "total") if e1.get(k) != e2.get(k)]
    out.write(f"  {label:8s} {fen:40s} {e1}  vs  {e2}  diffs={diffs or 'none'}\n")

out.write("\ncontrol B: forced asymmetry (must be DIFFERENT)\n")
fen_a = "4k3/8/8/8/8/8/8/3QK3 w - - 0 1"
fen_wrong = "4k3/8/8/8/8/8/8/4KQ2 w - - 0 1"
e1 = M.parse(eng.eval_fen(fen_a))
e2 = M.parse(eng.eval_fen(fen_wrong))
diffs = [k for k in ("hce", "nnue", "total") if e1.get(k) != e2.get(k)]
out.write(f"  A            {fen_a}\n  {e1}\n")
out.write(f"  wrong mirror {fen_wrong}\n  {e2}\n")
out.write(f"  diffs={diffs or 'none'}\n")
eng.quit()

text = out.getvalue()
print(text)
with open("positive_control.txt", "w") as fh:
    fh.write(text)
