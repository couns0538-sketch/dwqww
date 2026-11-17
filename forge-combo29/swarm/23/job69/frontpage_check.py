#!/usr/bin/env python3
"""frontpage_check.py : verify the three claims the FINAL's first page makes, in one run.

The FINAL leads with: (1) the bail exists and fires iff the searched position has occurred 3+ times; (2) the unsearched
move is generator index 0; (3) on a mate-in-one root that move forfeits the mate. This script checks all three on one
board so a reader can confirm the first page rather than take it on trust.
"""
import re, subprocess, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job59"))
import chess
from validate import check_fixture

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
MOVELINE = re.compile(r"^([a-h][1-8][a-h][1-8][qrbn]?): (\d+)$")
SUM = re.compile(r"^nodes (\d+)$")
BASE = os.path.expanduser("~/build/forge")
FEN = "6k1/5ppp/8/8/8/8/5PPP/1Q4K1 w - - 0 1"
CYC = "g1h1 g8h8 h1g1 h8g8".split() * 2


def conn(moves):
    p = subprocess.Popen([BASE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen %s%s\n" % (FEN, (" moves " + " ".join(moves)) if moves else "")); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    return p


def perft1(p):
    p.stdin.write("go perft 1\n"); p.stdin.flush()
    order = []
    while True:
        l = p.stdout.readline()
        s = l.strip()
        m = MOVELINE.match(s)
        if m:
            order.append(m.group(1))
        if SUM.match(s):
            return order


def search(p, depth=10):
    p.stdin.write("go depth %d\n" % depth); p.stdin.flush()
    last = None; pvlen = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died")
        s = l.strip()
        m = INFO.match(s)
        if m:
            last = (m.group(2), int(m.group(3)), int(m.group(4)))
            tail = s[s.find(" pv ") + 4:] if " pv " in s else ""
            pvlen = len(tail.split())
        if s.startswith("bestmove"):
            return last, pvlen, s.split()[1]


ok, msg = check_fixture(FEN, CYC, expect=3)
print("fixture validated:", "PASS" if ok else "**REJECTED**", "|", msg)
if not ok:
    sys.exit(2)

p = conn(CYC)
order = perft1(p)
last, pvlen, bm = search(p, 10)
p.stdin.write("quit\n"); p.stdin.flush()

b = chess.Board(FEN)
for mv in CYC:
    b.push(chess.Move.from_uci(mv))
mates = [m.uci() for m in b.legal_moves if (lambda c: (c.push(m), c.is_checkmate())[1])(b.copy())]

ok1 = last[2] == 0 and pvlen == 0
ok2 = bm == order[0]
ok3 = bool(mates) and bm not in mates
print()
print("CLAIM 1  the bail fires on a genuine threefold:      %s" % (
    "PASS" if ok1 else "**FAIL** (nodes %d, pv %s)" % (last[2], pvlen)))
print("CLAIM 2  the move played is generator index 0:       %s  (index0 %s, played %s)" % (
    "PASS" if ok2 else "**FAIL**", order[0], bm))
print("CLAIM 3  that move forfeits an available mate:       %s  (mate in 1 %s, played %s)" % (
    "PASS" if ok3 else "**FAIL**", ",".join(mates) or "none", bm))
print()
print("score reported: %s %d | info-line pv: %d plies" % (last[0], last[1], pvlen))
print()
print("If all three PASS, the FINAL's first page is verified on this board by this command.")
print()
if ok1 and ok2 and ok3:
    print("VERDICT: PASS")
    sys.exit(0)
print("VERDICT: FAIL (%d of 3 claims)" % (3 - (ok1 + ok2 + ok3)))
sys.exit(1)
