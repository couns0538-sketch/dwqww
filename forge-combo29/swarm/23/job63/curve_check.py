#!/usr/bin/env python3
"""job63h : re-verify the eval/go gap CURVE table in GUI_HAZARDS.md (counters 40..100, depth 10)."""
import re, subprocess, os
INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
EVAL = re.compile(r"info string eval .*?\btotal (-?\d+)")
BASE = os.path.expanduser("~/build/forge")
FEN = "1K6/8/8/3R4/8/8/8/k7 w - - %d 60"


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


def ev(p, fen):
    p.stdin.write("position fen " + fen + "\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("eval\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    v = None
    while True:
        s = p.stdout.readline().strip()
        m = EVAL.search(s)
        if m:
            v = int(m.group(1))
        if s == "readyok":
            return v


def go(p, fen, depth=10):
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen " + fen + "\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("go depth %d\n" % depth); p.stdin.flush()
    last = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died")
        s = l.strip()
        m = INFO.match(s)
        if m:
            last = (m.group(2), int(m.group(3)), int(m.group(4)))
        if s.startswith("bestmove"):
            return last


CLAIM = {40: 25, 60: 25, 80: 32, 88: 45, 90: 135, 92: 406, 95: 406, 99: 406, 100: 406}
p = conn()
print("| counter | eval | go depth 10 | gap | GUI page claims |")
print("|---|---|---|---|---|")
bad = 0
for c in (40, 60, 80, 88, 90, 92, 95, 99, 100):
    fen = FEN % c
    e = ev(p, fen)
    (k, v, n) = go(p, fen, 10)
    gap = (e - v) if k == "cp" else "mate"
    ok = (gap == CLAIM[c])
    if not ok:
        bad += 1
    print("| %d | %s | %s %d | %s | %d %s |" % (c, e, k, v, gap, CLAIM[c], "" if ok else "**MISMATCH**"))
p.stdin.write("quit\n"); p.stdin.flush()
print()
print("rows matching the GUI page: %d of %d" % (9 - bad, 9))
