#!/usr/bin/env python3
"""job60 : occurrence-count monotonicity, and the seventy-five-move rule, on a revalidated fixture.

Every fixture validated with job59/validate.py (two independent counters must agree) and asserted to the exact
occurrence count BEFORE the engine is called.
"""
import re, subprocess, os, sys
sys.path.insert(0, '../job59')
import chess
from validate import check_fixture, count_occurrences

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")
FEN = "1K6/8/8/3R4/8/8/8/k7 w - - 0 1"
CYCLE = "b8c8 a1b2 c8b8 b2a1".split()


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


def go(p, fen, moves, depth=10):
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen %s%s\n" % (fen, (" moves " + " ".join(moves)) if moves else "")); p.stdin.flush()
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
print("| case | expected occ | validated | nodes | score | verdict |")
print("|---|---|---|---|---|---|")
rows = []
for n in (2, 3, 4, 5, 6):
    moves = CYCLE * (n - 1)
    ok, msg = check_fixture(FEN, moves, expect=n)
    if not ok:
        print("| occ %d | %d | **REJECTED: %s** | - | - | EXCLUDED |" % (n, n, msg))
        continue
    (k, v, nodes), bm = go(p, FEN, moves, 10)
    rows.append((n, nodes))
    print("| occ %d | %d | yes | %d | %s %d | %s |" % (n, n, nodes, k, v,
                                                       "**BAIL**" if nodes == 0 else "searched"))
    sys.stdout.flush()

print()
print("== seventy-five-move rule (no repetition; 9.6.2 is automatic, unlike the claimable fifty) ==")
for hm in (74, 75, 76):
    f = "1K6/8/8/3R4/8/8/8/k7 w - - %d 60" % hm
    (k, v, nodes), bm = go(p, f, None, 10)
    print("| halfmove %d, no moves | - | - | %d | %s %d | %s |" % (
        hm, nodes, k, v, "**BAIL**" if nodes == 0 else "searched"))
p.stdin.write("quit\n"); p.stdin.flush()
try:
    p.wait(timeout=10)
except Exception:
    p.kill()

print()
if rows:
    d = dict(rows)
    print("P1 occ 2 searches:", d.get(2, -1) > 0, "(nodes %s)" % d.get(2))
    print("P2 occ 3,4,5,6 all bail:", all(d.get(n, 1) == 0 for n in (3, 4, 5, 6)))
    print("   individual:", [(n, d.get(n)) for n in (3, 4, 5, 6)])
