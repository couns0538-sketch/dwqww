#!/usr/bin/env python3
"""depth_series.py EXE OUT.txt : score of each mate/cp position and its mirror at depths 1..12,
and the same position searched twice at depth 10 (determinism check)."""
import re
import subprocess
import sys
import time

import chess

EXE, OUT = sys.argv[1], sys.argv[2]
DEPTHS = [1, 2, 4, 6, 8, 10, 12]

POSITIONS = [
    ("G69", "k7/6R1/5N2/p4K1P/P7/8/8/8 b - - 0 1"),
    ("G184", "5K2/1p1k2Nb/4p3/4P3/8/P3q3/8/8 w - - 0 1"),
    ("G196", "5Q2/1k6/3pK1PP/3P4/8/4N3/8/8 w - - 0 1"),
    ("G217", "8/7p/8/7p/3k2b1/6K1/2p5/8 b - - 0 1"),
    ("R120", "3rkb1r/p3ppp1/4bq1p/2n5/N1pP1P1P/1Pp1P3/P1P1B3/R2QK2R w KQk - 0 1"),
]


def one(exe, fen, depth):
    script = ["uci", "isready", "setoption name Threads value 1", "isready",
              "setoption name Hash value 16", "isready",
              "setoption name LmrQuietBase value 93", "isready",
              "setoption name LmrQuietDivisor value 205", "isready",
              "setoption name NonPawnCorrection value true", "isready",
              f"position fen {fen}", "isready", f"go depth {depth}"]
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    for c in script:
        p.stdin.write(c + "\n")
        p.stdin.flush()
    lines = []
    deadline = time.monotonic() + 300
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
    best = next((l.split()[1] for l in lines if l.startswith("bestmove")), None)
    score = None
    for l in lines:
        m = re.match(rf"^info depth {depth} .*score (cp|mate) (-?\d+)", l)
        if m:
            score = f"{m.group(1)} {m.group(2)}"
    return best, score


lines = []
for label, fen in POSITIONS:
    b = chess.Board(fen)
    mir = b.mirror()
    lines.append(f"### {label} {fen}")
    for depth in DEPTHS:
        a = one(EXE, fen, depth)
        c = one(EXE, mir.fen(), depth)
        lines.append(f"  depth {depth:2d}: A {a[0]} {a[1]:12s} | mirror {c[0]} {c[1]}")
    # determinism: same position, same depth, twice
    r1 = one(EXE, fen, 10)
    r2 = one(EXE, fen, 10)
    lines.append(f"  determinism depth 10 twice: {r1} vs {r2}  identical={r1 == r2}")
    lines.append("")
text = "\n".join(lines) + "\n"
print(text)
with open(OUT, "w") as fh:
    fh.write(text)
