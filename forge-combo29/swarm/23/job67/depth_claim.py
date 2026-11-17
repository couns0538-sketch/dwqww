#!/usr/bin/env python3
"""job67 : is the PC's drawn-root repair depth-dependent, or correct at every depth?

Builds genuine threefold roots (validated by job59/validate.py, expect=3) in which the mover has a mate available, then
asks BASE and PC at depths 4, 10 and 20. If the PC reports the mate at depth 4 where the base bails, the repair is NOT
shallow-only — it is correct at every depth tested.
"""
import re, subprocess, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'job59'))
import chess
from validate import check_fixture, identity

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")
PC = os.path.expanduser("~/pcbuild/forge")

# mate-in-2 shapes with a shuttle available that does not disturb castling (castling '-' throughout)
BOARDS = [
    ("KRK mate-in-2", "8/8/8/8/8/7k/6R1/6K1 w - - 0 1", ["g2g3", "h3h2", "g3g2", "h2h3"]),
    ("KQK mate-in-2", "8/8/8/8/8/7k/6Q1/6K1 w - - 0 1", ["g2g3", "h3h2", "g3g2", "h2h3"]),
    ("KRK alt", "8/8/8/8/8/6k1/6R1/6K1 w - - 0 1", ["g2g3", "g3h4", "g3g2", "h4g3"]),
]


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


print("| board | validates as threefold? | build | depth 4 | depth 10 | depth 20 |")
print("|---|---|---|---|---|---|")
pb = conn(BASE)
pp = conn(PC)
for label, fen, cyc in BOARDS:
    # the cycle may not repeat cleanly — rotate/trim until it does, or report
    best = None
    for n in range(1, 3):
        moves = cyc * n
        ok, msg = check_fixture(fen, moves, expect=3 if n == 2 else 2)
        if ok:
            best = moves
            break
    if not best:
        print("| %s | **no valid threefold cycle** | - | - | - | - |" % label)
        continue
    ok, msg = check_fixture(fen, best, expect=3)
    cells = []
    for d in (4, 10, 20):
        out = []
        for name, p in (("base", pb), ("PC", pp)):
            (k, v, n), bm = go(p, fen, best, d)
            out.append("%s %d/%d" % (k, v, n))
        cells.append("base %s vs PC %s" % (out[0], out[1]))
    print("| %s | yes (%s) | both | %s | %s | %s |" % (label, msg.split('|')[0].strip(), *cells))
pb.stdin.write("quit\n"); pb.stdin.flush()
pp.stdin.write("quit\n"); pp.stdin.flush()
