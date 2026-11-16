#!/usr/bin/env python3
"""probe_no_clock.py EXE — what does the engine answer when the clock is at or below Move Overhead?
For 8 positions: run `go wtime 1 btime 1`, record the bestmove and the full output, and compare it with
  (a) the first legal move in python-chess order,
  (b) the answer to `go depth 1`,
  (c) the answer to `go movetime 100` (a real search).
If the no-clock answer equals the depth-1 answer everywhere, the reserve-empty branch still runs a depth-1
search; if it equals the first legal move, it is a move-list answer.
"""
import subprocess
import sys

import chess

exe = sys.argv[1]
fens = [l.strip() for l in open("probe_fens.txt") if l.strip()]

p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)


def send(s):
    p.stdin.write(s + "\n")
    p.stdin.flush()


def sync():
    send("isready")
    lines = []
    while True:
        l = p.stdout.readline().rstrip("\n")
        if l == "":
            raise EOFError
        lines.append(l)
        if l.startswith("readyok"):
            return lines


send("uci")
while not p.stdout.readline().startswith("uciok"):
    pass
sync()


def ask(fen, go):
    send("ucinewgame")
    sync()
    send("position fen " + fen)
    sync()
    send(go)
    lines = []
    while True:
        l = p.stdout.readline().rstrip("\n")
        lines.append(l)
        if l.startswith("bestmove"):
            break
    sync()
    bm = lines[-1].split()[1]
    ev = [x for x in lines if x.startswith("info") and " score " in x]
    return bm, len(ev), ev[-1] if ev else ""


print("| fen | no clock (wtime 1) | first legal | depth 1 | movetime 100 | info lines at wtime 1 |")
print("|---|---|---|---|---|---|")
same_as_depth1 = 0
same_as_first = 0
for fen in fens:
    b = chess.Board(fen)
    first = b.uci(list(b.legal_moves)[0])
    nc, nlines, _ = ask(fen, "go wtime 1 btime 1")
    d1, _, _ = ask(fen, "go depth 1")
    mt, _, _ = ask(fen, "go movetime 100")
    same_as_depth1 += (nc == d1)
    same_as_first += (nc == first)
    print("| %s | %s | %s | %s | %s | %d |" % (fen, nc, first, d1, mt, nlines))
send("quit")
p.wait(timeout=10)
print()
print("no-clock answer equals depth-1 answer: %d of %d" % (same_as_depth1, len(fens)))
print("no-clock answer equals first legal move: %d of %d" % (same_as_first, len(fens)))
