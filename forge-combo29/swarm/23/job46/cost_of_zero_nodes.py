#!/usr/bin/env python3
"""job46 : does the base's 0-node move on a threefold root COST anything, or does it still win?

Fixture W-3 (validated in job45): 1K6/8/8/3R4/8/8/8/k7 w, moves d5d6 a1b1 d6d5 b1a1 d5d6 a1b1 d6d5 b1a1 -> root occurs
3 times, white to move, white is winning.

Step 1: ask the BASE for its move on the threefold root (expect d5d1 at 0 nodes) and the PC for its move (expect d5b5).
Step 2: push each move with PYTHON-CHESS (independent of the engine), then ask the PC at depth 16 for white's score in
the resulting position. The question is whether both moves still win.

Controls: python-chess must confirm both moves are legal from the root, and the twin (no moves) must show white
winning, so a "still winning" verdict cannot come from a board that is winning anyway because I mis-built it.
"""
import re, subprocess, sys, os
import chess

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")
PC = os.path.expanduser("~/pcbuild/forge")
FEN = "1K6/8/8/3R4/8/8/8/k7 w - - 0 1"
MOVES = "d5d6 a1b1 d6d5 b1a1 d5d6 a1b1 d6d5 b1a1"


def proc(exe):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    opts = set()
    p.stdin.write("uci\n"); p.stdin.flush()
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died")
        s = l.strip()
        if s.startswith("option name "):
            opts.add(s.split("option name ")[1].split(" type ")[0])
        if s == "uciok":
            break
    if "OwnBook" in opts:
        p.stdin.write("setoption name OwnBook value false\n"); p.stdin.flush()
    p.stdin.write("setoption name Threads value 1\n")
    p.stdin.write("setoption name Hash value 16\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    return p


def go(p, fen, moves, depth):
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen %s%s\n" % (fen, (" moves " + moves) if moves else "")); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("go depth %d\n" % depth); p.stdin.flush()
    last = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died in search")
        s = l.strip()
        m = INFO.match(s)
        if m:
            last = (m.group(2), int(m.group(3)), int(m.group(4)))
        if s.startswith("bestmove"):
            return last, s.split()[1]


print("== step 1: each build's move on the threefold root ==")
picks = {}
for name, exe in (("base", BASE), ("PC", PC)):
    p = proc(exe)
    (score, val, nodes), bm = go(p, FEN, MOVES, 12)
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    picks[name] = (bm, score, val, nodes)
    print("  %-5s score %s %d | nodes %d | bestmove %s" % (name, score, val, nodes, bm))

print()
print("== control: are both moves legal from the root, per python-chess? ==")
root = chess.Board(FEN)
for name, (bm, *_rest) in picks.items():
    m = chess.Move.from_uci(bm)
    print("  %-5s %s legal: %s" % (name, bm, m in root.legal_moves))

print()
print("== control: is the root itself winning for white, per the PC at depth 16? ==")
p = proc(PC)
(score, val, nodes), bm = go(p, FEN, MOVES, 16)
print("  PC on the threefold root at depth 16: %s %d (%d nodes)" % (score, val, nodes))
p.stdin.write("quit\n"); p.stdin.flush()
try:
    p.wait(timeout=10)
except Exception:
    p.kill()

print()
print("== step 2: score for white AFTER each chosen move (PC at depth 16, board from python-chess) ==")
for name, (bm, *_rest) in picks.items():
    after = chess.Board(FEN)
    for mv in MOVES.split():
        after.push(chess.Move.from_uci(mv))
    assert chess.Move.from_uci(bm) in after.legal_moves, ("illegal after prefix", bm)
    after.push(chess.Move.from_uci(bm))
    fen_after = after.fen()
    p = proc(PC)
    (score, val, nodes), reply = go(p, fen_after, None, 16)
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    print("  after %s (%s): %s %d | %d nodes | board %s" % (name, bm, score, val, nodes, fen_after))
    print("      (a mate score or cp > 100 for white means the move STILL WINS)")
