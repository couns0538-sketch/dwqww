#!/usr/bin/env python3
"""job44 : on a threefold ROOT, does either build give the right answer for the LOSING side?

T-W: root repeats 3x, WHITE to move and winning  -> a claim is optional; cp != 0 is arguable.
T-L: root repeats 3x, BLACK to move and lost     -> a claim is strictly better; correct score is cp 0.
Both fixtures validated in python-chess before any engine call (see job44_fixture_check*.out).

Known-answer control: the same harness on the counter-0 twins must show BOTH builds winning (not cp 0), so a cp 0
cannot be produced by a harness that simply always returns 0.
"""
import re, subprocess, sys, os

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
EVAL = re.compile(r"info string eval .*?\btotal (-?\d+)")
BASE = os.path.expanduser("~/build/forge")
PC = os.path.expanduser("~/pcbuild/forge")

CASES = [
    ("T-W root x3, WHITE winning", "1K6/8/8/3R4/8/8/8/k7 w - - 0 1",
     "d5d6 a1b1 d6d5 b1a1 d5d6 a1b1 d6d5 b1a1"),
    ("T-L root x3, BLACK lost", "1K6/8/8/3R4/8/8/8/k7 b - - 0 1",
     "a1b1 d5d6 b1a1 d6d5 a1b1 d5d6 a1b1 d6d5"),
    ("CONTROL T-W twin, no moves", "1K6/8/8/3R4/8/8/8/k7 w - - 0 1", None),
    ("CONTROL T-L twin, no moves", "1K6/8/8/3R4/8/8/8/k7 b - - 0 1", None),
]


def proc(exe):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    opts = set()
    p.stdin.write("uci\n"); p.stdin.flush()
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died")
        s = l.strip()
        if s.startswith("option name "):
            opts.add(s.split("option name ")[1].split(" type ")[0])
        if s == "uciok":
            break
    if "OwnBook" in opts:
        p.stdin.write("setoption name OwnBook value false\n"); p.stdin.flush()
    p.stdin.write("setoption name Threads value 1\n")
    p.stdin.write("setoption name Hash value 16\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    return p


def go(p, fen, moves, depth=12):
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    line = "position fen " + fen + (" moves " + moves if moves else "") + "\n"
    p.stdin.write(line); p.stdin.flush()
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


def evaltot(p, fen, moves):
    p.stdin.write("position fen " + fen + (" moves " + moves if moves else "") + "\n"); p.stdin.flush()
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


print("| case | build | eval total | go depth 12 | nodes | bestmove |")
print("|---|---|---|---|---|---|")
for label, fen, moves in CASES:
    for name, exe in (("base", BASE), ("PC r15", PC)):
        p = proc(exe)
        ev = evaltot(p, fen, moves)
        (score, val, nodes), bm = go(p, fen, moves)
        print("| %s | %s | %s | %s %d | %d | %s |" % (label, name, ev, score, val, nodes, bm))
        sys.stdout.flush()
        p.stdin.write("quit\n"); p.stdin.flush()
        try:
            p.wait(timeout=10)
        except Exception:
            p.kill()
