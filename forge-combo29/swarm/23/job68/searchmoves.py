#!/usr/bin/env python3
"""job68 : does searchmoves filter root_candidates BEFORE the bail, so the bail publishes the restricted head?"""
import re, subprocess, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job59"))
import chess
from validate import check_fixture

INFO = re.compile(r"^info depth (\d+)")
MOVELINE = re.compile(r"^([a-h][1-8][a-h][1-8][qrbn]?): (\d+)$")
SUM = re.compile(r"^nodes (\d+)$")
BASE = os.path.expanduser("~/build/forge")
FEN = "1K6/8/8/3R4/8/8/8/k7 w - - 0 1"
CYC = "b8c8 a1b2 c8b8 b2a1".split() * 2


def conn():
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
    return p


def divide(p):
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen %s moves %s\n" % (FEN, " ".join(CYC))); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("go perft 1\n"); p.stdin.flush()
    order = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died")
        s = l.strip()
        m = MOVELINE.match(s)
        if m:
            order.append(m.group(1))
        if SUM.match(s):
            return order


def go(p, sm):
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen %s moves %s\n" % (FEN, " ".join(CYC))); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("go depth 10" + ((" searchmoves " + sm) if sm else "") + "\n"); p.stdin.flush()
    n = 0
    strings = []
    nodes = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died in search")
        s = l.strip()
        if s.startswith("info depth"):
            n += 1
            m = re.search(r"nodes (\d+)", s)
            if m:
                nodes = int(m.group(1))
        if s.startswith("info string"):
            strings.append(s)
        if s.startswith("bestmove"):
            return n, nodes, s.split()[1], strings


ok, msg = check_fixture(FEN, CYC, expect=3)
print("fixture:", "PASS" if ok else "REJECTED", "|", msg)
p = conn()
order = divide(p)
print("generator order (first 6):", order[:6])
print()
print("| case | restriction | info lines | last nodes | bestmove | inside restriction? |")
print("|---|---|---|---|---|---|")
cases = [("U", None), ("R1", "d5d8"), ("R2", "b8a8 d5d8"), ("R3", "e2e4")]
res = {}
for label, sm in cases:
    n, nodes, bm, strings = go(p, sm)
    allowed = sm.split() if sm else None
    inside = (bm in allowed) if allowed else "n/a"
    res[label] = bm
    print("| %s | %s | %d | %s | %s | %s |" % (label, sm or "(none)", n, nodes, bm, inside))
    if strings:
        print("      info strings: %s" % strings)
p.stdin.write("quit\n"); p.stdin.flush()
print()
print("P1 U publishes generator head:", res.get("U") == order[0], "| U =", res.get("U"), "head =", order[0])
print("P2 R1 publishes d5d8:", res.get("R1") == "d5d8", "| R1 =", res.get("R1"))
first_of_r2 = min(["b8a8", "d5d8"], key=lambda m: order.index(m) if m in order else 999)
print("P3 R2 publishes the earlier of b8a8/d5d8 in generator order (%s):" % first_of_r2, res.get("R2") == first_of_r2, "| R2 =", res.get("R2"))
print("P4 R3 (illegal restriction) reported, not predicted: bestmove =", res.get("R3"))
