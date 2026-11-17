#!/usr/bin/env python3
"""job65b : the three-occurrence threshold at the END of a LONG list, searched position != start position."""
import re, subprocess, os, sys
sys.path.insert(0, '../job59')
import chess
from validate import identity

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")
START = "1K6/8/8/3R4/8/8/8/k7 w - - 0 1"
PRE = "d5g5 a1b2 g5a5 b2b3 a5a7 b3b2 a7a5 b2b1 b8b7 b1c2".split()
CYC = "b7c8 c2d3 c8b7 d3c2".split()


def conn():
    p = subprocess.Popen([BASE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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


def go(p, moves, depth=10):
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen %s moves %s\n" % (START, " ".join(moves))); p.stdin.flush()
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


p = conn()
print("| n | line length | searched-pos occ | searched == start? | nodes | score | verdict |")
print("|---|---|---|---|---|---|---|")
for n in (2, 3, 4, 5):
    moves = PRE + CYC * (n - 1)
    b = chess.Board(START); ids = [identity(b)]; ok = True
    for mv in moves:
        m = chess.Move.from_uci(mv)
        if m not in b.legal_moves:
            ok = False
            break
        b.push(m); ids.append(identity(b))
    if not ok:
        print("| %d | **illegal line** | - | - | - | - | EXCLUDED |" % n)
        continue
    occ = ids.count(ids[-1])
    same = ids[-1] == ids[0]
    (k, v, nodes), bm = go(p, moves, 10)
    print("| %d | %d | %d | %s | %d | %s %d | %s |" % (
        n, len(moves), occ, same, nodes, k, v, "**BAIL**" if nodes == 0 else "searched"))
p.stdin.write("quit\n"); p.stdin.flush()
