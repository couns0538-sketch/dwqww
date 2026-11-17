#!/usr/bin/env python3
"""job68g : the BAIL under a NODE budget — `go nodes N`, the third budget type.

23-F168 showed the base's bail is identical under `go depth` and under `go movetime` / `go wtime`, returning
immediately with 0 nodes. Node budgets are the third kind and are the interesting one, because a node budget is the
budget the bail itself consumes none of: `go nodes 1000` on a drawn root should either bail instantly or spend the
whole budget, and which one it does says whether the guard precedes the node accounting.
"""
import re, subprocess, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job59"))
from validate import check_fixture
import chess

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")
PC = os.path.expanduser("~/pcbuild/forge")
FEN = "1K6/8/8/3R4/8/8/8/k7 w - - 0 1"
CYC = "b8c8 a1b2 c8b8 b2a1".split() * 2


def conn(exe):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    while True:
        l = p.stdout.readline()
        if l.strip() == "uciok":
            break
    p.stdin.write("setoption name OwnBook value false\n"); p.stdin.flush()
    p.stdin.write("setoption name Threads value 1\nsetoption name Hash value 16\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    return p


def go(p, fen, moves, cmd):
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen %s%s\n" % (fen, (" moves " + " ".join(moves)) if moves else "")); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write(cmd + "\n"); p.stdin.flush()
    n = 0; last = None; pvlen = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died")
        s = l.strip()
        m = INFO.match(s)
        if m:
            n += 1
            last = (m.group(2), int(m.group(3)), int(m.group(4)))
            tail = s[s.find(" pv ") + 4:] if " pv " in s else ""
            pvlen = len(tail.split())
        if s.startswith("bestmove"):
            return n, last, pvlen, s.split()[1]


ok, msg = check_fixture(FEN, CYC, expect=3)
print("fixture:", "PASS" if ok else "REJECTED", "|", msg)
print()
print("| build | root | budget | info lines | nodes | score | pv | bestmove |")
print("|---|---|---|---|---|---|---|---|")
for name, exe in (("base", BASE), ("PC", PC)):
    p = conn(exe)
    for label, moves in (("drawn", CYC), ("bare (searches)", None)):
        for cmd in ("go nodes 1000", "go nodes 100000", "go depth 10"):
            n, last, pvlen, bm = go(p, FEN, moves, cmd)
            print("| %s | %s | `%s` | %d | %d | %s %d | %s | %s |" % (
                name, label, cmd, n, last[2], last[0], last[1], pvlen, bm))
    p.stdin.write("quit\n"); p.stdin.flush()
