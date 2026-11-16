#!/usr/bin/env python3
"""Verify the mate-score sign convention: in a LOST position, is a LONGER mate a HIGHER score?

Test: KR vs K, white to move, white is lost. Give the engine a position where it can be mated
sooner or later and see which move it picks and what it reports. Simpler and decisive: ask the
engine to score two positions, one mate-in-2 against white and one mate-in-4 against white, and see
which score is numerically higher (i.e. which the engine prefers for the losing side).
"""
import subprocess

def score(exe, fen, depth=12):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    def w(c): p.stdin.write(c+"\n"); p.stdin.flush()
    def r():
        l = p.stdout.readline()
        if l == "": raise RuntimeError("died")
        return l
    def rd():
        while True:
            if r().strip() == "readyok": return
    w("uci")
    while r().strip() != "uciok": pass
    w("setoption name Threads value 1"); w("isready"); rd()
    w("setoption name Hash value 16"); w("isready"); rd()
    w("setoption name OwnBook value false"); w("isready"); rd()
    w("ucinewgame"); w("isready"); rd()
    w("position fen "+fen); w("isready"); rd()
    w("go depth %d" % depth)
    last = None; bm = None
    while True:
        l = r().strip()
        if " pv " in l and l.startswith("info"): last = l.split()
        if l.startswith("bestmove"): bm = l.split()[1]; break
    p.kill()
    return last[last.index("score")+1], int(last[last.index("score")+2]), bm

exe = "/home/ubuntu/bld/release/forge"
# White (to move) is lost in both. Position A: black mates very soon. Position B: black needs longer.
# Use simple king+rook mates: white lone king in the corner, black K+R.
cases = [
 ("black rook already cutting, white in corner - fast mate", "7k/8/8/8/8/8/5q2/7K w - - 0 1"),
 ("black queen far away - slower mate",                      "7k/8/8/8/8/8/8/q6K w - - 0 1"),
]
print("| position | score kind | value | engine's move |")
print("|---|---|---|---|")
for label, fen in cases:
    k, v, bm = score(exe, fen)
    print("| %s | %s | %d | %s |" % (label, k, v, bm))

print()
print("DIRECT test: which does the engine PREFER when it can choose between a shorter and a longer mate")
print("against itself? White to move, white lost, two moves giving different mate distances.")
# White king h1, black queen g3 (mate threats). Let the engine choose.
fen = "8/8/8/8/8/6q1/8/7K w - - 0 1"
k, v, bm = score(exe, fen, 14)
print("  %s -> %s %d, plays %s" % (fen, k, v, bm))
