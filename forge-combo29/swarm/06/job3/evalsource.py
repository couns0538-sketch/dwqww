#!/usr/bin/env python3
"""Which eval source breaks search symmetry?

Searches one FEN and its colour mirror in fresh processes at a fixed depth under several
evaluation configurations, and reports bestmove mirroring, score equality and both node counts.
Node counts are the sharper signal: a symmetric search must visit the same number of nodes.

usage: evalsource.py EXE FEN DEPTH
"""
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]

CONFIGS = [
    ("default (net residual)", []),
    ("UseNNUE false", [("UseNNUE", "false")]),
    ("DeadMaterial true", [("DeadMaterial", "true")]),
    ("NonPawnCorrection false", [("NonPawnCorrection", "false")]),
    ("MaterialCorrectionWeight 0", [("MaterialCorrectionWeight", "0")]),
    ("EvalRule50Damp true", [("EvalRule50Damp", "true")]),
    ("DrawJitter 0", [("DrawJitter", "0")]),
]


class E:
    def __init__(self, exe, opts):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.w("uci")
        while self.r().strip() != "uciok":
            pass
        for n, v in [("Threads", "1"), ("Hash", "16")] + S14 + opts:
            self.w("setoption name %s value %s" % (n, v))
            self.w("isready")
            self.ready()

    def w(self, c):
        self.p.stdin.write(c + "\n")
        self.p.stdin.flush()

    def r(self):
        line = self.p.stdout.readline()
        if line == "":
            raise RuntimeError("died")
        return line

    def ready(self):
        while True:
            line = self.r().strip()
            if any(m in line for m in ("unknown option", "invalid value")):
                raise RuntimeError(line)
            if line == "readyok":
                return

    def go(self, fen, d):
        self.w("ucinewgame")
        self.w("isready")
        self.ready()
        self.w("position fen " + fen)
        self.w("isready")
        self.ready()
        self.w("go depth %d" % d)
        pv = None
        while True:
            line = self.r().strip()
            if " pv " in line:
                pv = line
            if line.startswith("bestmove"):
                bm = line.split()[1]
                break
        t = pv.split()
        return (bm, t[t.index("score") + 1] + " " + t[t.index("score") + 2],
                int(t[t.index("nodes") + 1]))


def mir(u):
    return (chess.square_name(chess.parse_square(u[0:2]) ^ 56) +
            chess.square_name(chess.parse_square(u[2:4]) ^ 56) + (u[4:] or ""))


def main():
    exe, fen, depth = sys.argv[1], sys.argv[2], int(sys.argv[3])
    mfen = chess.Board(fen).mirror().fen()
    print("fen   : " + fen)
    print("mirror: " + mfen)
    print("depth %d" % depth)
    print("| config | W bm/score/nodes | B bm/score/nodes | bm mirrors | score equal | nodes equal |")
    print("|---|---|---|---|---|---|")
    for name, opts in CONFIGS:
        ea, eb = E(exe, opts), E(exe, opts)
        a = ea.go(fen, depth)
        b = eb.go(mfen, depth)
        ea.p.kill()
        eb.p.kill()
        print("| %s | %s/%s/%d | %s/%s/%d | %s | %s | %s |" %
              (name, a[0], a[1], a[2], b[0], b[1], b[2],
               b[0] == mir(a[0]), a[1] == b[1], a[2] == b[2]))


if __name__ == "__main__":
    main()
