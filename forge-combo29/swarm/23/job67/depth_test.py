#!/usr/bin/env python3
"""job67b : is the PC's ROOT_DRAWN repair depth-dependent? Base vs PC at depths 4, 10, 20 on VALIDATED threefolds."""
import re, subprocess, os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'job59'))
import chess
from validate import check_fixture

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
EVAL = re.compile(r"info string eval .*?\btotal (-?\d+)")
BASE = os.path.expanduser("~/build/forge")
PC = os.path.expanduser("~/pcbuild/forge")
HERE = os.path.dirname(os.path.abspath(__file__))
boards = json.load(open(os.path.join(HERE, "boards.json")))


def conn(exe):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    o = set()
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died")
        s = l.strip()
        if s.startswith("option name "):
            o.add(s.split("option name ")[1].split(" type ")[0])
        if s == "uciok":
            break
    if "OwnBook" in o:
        p.stdin.write("setoption name OwnBook value false\n"); p.stdin.flush()
    p.stdin.write("setoption name Threads value 1\nsetoption name Hash value 16\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    return p


def go(p, fen, moves, depth):
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen %s moves %s\n" % (fen, " ".join(moves))); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("go depth %d\n" % depth); p.stdin.flush()
    last = None
    nlines = 0
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died in search")
        s = l.strip()
        m = INFO.match(s)
        if m:
            last = (m.group(2), int(m.group(3)), int(m.group(4)))
            nlines += 1
        if s.startswith("bestmove"):
            return last, s.split()[1], nlines


pb = conn(BASE); pp = conn(PC)
print("| board | build | d4 | d10 | d20 | info lines at d10 |")
print("|---|---|---|---|---|---|")
for fen, moves in boards:
    ok, msg = check_fixture(fen, moves, expect=3)
    assert ok, (fen, msg)
    for name, p in (("base", pb), ("PC", pp)):
        cells = []
        nl = None
        for d in (4, 10, 20):
            (k, v, n), bm, lines = go(p, fen, moves, d)
            cells.append("%s %d / %d nodes" % (k, v, n))
            if d == 10:
                nl = lines
        print("| `%s` | %s | %s | %s | %s | %d |" % (fen, name, cells[0], cells[1], cells[2], nl))
pb.stdin.write("quit\n"); pb.stdin.flush()
pp.stdin.write("quit\n"); pp.stdin.flush()
