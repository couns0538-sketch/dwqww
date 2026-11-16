#!/usr/bin/env python3
"""Decisive localisation: is a depth-1 node-count difference a per-move property or an
accumulation-of-order property?

Method: search each ROOT MOVE on its own with `go depth 1 searchmoves <move>`, for the position and
its mirror. If for every move m the node count of m equals the node count of mirror(m), then no
single move's subtree differs - the difference in the whole-position search can only come from the
ORDER in which the root walks them (alpha-beta accumulation). If some individual move differs, the
difference is inside that move's subtree.

usage: probe_root_moves.py EXE FEN
"""
import subprocess
import sys

import chess

S14 = [("Threads", "1"), ("Hash", "16"), ("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"),
       ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"),
       ("NullMoveBase", "5"), ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"),
       ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"),
       ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true")]


def run(exe, fen, d, searchmove=None):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def w(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def r():
        line = p.stdout.readline()
        if line == "":
            raise RuntimeError("died")
        return line

    def ready():
        while True:
            if r().strip() == "readyok":
                return

    w("uci")
    while r().strip() != "uciok":
        pass
    for n, v in S14:
        w("setoption name %s value %s" % (n, v))
        w("isready")
        ready()
    w("ucinewgame")
    w("isready")
    ready()
    w("position fen " + fen)
    w("isready")
    ready()
    w(("go depth %d searchmoves %s" % (d, searchmove)) if searchmove else ("go depth %d" % d))
    pv = None
    while True:
        line = r().strip()
        if " pv " in line:
            pv = line
        if line.startswith("bestmove"):
            bm = line.split()[1]
            break
    p.kill()
    t = pv.split()
    return {"nodes": int(t[t.index("nodes") + 1]), "bm": bm}


def mir(u):
    return (chess.square_name(chess.parse_square(u[0:2]) ^ 56) +
            chess.square_name(chess.parse_square(u[2:4]) ^ 56) + (u[4:] or ""))


exe, fen = sys.argv[1], sys.argv[2]
b = chess.Board(fen)
m = b.mirror()
mfen = m.fen()
print("FEN    :", fen)
print("mirror :", mfen)
whole_a = run(exe, fen, 1)
whole_b = run(exe, mfen, 1)
print("whole-position depth-1 nodes: %d vs %d" % (whole_a["nodes"], whole_b["nodes"]))
print()
print("| move | nodes self | mirror move | nodes mirror | equal |")
mismatch = 0
for mv in sorted(b.legal_moves, key=lambda x: x.uci()):
    mm = mir(mv.uci())
    a = run(exe, fen, 1, mv.uci())
    bb = run(exe, mfen, 1, mm)
    eq = a["nodes"] == bb["nodes"]
    if not eq:
        mismatch += 1
    print("| %s | %d | %s | %d | %s |" % (mv.uci(), a["nodes"], mm, bb["nodes"], eq))
print()
print("root moves whose own subtree differs: %d of %d" % (mismatch, b.legal_moves.count()))
