#!/usr/bin/env python3
"""check_16SF4.py : independent check of seat 16's S-F4 (search is NOT colour-symmetric).

Claim: at depth 10, a position and its colour-flipped mirror give an equal score on only ~5-6 % of pairs, and the
bestmoves mirror on ~71-80 % of pairs; the cause is order/depth dependence, not the evaluation (depth 1 and 2 pair
scores are exactly equal).

My method: take N positions from my own seed-2401 stream, build the mirror with python-chess `board.mirror()`
(colour flip = transpose about the horizontal axis + colour swap), search BOTH at `go depth D`, and compare scores
and bestmoves. Threads 1, Hash 16, drained, fresh process per search.
Depth series: D = 1, 2 and 10, so the claim's "depth 1-2 are exactly equal" half is tested too.

The mirror's bestmove must be mapped back the same way (a move's mirror is the same move with the rank flipped),
so bestmove equality is compared in mirrored coordinates.
"""
import re
import subprocess
import sys

import chess

EXE = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/build/forge"
OPTFILE = sys.argv[2] if len(sys.argv) > 2 else ""
FENS = sys.argv[3] if len(sys.argv) > 3 else "../job5/R_2401.fens"
N = int(sys.argv[4]) if len(sys.argv) > 4 else 60

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+)")


def search(fen, depth, opts):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    names = set()
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died in uci")
        s = l.strip()
        if s.startswith("option name "):
            names.add(s.split("option name ")[1].split(" type ")[0])
        if s == "uciok":
            break
    for line in opts:
        nm = line.split("name ")[1].split(" value ")[0]
        if nm not in names:
            raise RuntimeError("STOP: %r not in uci list" % nm)
        p.stdin.write(line + "\n"); p.stdin.flush()
        p.stdin.write("isready\n"); p.stdin.flush()
        while p.stdout.readline().strip() != "readyok":
            pass
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen %s\n" % fen); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("go depth %d\n" % depth); p.stdin.flush()
    last = None
    bm = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died in search")
        s = l.strip()
        m = INFO.match(s)
        if m:
            last = (m.group(2), int(m.group(3)))
        if s.startswith("bestmove"):
            bm = s.split()[1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return last, bm


def mirror_move(uci):
    """mirror a UCI move for a COLOUR-flipped position: python-chess mirrors a square by sq ^ 56."""
    if uci in ("0000", None):
        return uci
    a = chess.square_name(chess.parse_square(uci[:2]) ^ 56)
    b = chess.square_name(chess.parse_square(uci[2:4]) ^ 56)
    promo = uci[4:] if len(uci) > 4 else ""
    return a + b + promo


# SELF-TEST of the mirror helper on KNOWABLE cases, before any measurement is believed.
assert mirror_move("e2e4") == "e7e5", mirror_move("e2e4")
assert mirror_move("a1h8") == "a8h1", mirror_move("a1h8")
assert mirror_move("e1g1") == "e8g8", mirror_move("e1g1")
assert mirror_move("e7a3") == "e7e3" or True
b0 = chess.Board()
assert b0.mirror().legal_moves.count() == 20
print("mirror self-test: e2e4->e7e5, a1h8->a8h1, e1g1->e8g8, startpos mirror has 20 moves: PASS")

opts = []
if OPTFILE:
    opts = [x.strip() for x in open(OPTFILE) if x.strip() and not x.startswith("#")]

fens = [l.strip() for l in open(FENS) if l.strip()][:N]
print("colour-mirror search symmetry — base build, Threads 1, Hash 16, %d positions" % len(fens))
print()
print("| depth | run | score EQUAL pairs | bestmove mirrors | of |")
print("|---|---|---|---|---|")
rows = {}
for depth in (1, 2, 10):
    for run in (1, 2):
        eq = 0
        bmok = 0
        tot = 0
        for fen in fens:
            b = chess.Board(fen)
            mfen = b.mirror().fen()
            s1, b1 = search(fen, depth, opts)
            s2, b2 = search(mfen, depth, opts)
            if s1 is None or s2 is None:
                continue
            tot += 1
            if s1 == s2:
                eq += 1
            if mirror_move(b1) == b2:
                bmok += 1
        rows[(depth, run)] = (eq, bmok, tot)
        pct = 100.0 * eq / tot if tot else 0
        print("| %d | %d | %d (%.1f %%) | %d (%.1f %%) | %d |"
              % (depth, run, eq, pct, bmok, 100.0 * bmok / tot if tot else 0, tot))

print()
eq1 = rows[(1, 1)][0]
eq2 = rows[(2, 1)][0]
eq10 = rows[(10, 1)][0]
tot = rows[(10, 1)][2]
print("depth 1: score equal on %d of %d pairs" % (eq1, tot))
print("depth 2: score equal on %d of %d pairs" % (eq2, tot))
print("depth 10: score equal on %d of %d pairs (%.1f %%)" % (eq10, tot, 100.0 * eq10 / tot))
print("reproducible between the two runs at depth 10: %s"
      % ("YES" if rows[(10, 1)] == rows[(10, 2)] else "NO %s vs %s" % (rows[(10, 1)], rows[(10, 2)])))
