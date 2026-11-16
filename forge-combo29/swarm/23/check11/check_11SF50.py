#!/usr/bin/env python3
"""check_11SF50.py : independent check of seat 11's S-F50 (paired depth between the two builds).

Claim: for the SAME node budget, base 6b98f217 (Threads 1, Hash 16) and PC r15 (PC20) reach the same depth on only
4 of 10 openings at `go nodes 50000`, and on 0 of 10 at `go nodes 250000` — the PC is consistently 1-4 plies deeper.
So an equal-node match between them is biased toward the PC.

Method: 10 openings (real move sequences), for each: apply the opening to a fresh board, then `go nodes N` on each
build and record the depth reached. Threads 1, Hash 16, OwnBook false, drained, fresh process per search.

CONTROL: the two builds must agree at a very SMALL budget (where both search depth 1-2) — otherwise the harness could
be misreading depth and the comparison would be meaningless.
"""
import re
import subprocess
import sys

import chess

BASE = "/home/ubuntu/build/forge"
PC = "/home/ubuntu/pcbuild/forge"
OPTPC = "../job7/pc20_opts.txt"
INFO = re.compile(r"^info depth (\d+)")

OPENINGS = [
 ("London",      "d2d4 d7d5 b1f3 g8f6 e2e3 c7c5"),
 ("Ruy Lopez",   "e2e4 e7e5 g1f3 b8c6 f1b5 a7a6"),
 ("French",      "e2e4 e7e6 d2d4 d7d5 b1c3 g8f6"),
 ("Sicilian",    "e2e4 c7c5 g1f3 d7d6 d2d4 c5d4"),
 ("QGD",         "d2d4 d7d5 c2c4 e7e6 b1c3 g8f6"),
 ("King's Indian","d2d4 g8f6 c2c4 g7g6 b1c3 f8g7"),
 ("English",     "c2c4 e7e5 b1c3 g8f6 g1f3 b8c6"),
 ("Reti",        "g1f3 d7d5 c2c4 e7e6 b2b3 g8f6"),
 ("Caro-Kann",   "e2e4 c7c6 d2d4 d7d5 b1c3 d5e4"),
 ("Scandinavian","e2e4 d7d5 e4d5 d8d5 b1c3 d5a5"),
]
BUDGETS = [50000, 250000]


def depth_for(exe, moves, nodes, opts):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    names = set()
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died")
        s = l.strip()
        if s.startswith("option name "):
            names.add(s.split("option name ")[1].split(" type ")[0])
        if s == "uciok":
            break
    for line in opts:
        nm = line.split("name ")[1].split(" value ")[0]
        if nm not in names:
            raise RuntimeError("STOP: %r not in uci list" % nm)
        p.stdin.write(line + "\n"); p.stdin.flush()
        p.stdin.write("isready\n"); p.stdin.flush()
        while p.stdout.readline().strip() != "readyok":
            pass
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position startpos moves %s\n" % moves); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("go nodes %d\n" % nodes); p.stdin.flush()
    deepest = 0
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died in search")
        s = l.strip()
        m = INFO.match(s)
        if m:
            deepest = max(deepest, int(m.group(1)))
        if s.startswith("bestmove"):
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return deepest


pc_opts = [x.strip() for x in open(OPTPC) if x.strip() and not x.startswith("#")]
pc_opts = pc_opts + ["setoption name OwnBook value false"]

print("== CONTROL: at a tiny budget both builds should search the same shallow depth")
for name, mv in OPENINGS[:3]:
    b = depth_for(BASE, mv, 1000, [])
    p_ = depth_for(PC, mv, 1000, pc_opts)
    print("  %-14s base depth %d | PC depth %d | %s" % (name, b, p_, "agree" if b == p_ else "DIFFER"))

for budget in BUDGETS:
    print()
    print("== go nodes %d" % budget)
    print("| opening | base depth | PC depth | PC deeper by | same depth? |")
    print("|---|---|---|---|---|")
    same = 0
    deltas = []
    for name, mv in OPENINGS:
        b = depth_for(BASE, mv, budget, [])
        p_ = depth_for(PC, mv, budget, pc_opts)
        deltas.append(p_ - b)
        if b == p_:
            same += 1
        print("| %s | %d | %d | %+d | %s |" % (name, b, p_, p_ - b, "yes" if b == p_ else "NO"))
    print()
    print("  openings reaching the SAME depth: %d of %d" % (same, len(OPENINGS)))
    print("  PC-deeper deltas: min %+d, max %+d" % (min(deltas), max(deltas)))
