#!/usr/bin/env python3
"""job68c : does the bail behave the same under CLOCK and MOVETIME budgets, not just `go depth`?

Every drawn-root measurement in this seat used `go depth`. A real front end sends a clock. If the bail behaves differently
there, the family's practical statement is incomplete.
"""
import re, subprocess, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job59"))
from validate import check_fixture

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
    t0 = time.monotonic()
    p.stdin.write(cmd + "\n"); p.stdin.flush()
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
            return n, last, pvlen, s.split()[1], (time.monotonic() - t0) * 1000


ok, msg = check_fixture(FEN, CYC, expect=3)
print("fixture:", "PASS" if ok else "REJECTED", "|", msg)
print()
print("| build | case | budget | info lines | nodes | score | pv plies | bestmove | elapsed ms |")
print("|---|---|---|---|---|---|---|---|---|")
for name, exe in (("base", BASE), ("PC", PC)):
    p = conn(exe)
    for label, moves, cmd in (
        ("drawn root", CYC, "go depth 10"),
        ("drawn root", CYC, "go movetime 1000"),
        ("drawn root", CYC, "go wtime 6000 btime 6000"),
        ("bare (searches)", None, "go movetime 1000"),
        ("bare (searches)", None, "go wtime 6000 btime 6000"),
    ):
        n, last, pvlen, bm, ms = go(p, FEN, moves, cmd)
        print("| %s | %s | `%s` | %d | %d | %s %d | %s | %s | %.0f |" % (
            name, label, cmd, n, last[2], last[0], last[1], pvlen, bm, ms))
    p.stdin.write("quit\n"); p.stdin.flush()
