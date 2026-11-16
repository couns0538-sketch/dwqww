#!/usr/bin/env python3
"""check_f12.py EXE OUT.txt : per-move vs whole-position depth-1 node counts, position vs colour mirror.

For the position and its colour mirror:
  - `go depth 1` (whole position) -> node count
  - for each legal root move, `go depth 1 searchmoves <move>` -> node count
  - map each mirror move back (square ^ 56) and compare counts move by move.
"""
import re
import subprocess
import sys
import time

import chess

EXE, OUT = sys.argv[1], sys.argv[2]


def run(fen, extra=""):
    script = ["uci", "isready", "setoption name OwnBook value false", "isready",
              "setoption name Threads value 1", "isready", "setoption name Hash value 16", "isready",
              f"position fen {fen}", "isready", f"go depth 1{extra}"]
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    for c in script:
        p.stdin.write(c + "\n")
        p.stdin.flush()
    lines = []
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        line = p.stdout.readline()
        if not line:
            break
        lines.append(line.rstrip("\n"))
        if line.startswith("bestmove"):
            break
    try:
        p.stdin.write("quit\n")
        p.stdin.flush()
        p.wait(timeout=5)
    except Exception:
        p.kill()
    nodes = None
    for l in lines:
        m = re.match(r"^info depth 1 .*nodes (\d+)", l)
        if m:
            nodes = int(m.group(1))
    best = next((l.split()[1] for l in lines if l.startswith("bestmove")), None)
    return best, nodes


FEN = "R7/8/8/5p1p/5K1P/1kpr2n1/8/8 b - - 0 1"
b = chess.Board(FEN)
mir = b.mirror()

out = []
out.append(f"position     {b.fen()}")
out.append(f"colour mirror {mir.fen()}")
out.append(f"legal root moves: {b.legal_moves.count()} / {mir.legal_moves.count()}")

wm_a = run(FEN)
wm_b = run(mir.fen())
out.append(f"whole position depth 1: A {wm_a} | mirror {wm_b}")
out.append(f"P1 whole-position node counts differ: {wm_a[1] != wm_b[1]}  (pair {wm_a[1]},{wm_b[1]})")
out.append("")

per_move_a = {}
for mv in sorted(b.legal_moves, key=lambda m: m.uci()):
    best, nodes = run(FEN, f" searchmoves {mv.uci()}")
    per_move_a[mv.uci()] = (nodes, best)

per_move_b = {}
for mv in sorted(mir.legal_moves, key=lambda m: m.uci()):
    best, nodes = run(mir.fen(), f" searchmoves {mv.uci()}")
    per_move_b[mv.uci()] = (nodes, best)

out.append("move | A nodes | mirrored move | mirror nodes | same")
diff = 0
total_a = 0
total_b = 0
for m1 in sorted(per_move_a):
    mv = chess.Move.from_uci(m1)
    back = chess.Move(mv.from_square ^ 56, mv.to_square ^ 56, mv.promotion).uci()
    if back not in per_move_b:
        out.append(f"{m1} | {per_move_a[m1][0]} | {back} | MISSING (promotion mismatch?) | -")
        continue
    na = per_move_a[m1][0]
    nb = per_move_b[back][0]
    total_a += na or 0
    total_b += nb or 0
    same = (na == nb)
    diff += (not same)
    out.append(f"{m1} | {na} | {back} | {nb} | {same}")
out.append("")
out.append(f"P2 per-move pairs differing: {diff} of {len(per_move_a)}")
out.append(f"P3 sum of per-move counts: A {total_a} vs mirror {total_b}; whole position A {wm_a[1]} "
           f"mirror {wm_b[1]}")
text = "\n".join(out) + "\n"
print(text)
with open(OUT, "w") as fh:
    fh.write(text)
