#!/usr/bin/env python3
"""Is the symmetry break tied to the transposition table? Search with Hash 1, 16, 64 and
also with each position searched TWICE in the same process (second search reuses the TT).

usage: tt_test.py EXE FEN DEPTH
"""
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]


class E:
    def __init__(self, exe, hash_mb):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.w("uci")
        while self.r().strip() != "uciok":
            pass
        for n, v in [("Threads", "1"), ("Hash", str(hash_mb))] + S14:
            self.w("setoption name %s value %s" % (n, v)); self.w("isready"); self.ready()
        self.w("isready"); self.ready()

    def w(self, c):
        self.p.stdin.write(c + "\n"); self.p.stdin.flush()

    def r(self):
        l = self.p.stdout.readline()
        if l == "":
            raise RuntimeError("died")
        return l

    def ready(self):
        while True:
            if self.r().strip() == "readyok":
                return

    def go(self, fen, d, newgame=True):
        if newgame:
            self.w("ucinewgame"); self.w("isready"); self.ready()
        self.w("position fen " + fen); self.w("isready"); self.ready()
        self.w("go depth %d" % d)
        pv = None
        while True:
            l = self.r().strip()
            if " pv " in l:
                pv = l
            if l.startswith("bestmove"):
                bm = l.split()[1]
                break
        t = pv.split()
        return (bm, t[t.index("score") + 1], int(t[t.index("score") + 2]), int(t[t.index("nodes") + 1]))


def mir(u):
    return chess.square_name(chess.parse_square(u[0:2]) ^ 56) + chess.square_name(chess.parse_square(u[2:4]) ^ 56) + (u[4:] or "")


exe, fen, depth = sys.argv[1], sys.argv[2], int(sys.argv[3])
mfen = chess.Board(fen).mirror().fen()
print("| hash | W (bm,score,nodes) | B (bm,score,nodes) | bm mirrors? | score equal? |")
for h in (1, 16, 64, 256):
    ea, eb = E(exe, h), E(exe, h)
    a = ea.go(fen, depth)
    b = eb.go(mfen, depth)
    ea.p.kill(); eb.p.kill()
    print("| %d | %s | %s | %s | %s |" % (h, a, b, b[0] == mir(a[0]), a[1:3] == b[1:3]))
print("")
print("same process, two searches (reuse TT + history):")
for h in (16,):
    ea = E(exe, h); eb = E(exe, h)
    a1 = ea.go(fen, depth); a2 = ea.go(fen, depth, newgame=False)
    b1 = eb.go(mfen, depth); b2 = eb.go(mfen, depth, newgame=False)
    ea.p.kill(); eb.p.kill()
    print(" W run1", a1, " run2", a2)
    print(" B run1", b1, " run2", b2)
