#!/usr/bin/env python3
"""job63g : re-verify the eval/go GAP table in GUI_HAZARDS.md (threefold / fifty-move / insufficient material)."""
import re, subprocess, os, sys
sys.path.insert(0, '../job59')
import chess
from validate import check_fixture

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
EVAL = re.compile(r"info string eval .*?\btotal (-?\d+)")
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


CASES = [
    ("threefold repetition", "1K6/8/8/3R4/8/8/8/k7 w - - 0 1", "b8c8 a1b2 c8b8 b2a1".split() * 2, "406 / cp 0 / 406"),
    ("fifty-move rule", "1K6/8/8/3R4/8/8/8/k7 w - - 150 1", None, "406 / cp 0 / 406"),
    ("insufficient material", "8/8/8/8/8/8/8/K6k w - - 0 1", None, "20 / cp 0 / 20"),
]
p = conn()
print("| draw type | eval | go depth 12 | gap | GUI_HAZARDS claims |")
print("|---|---|---|---|---|")
for label, fen, moves, claim in CASES:
    if moves:
        ok, msg = check_fixture(fen, moves, expect=3)
        if not ok:
            print("| %s | **fixture REJECTED: %s** | - | - | %s |" % (label, msg, claim))
            continue
    ev = evaltot(p, fen, moves)
    (k, v, n), bm = go(p, fen, moves, 12)
    gap = (ev - v) if k == "cp" else None
    print("| %s | %s | %s %d / %d nodes | %s | %s |" % (label, ev, k, v, n, gap if gap is not None else "-", claim))
p.stdin.write("quit\n"); p.stdin.flush()
