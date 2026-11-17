#!/usr/bin/env python3
"""job63f : re-verify the eval/go table in GUI_HAZARDS.md, which was written under the flawed fixture key.

The table claims eval +406 vs go cp 0 on a threefold root, and PC cp 507 / 44,269 nodes. If any of those came from a
fixture whose cycle disturbed castling, the row is about a non-threefold.
"""
import re, subprocess, os, sys
sys.path.insert(0, '../job59')
import chess
from validate import check_fixture

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
EVAL = re.compile(r"info string eval .*?\btotal (-?\d+)")
BASE = os.path.expanduser("~/build/forge")
PC = os.path.expanduser("~/pcbuild/forge")
FEN = "1K6/8/8/3R4/8/8/8/k7 w - - 0 1"
CYC = "b8c8 a1b2 c8b8 b2a1".split() * 2


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


def evaltot(p, fen, moves):
    p.stdin.write("position fen %s%s\n" % (fen, (" moves " + " ".join(moves)) if moves else "")); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("eval\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    val = None
    while True:
        s = p.stdout.readline().strip()
        m = EVAL.search(s)
        if m:
            val = int(m.group(1))
        if s == "readyok":
            return val


def go(p, fen, moves, depth=12):
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


ok, msg = check_fixture(FEN, CYC, expect=3)
print("fixture used for the GUI table: threefold root on K+R v K")
print("validator:", "PASS" if ok else "**REJECTED**", "|", msg)
print()
print("| build | eval total | go depth 12 | matches GUI_HAZARDS table? |")
print("|---|---|---|---|")
for name, exe, claim in (("base", BASE, "+406 vs cp 0, 0 nodes"), ("PC r15", PC, "+406 vs cp 507, 44,269 nodes")):
    p = conn(exe)
    ev = evaltot(p, FEN, CYC)
    (k, v, n), bm = go(p, FEN, CYC, 12)
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    print("| %s | %s | %s %d / %d nodes | claimed: %s |" % (name, ev, k, v, n, claim))
