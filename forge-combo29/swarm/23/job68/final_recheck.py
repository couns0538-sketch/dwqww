#!/usr/bin/env python3
"""final_recheck.py : one cold pass over the numbers the FINAL will quote, all in one run, all with fixtures validated.

If any cell here disagrees with the finding it comes from, the FINAL is wrong and I want to know now.
"""
import re, subprocess, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job59"))
import chess
from validate import check_fixture

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")
PC = os.path.expanduser("~/pcbuild/forge")


def conn(exe, mpv=1):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    while True:
        l = p.stdout.readline()
        if l.strip() == "uciok":
            break
    p.stdin.write("setoption name OwnBook value false\n"); p.stdin.flush()
    p.stdin.write("setoption name MultiPV value %d\n" % mpv); p.stdin.flush()
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
    n = 0; last = None; pvlen = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died")
        s = l.strip()
        m = INFO.match(s)
        if m:
            n += 1; last = (m.group(2), int(m.group(3)), int(m.group(4)))
            tail = s[s.find(" pv ") + 4:] if " pv " in s else ""
            pvlen = len(tail.split())
        if s.startswith("bestmove"):
            return n, last, pvlen, s.split()[1]


print("COLD RECHECK of the numbers the FINAL quotes")
print()
FEN = "1K6/8/8/3R4/8/8/8/k7 w - - 0 1"
CYC = "b8c8 a1b2 c8b8 b2a1".split() * 2
ok, msg = check_fixture(FEN, CYC, expect=3)
print("fixture (threefold root):", "PASS" if ok else "**REJECTED**", "|", msg)
p = conn(BASE)
print()
_agree = [0]
_total = [0]
def row(fmt, ok, *args):
    """Print one evidence row and COUNT whether it agreed. A row that prints **NO**
    must be able to fail the script (23-F199/F226). The fmt's trailing %s is the
    agree-cell, supplied here so no row can print its verdict independently of the tally."""
    _total[0] += 1
    if ok: _agree[0] += 1
    print(fmt % (args + ("yes" if ok else "**NO**",)))

print("| claim | expected | measured | agree? |")
print("|---|---|---|---|")

# 1. threshold: 2 occurrences searches, 3 bails
n2, l2, pv2, _ = go(p, FEN, "b8c8 a1b2 c8b8 b2a1".split(), 10)
n3, l3, pv3, bm3 = go(p, FEN, CYC, 10)
row("| 2 occ searches | nodes > 0 | %d | %s |", l2[2] > 0, l2[2])
row("| 3 occ bails | nodes 0 | %d | %s |", l3[2] == 0, l3[2])

# 2. info lines = depth, pv empty on bail
row("| bail emits 10 info lines | 10 | %d | %s |", n3 == 10, n3)
row("| bail pv empty | 0 | %s | %s |", pv3 == 0, pv3)
row("| search pv non-empty | > 0 | %s | %s |", pv2 > 0, pv2)

# 3. halfmove 100 bails, 99 searches
n99, l99, _, _ = go(p, "1K6/8/8/3R4/8/8/8/k7 w - - 99 60", None, 10)
n100, l100, _, _ = go(p, "1K6/8/8/3R4/8/8/8/k7 w - - 100 60", None, 10)
row("| halfmove 99 searches | nodes > 0 | %d | %s |", l99[2] > 0, l99[2])
row("| halfmove 100 bails | nodes 0 | %d | %s |", l100[2] == 0, l100[2])

# 4. insufficient material bails (automatic)
n_im, l_im, pv_im, bm_im = go(p, "8/8/8/8/8/8/8/K6k w - - 0 1", None, 10)
row("| bare kings bails | nodes 0 | %d | %s |", l_im[2] == 0, l_im[2])
p.stdin.write("quit\n"); p.stdin.flush()

# 5. MultiPV 3 on the bail: still 10 lines
p3 = conn(BASE, 3)
n_m, l_m, pv_m, bm_m = go(p3, FEN, CYC, 10)
row("| bail at MultiPV 3 still 10 lines | 10 | %d | %s |", n_m == 10, n_m)
p3.stdin.write("quit\n"); p3.stdin.flush()

# 6. PC searches where base bails (the repair)
pp = conn(PC)
n_pc, l_pc, pv_pc, bm_pc = go(pp, FEN, CYC, 10)
row("| PC searches on the drawn root | nodes > 0 | %d | %s |", l_pc[2] > 0, l_pc[2])
pp.stdin.write("quit\n"); pp.stdin.flush()

# 7. perft anchor
def perft(exe, d):
    q = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q.stdin.write("uci\n"); q.stdin.flush()
    while True:
        l = q.stdout.readline()
        if l.strip() == "uciok": break
    q.stdin.write("position fen %s\n" % chess.STARTING_FEN); q.stdin.flush()
    q.stdin.write("go perft %d\n" % d); q.stdin.flush()
    while True:
        l = q.stdout.readline()
        if not l: break
        m = re.match(r"^nodes (\d+)$", l.strip())
        if m:
            q.stdin.write("quit\n"); q.stdin.flush()
            return int(m.group(1))
row("| perft 5 anchor | 4,865,609 | %d | %s |", perft(BASE, 5) == 4865609, perft(BASE, 5))
print()
print("rows agreeing: %d of %d" % (_agree[0], _total[0]))
if _agree[0] == _total[0] and _total[0] > 0:
    print("VERDICT: PASS")
    sys.exit(0)
print("VERDICT: FAIL (%d of %d disagreed)" % (_total[0] - _agree[0], _total[0]))
sys.exit(1)
