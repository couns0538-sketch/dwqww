#!/usr/bin/env python3
"""conv_check.py EXE OUT.txt : is `eval` side-to-move relative (seat 20's S-F14)?

Four boards: the finding's board with white to move, its colour mirror (black to move), the same board with
black to move, and the colour mirror with white to move. Under a side-to-move-relative eval the mirror of a
position scores the SAME; the same board with the other side to move scores roughly its NEGATIVE.
"""
import subprocess
import sys

import chess

EXE, OUT = sys.argv[1], sys.argv[2]
CASES = [
    ("finding board, white to move", "4k3/8/8/8/8/8/8/QQQQK3 w - - 0 1"),
    ("its colour mirror, black to move", "qqqqk3/8/8/8/8/8/8/4K3 b - - 0 1"),
    ("same board, BLACK to move", "4k3/8/8/8/8/8/8/QQQQK3 b - - 0 1"),
    ("its colour mirror, white to move", "qqqqk3/8/8/8/8/8/8/4K3 w - - 0 1"),
]


def ev(fen):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    for c in ["uci", "isready", f"position fen {fen}", "isready", "eval", "isready", "quit"]:
        p.stdin.write(c + "\n")
        p.stdin.flush()
    lines = []
    while True:
        line = p.stdout.readline()
        if not line:
            break
        lines.append(line.rstrip("\n"))
        if line.startswith("info string eval"):
            break
    try:
        p.kill()
    except Exception:
        pass
    for l in lines:
        if l.startswith("info string eval"):
            return l
    return None


out = []
vals = {}
for label, fen in CASES:
    line = ev(fen)
    vals[label] = line
    # sanity: is the board legal / is python-chess's mirror really this board?
    b = chess.Board(fen)
    mir = b.mirror()
    is_mirror_of_first = mir.fen() == chess.Board(CASES[0][1]).fen()
    out.append(f"{label}\n  fen {fen}\n  {line}\n  (python-chess: this is the colour mirror of case 1: "
               f"{is_mirror_of_first})")

# also: what a NEGATED comparison would conclude
def num(line):
    for tok in line.split():
        pass
    parts = line.split()
    return {parts[i]: int(parts[i + 1]) for i in range(len(parts) - 1)
            if parts[i] in ("hce", "nnue", "total")}


a = num(vals["finding board, white to move"])
b = num(vals["its colour mirror, black to move"])
c = num(vals["same board, BLACK to move"])
out.append("")
out.append(f"mirror reads the SAME as the original (S-F14's claim): "
           f"hce {a['hce']} vs {b['hce']} -> {a['hce'] == b['hce']}")
out.append(f"a NEGATION-based checker would call this a FALSE fault: "
           f"requires {b['hce']} == {-a['hce']} -> {-a['hce'] == b['hce']} "
           f"(so it would report a difference of {abs(b['hce'] + a['hce'])} cp per position)")
out.append(f"same board with black to move: hce {c['hce']} (negative of the white-to-move value: "
           f"{c['hce'] == -a['hce']})")
text = "\n".join(out) + "\n"
print(text)
with open(OUT, "w") as fh:
    fh.write(text)
