#!/usr/bin/env python3
"""order_test.py EXE OUT.txt : is the GENERATED move order mirror-corresponding?

For a position and its colour mirror, get the move list the engine generates (the perft-1 divide order is the
generator's order) and compare it, move by move, against the mirrored sequence of the original. If the order is
not the mirror image, then any search that breaks ties by first-found takes a different path on the two sides -
a deterministic, order-only cause for the node-count asymmetry.

Also computes how many positions in G have a mirror-corresponding generation order, so the size of the effect
is known rather than inferred from one position.
"""
import re
import subprocess
import sys

import chess

EXE, OUT = sys.argv[1], sys.argv[2]


def gen_order(fen):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    for c in ["uci", "isready", "position fen " + fen, "isready", "go perft 1"]:
        p.stdin.write(c + "\n")
        p.stdin.flush()
    moves = []
    while True:
        l = p.stdout.readline()
        if not l:
            break
        l = l.rstrip("\n")
        m = re.match(r"^([a-h][1-8][a-h][1-8][qrbn]?): \d+$", l)
        if m:
            moves.append(m.group(1))
        if l.strip().startswith("nodes"):
            break
    p.stdin.write("isready\n")
    p.stdin.flush()
    while True:
        l = p.stdout.readline()
        if not l or l.strip() == "readyok":
            break
    p.stdin.write("quit\n")
    p.stdin.flush()
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    return moves


def mirror_move(mv):
    m = chess.Move.from_uci(mv)
    return chess.Move(m.from_square ^ 56, m.to_square ^ 56, m.promotion).uci()


CASES = [("R7/8/8/5p1p/5K1P/1kpr2n1/8/8 b - - 0 1", "the S-F8 probe position")]
fens = [l.strip() for l in open("/agent/repos/dwqww/forge-combo29/swarm/16/job2/G_nocastle.fens")
        if l.strip()][:40]
CASES += [(f, f"G_nocastle #{i}") for i, f in enumerate(fens)]

out = []
same_order = 0
for fen, label in CASES:
    b = chess.Board(fen)
    mir = b.mirror()
    a = gen_order(fen)
    c = gen_order(mir.fen())
    expected = [mirror_move(m) for m in a]
    ok = (expected == c)
    same_order += ok
    out.append(f"{label}: {fen}")
    out.append(f"  order matches the mirror order: {ok}   moves {len(a)}")
    if not ok:
        out.append(f"  A order      : {' '.join(a)}")
        out.append(f"  mirror order : {' '.join(c)}")
        out.append(f"  A mirrored   : {' '.join(expected)}")
        for i, (x, y) in enumerate(zip(expected, c)):
            if x != y:
                out.append(f"  first divergence at index {i}: expected {x}, got {y}")
                break
    if label.startswith("the S-F8"):
        print("\n".join(out[-4:]) if not ok else out[-1])

out.append("")
out.append(f"positions whose GENERATION ORDER mirrors exactly: {same_order} of {len(CASES)}")
text = "\n".join(out) + "\n"
print(out[-1])
with open(OUT, "w") as fh:
    fh.write(text)
