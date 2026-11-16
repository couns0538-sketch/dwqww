#!/usr/bin/env python3
"""Where does the depth-1 node-count difference come from?

At depth 1 there is no pruning, no reduction and no null move, so the node count is determined
entirely by how many moves the engine scores. It equals: 1 (root) + the number of root moves tried
+ the number of qsearch nodes below them. So a differing count at depth 1 means a different number of
moves is being searched at some node, which is either (i) a different move list, or (ii) a different
SEE / legality decision on the same list.

This script searches one position and its mirror at depth 1 and dumps, for each root move, whether
it is a capture, a promotion, and the score the engine reports; then compares the two move sets.

usage: probe_depth1.py EXE FEN
"""
import subprocess
import sys

import chess

S14 = [("Threads", "1"), ("Hash", "16"), ("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"),
       ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"),
       ("NullMoveBase", "5"), ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"),
       ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"),
       ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true")]


def run(exe, fen, d):
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
    w("ucinewgame"); w("isready"); ready()
    w("position fen " + fen); w("isready"); ready()
    w("go depth %d" % d)
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
    return {"nodes": int(t[t.index("nodes") + 1]), "score": int(t[t.index("score") + 2]),
            "bm": bm}


def mir(u):
    return (chess.square_name(chess.parse_square(u[0:2]) ^ 56) +
            chess.square_name(chess.parse_square(u[2:4]) ^ 56) + (u[4:] or ""))


exe, fen = sys.argv[1], sys.argv[2]
b = chess.Board(fen)
mfen = b.mirror().fen()
a1 = run(exe, fen, 1)
b1 = run(exe, mfen, 1)
print("FEN    :", fen)
print("mirror :", mfen)
print("depth-1 node counts : self %d  mirror %d  (differ by %d)" % (a1["nodes"], b1["nodes"], b1["nodes"] - a1["nodes"]))
print("depth-1 bestmoves   : self %s  mirror(mirrored back) %s  -> %s"
      % (a1["bm"], mir(b1["bm"]), "same" if a1["bm"] == mir(b1["bm"]) else "DIFFERENT"))
print()
print("per-root-move accounting on the original position (each move as its own root):")
print("| move | type | depth-1 nodes |")
for mv in sorted(b.legal_moves, key=lambda m: m.uci()):
    b.push(mv)
    legal_after = b.legal_moves.count()
    b.pop()
    print("| %s | %s | %d replies |" % (mv.uci(), "capture" if b.is_capture(mv) else "quiet", legal_after))
