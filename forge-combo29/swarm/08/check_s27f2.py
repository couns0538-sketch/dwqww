#!/usr/bin/env python3
"""check_s27f2.py EXE OUT — my own check of seat 27's S-F2, written from its sentence alone:

"`go nodes N` below one root iteration (N < 26 at startpos) answers the first legal move in generation order
 (a2a3) with no info line at all; N = 26 answers d2d4."

Design note (a bug I fixed in my own first attempt): the `quit` must NOT be sent with the `go` line. A long
lived engine process is used and it is waited on until `bestmove`, otherwise the engine reads `quit` and never
searches, which makes every answer look unsearched.

Controls:
 (1) N = 1 measured twice in two fresh processes must agree;
 (2) `go nodes 700000` must print info lines and a move that is not a2a3, proving the harness sees a search;
 (3) `go depth 1` is recorded too, since a 1-ply search is what a tiny node budget is likely to resemble.
"""
import subprocess
import sys

import chess

exe, outpath = sys.argv[1:3]
START = chess.STARTING_FEN
OTHER = "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"

lines = []


def emit(s):
    lines.append(s)
    print(s)


class Eng:
    def __init__(self):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  text=True, bufsize=1)
        self.send("uci")
        while not self.p.stdout.readline().startswith("uciok"):
            pass
        self.send("setoption name Threads value 1")
        self.sync()
        self.send("setoption name Hash value 16")
        self.sync()

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def sync(self):
        self.send("isready")
        out = []
        while True:
            l = self.p.stdout.readline().rstrip("\n")
            if not l:
                raise EOFError
            out.append(l)
            if l.startswith("readyok"):
                return out

    def search(self, fen, go, timeout=180.0):
        self.send("ucinewgame")
        self.sync()
        self.send("position fen " + fen)
        self.sync()
        self.send(go)
        out = []
        while True:
            l = self.p.stdout.readline().rstrip("\n")
            if not l:
                raise EOFError
            out.append(l)
            if l.startswith("bestmove"):
                break
        self.sync()
        infos = [l for l in out if l.startswith("info depth")]
        bm = out[-1].split()[1]
        return bm, len(infos), (infos[-1] if infos else "")

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=5)
        except Exception:
            self.p.kill()


emit("## control 1: N = 1 in two separate fresh processes (must agree)")
a = Eng()
r1 = a.search(START, "go nodes 1")
a.close()
b = Eng()
r2 = b.search(START, "go nodes 1")
b.close()
emit("| run | bestmove | info lines |")
emit("|---|---|---|")
emit("| first | %s | %d |" % (r1[0], r1[1]))
emit("| second | %s | %d |" % (r2[0], r2[1]))
emit("| identical | %s | |" % (r1[0] == r2[0] and r1[1] == r2[1]))

e = Eng()
emit("")
emit("## control 2: a real budget must search and print info")
big = e.search(START, "go nodes 700000")
d1 = e.search(START, "go depth 1")
emit("| go | bestmove | info lines | last info (truncated) |")
emit("|---|---|---|---|")
emit("| go nodes 700000 | %s | %d | %s |" % (big[0], big[1], big[2][:100].replace("|", "/")))
emit("| go depth 1 | %s | %d | %s |" % (d1[0], d1[1], d1[2][:100].replace("|", "/")))

emit("")
emit("## the sweep at startpos, one fresh process per N is NOT needed: same process, ucinewgame between")
emit("(the table is cleared by ucinewgame, so each N starts from an empty table)")
emit("")
emit("| N | bestmove | info lines |")
emit("|---|---|---|")
rows = []
for n in list(range(1, 41)) + [50, 60, 100, 1000]:
    bm, ni, _ = e.search(START, "go nodes %d" % n)
    rows.append((n, bm, ni))
    emit("| %d | %s | %d |" % (n, bm, ni))
e.close()

first_non_a2a3 = next((n for n, bm, ni in rows if bm != "a2a3"), None)
first_with_info = next((n for n, bm, ni in rows if ni > 0), None)
first_d2d4 = next((n for n, bm, ni in rows if bm == "d2d4"), None)
emit("")
emit("| quantity | value |")
emit("|---|---|")
emit("| largest N still answering a2a3 with no info | %s |" %
     (max((n for n, bm, ni in rows if bm == "a2a3" and ni == 0), default=None)))
emit("| smallest N whose answer is not a2a3 | %s |" % first_non_a2a3)
emit("| smallest N printing any info line | %s |" % first_with_info)
emit("| smallest N answering d2d4 | %s |" % first_d2d4)

emit("")
emit("## the same sweep on a non-startpos position, to see if the threshold is startpos-specific")
e2 = Eng()
emit("| N | bestmove | info lines |")
emit("|---|---|---|")
for n in [1, 5, 10, 20, 26, 30, 40, 60]:
    bm, ni, _ = e2.search(OTHER, "go nodes %d" % n)
    emit("| %d | %s | %d |" % (n, bm, ni))
e2.close()
emit("")
emit("(engine-generation order in this position is not a2a3-shaped; the point is whether a tiny budget")
emit(" prints info and whether the answer changes with N)")

with open(outpath, "w") as fh:
    fh.write("\n".join(lines) + "\n")
