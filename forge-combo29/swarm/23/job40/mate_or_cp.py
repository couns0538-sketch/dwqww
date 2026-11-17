#!/usr/bin/env python3
"""job40 : is the PC's `mate 8` at counter 78 genuine reach, and is its cp 278 at counter 89 a depth artefact?

Board 1K6/8/8/3R4/8/8/8/k7 w at counters 78 and 89, both builds, depths 12/14/16/20.
Prints score, nodes, bestmove and the PV length so a mate claim can be checked against its own PV.
Known-answer control: the same harness on the same board at counter 0 must show both builds winning (not cp 0).
"""
import re, subprocess, sys, os

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
PVLEN = re.compile(r" pv ")
FEN = "1K6/8/8/3R4/8/8/8/k7 w - - %d 1"
BUILDS = (("base", os.path.expanduser("~/build/forge")),
          ("PC r15", os.path.expanduser("~/pcbuild/forge")))


def proc(exe):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    opts = set()
    p.stdin.write("uci\n"); p.stdin.flush()
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died during uci")
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


def search(p, fen, depth):
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen " + fen + "\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("go depth %d\n" % depth); p.stdin.flush()
    last = None
    pvlen = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died in search")
        s = l.strip()
        m = INFO.match(s)
        if m:
            last = (m.group(2), int(m.group(3)), int(m.group(4)))
            tail = s[s.find(" pv ") + 4:] if " pv " in s else ""
            pvlen = len(tail.split()) if tail else 0
        if s.startswith("bestmove"):
            return last, pvlen, s.split()[1]


CASES = [("CONTROL counter 0", 0, (12,)), ("counter 78", 78, (12, 14, 16, 20)),
         ("counter 89", 89, (12, 14, 16, 20))]
print("| case | build | depth | score | nodes | pv plies | bestmove |")
print("|---|---|---|---|---|---|---|")
for label, c, depths in CASES:
    fen = FEN % c
    for name, exe in BUILDS:
        p = proc(exe)
        for d in depths:
            (score, val, nodes), pvlen, bm = search(p, fen, d)
            print("| %s | %s | %d | %s %d | %d | %s | %s |" % (label, name, d, score, val, nodes,
                                                              pvlen if score == "mate" else "-", bm))
            sys.stdout.flush()
        p.stdin.write("quit\n"); p.stdin.flush()
        try:
            p.wait(timeout=15)
        except Exception:
            p.kill()
print()
print("P1 base reports SOME mate at counter 78 depth 16/20.  P2 mate distances agree within 1.")
print("P3 PC is cp 0 at counter 89 depth 16 and 20.        P4 base is cp 0 at counter 89 all depths.")
