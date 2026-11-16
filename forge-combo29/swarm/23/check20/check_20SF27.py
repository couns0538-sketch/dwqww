#!/usr/bin/env python3
"""check_20SF27.py : independent check of seat 20's S-F27 (tie-break cannot be read from the protocol).

Claims: on a lone-king position with 3 legal moves, all score cp 0 and the engine returns a1b1 at depths 1-3 while
python-chess's FIRST legal move is a1b2, so `bestmove` does not reveal which move came first in the engine's list.

My method: build the KvK position myself (white Ka1, black Kh8 -> three white moves a1a2, a1b1, a1b2), search at
depth 1-3, confirm cp 0 and the returned move; list python-chess's legal moves in ITS order.

THEN I test the part that matters for other seats: is the engine's ROOT ORDER knowable at all? I probe each legal
move alone with `go searchmoves <move>` and compare, and I check whether `bestmove` changes when the position's
move list reaches 4+ (the AVX2 branch their source note mentions) by giving white a fourth legal square.
"""
import re
import subprocess
import sys

import chess

EXE = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/build/forge"
INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+)")


def search(fen, depth, moves=None):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    while True:
        l = p.stdout.readline()
        if not l or l.strip() == "uciok":
            break
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen %s\n" % fen); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    cmd = "go depth %d" % depth
    if moves:
        cmd += " searchmoves " + " ".join(moves)
    p.stdin.write(cmd + "\n"); p.stdin.flush()
    last = None
    bm = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died")
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


KVK = "8/8/8/8/8/8/8/K6k w - - 0 1"

print("position:", KVK)
b = chess.Board(KVK)
print("python-chess legal moves in ITS order:", [m.uci() for m in b.legal_moves])
print("python-chess FIRST legal move:", next(iter(b.legal_moves)).uci())
print()
print("| depth | score | bestmove | is it python-chess's first? |")
print("|---|---|---|---|")
first = next(iter(b.legal_moves)).uci()
for d in (1, 2, 3):
    sc, bm = search(KVK, d)
    print("| %d | %s %d | %s | %s |" % (d, sc[0], sc[1], bm, "yes" if bm == first else "NO"))

print()
print("Can the ROOT ORDER be recovered from the protocol at all? Each move searched ALONE at depth 3:")
print("| move | score alone |")
print("|---|---|")
for m in [x.uci() for x in b.legal_moves]:
    sc, bm = search(KVK, 3, [m])
    print("| %s | %s %d |" % (m, sc[0], sc[1]))

print()
print("The 4+ move branch: give white a fourth legal square (Kb1-style position with more space)")
KVK4 = "8/8/8/8/8/8/8/K3k3 w - - 0 1"
b4 = chess.Board(KVK4)
moves4 = [m.uci() for m in b4.legal_moves]
print("  fen:", KVK4, "->", len(moves4), "legal moves:", moves4)
sc, bm = search(KVK4, 1)
print("  engine at depth 1: %s %d, bestmove %s; python-chess first %s"
      % (sc[0], sc[1], bm, moves4[0]))
