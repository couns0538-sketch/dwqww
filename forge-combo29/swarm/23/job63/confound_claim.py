#!/usr/bin/env python3
"""job63e : test the claim I just wrote into TRIGGER.md — 'a threefold cell is the ONLY one whose zero disappears when
the move list is removed'. If false, the rebuttal needs weakening."""
import re, subprocess, os, sys
sys.path.insert(0, '../job59')
import chess
from validate import check_fixture

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")


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


CASES = [
    ("threefold (K+R v K)", "1K6/8/8/3R4/8/8/8/k7 w - - 0 1", "b8c8 a1b2 c8b8 b2a1".split() * 2,
     "b8c8 a1b2 c8b8 b2a1".split() * 2),
    ("halfmove 100", "1K6/8/8/3R4/8/8/8/k7 w - - 100 60", None, None),
    ("insufficient material", "8/8/8/8/8/8/8/K6k w - - 0 1", None, None),
]
p = conn()
print("| case | WITH history/list | WITHOUT list | zero disappears when list removed? |")
print("|---|---|---|---|")
for label, fen, withmoves, withoutmoves in CASES:
    (k1, v1, n1), _ = go(p, fen, withmoves, 10)
    # 'without' = bare FEN of the same root (no move list)
    bare = fen.split(' moves')[0]
    (k2, v2, n2), _ = go(p, bare, None, 10)
    print("| %s | %s %d / %d nodes | %s %d / %d nodes | %s |" % (
        label, k1, v1, n1, k2, v2, n2, "**YES**" if (n1 == 0 and n2 > 0) else "no"))
p.stdin.write("quit\n"); p.stdin.flush()
print()
print("If only the threefold row shows YES, the claim in TRIGGER.md stands. If any other row also shows YES,")
print("the rebuttal sentence must be weakened.")
