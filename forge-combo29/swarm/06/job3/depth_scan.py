#!/usr/bin/env python3
"""Depth scan: for one FEN and its colour mirror, at each depth 1..N, report whether the
bestmove mirrors, whether the score is equal, and both node counts. Fresh process per search.

usage: depth_scan.py EXE FEN DEPTHMAX
"""
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]


def run(exe, fen, depth):
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
    for n, v in [("Threads", "1"), ("Hash", "16")] + S14:
        w("setoption name %s value %s" % (n, v))
        w("isready")
        ready()
    w("ucinewgame"); w("isready"); ready()
    w("position fen " + fen); w("isready"); ready()
    w("go depth %d" % depth)
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
    return {"bm": bm, "kind": t[t.index("score") + 1], "score": int(t[t.index("score") + 2]),
            "nodes": int(t[t.index("nodes") + 1]), "pv": t[t.index("pv") + 1:]}


def mir(u):
    return chess.square_name(chess.parse_square(u[0:2]) ^ 56) + chess.square_name(chess.parse_square(u[2:4]) ^ 56) + (u[4:] or "")


exe, fen, dmax = sys.argv[1], sys.argv[2], int(sys.argv[3])
mfen = chess.Board(fen).mirror().fen()
print("FEN   :", fen)
print("mirror:", mfen)
print("| depth | bm W | bm B | bm mirrors? | score W | score B | score equal? | nodes W | nodes B |")
for d in range(1, dmax + 1):
    a = run(exe, fen, d)
    b = run(exe, mfen, d)
    print("| %d | %s | %s | %s | %s %d | %s %d | %s | %d | %d |" %
          (d, a["bm"], b["bm"], b["bm"] == mir(a["bm"]),
           a["kind"], a["score"], b["kind"], b["score"],
           (a["kind"] == b["kind"] and a["score"] == b["score"]), a["nodes"], b["nodes"]))
