#!/usr/bin/env python3
"""wall_vs_iteration.py EXE OUT.txt : separate WALL time (go -> bestmove) from the kept ITERATION's
`time` field, at movetime 50/200 crossed with overhead 0/10/45.

This resolves my S-C7 against seat 08's reconciliation: if wall time = plan + a small constant while the
kept iteration's `time` sits well below plan, then both observations are true and the distinction is the
finding. Prints both figures per row so the reader can check the arithmetic.
"""
import re
import statistics
import subprocess
import sys
import time

EXE, OUT = sys.argv[1], sys.argv[2]
FEN = "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"
ROWS = [(50, 0), (50, 10), (50, 45), (200, 0), (200, 10), (200, 45)]
REPS = 8


def one(movetime, overhead):
    setup = ["uci", "isready", "setoption name OwnBook value false", "isready",
             "setoption name Threads value 1", "isready", "setoption name Hash value 16", "isready",
             f"setoption name Move Overhead value {overhead}", "isready"]
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    for c in setup:
        p.stdin.write(c + "\n")
        p.stdin.flush()
        if c == "isready":
            while True:
                l = p.stdout.readline()
                if not l or l.strip() == "readyok":
                    break
    p.stdin.write(f"position fen {FEN}\nisready\n")
    p.stdin.flush()
    while True:
        l = p.stdout.readline()
        if not l or l.strip() == "readyok":
            break
    t0 = time.monotonic()
    p.stdin.write("go movetime %d\n" % movetime)
    p.stdin.flush()
    lines = []
    while True:
        l = p.stdout.readline()
        if not l:
            break
        lines.append(l.rstrip("\n"))
        if l.startswith("bestmove"):
            break
    wall = (time.monotonic() - t0) * 1000.0
    try:
        p.stdin.write("quit\n")
        p.stdin.flush()
        p.wait(timeout=5)
    except Exception:
        p.kill()
    iter_times = [int(m.group(1)) for l in lines if l.startswith("info")
                  for m in [re.search(r"\btime (\d+)", l)] if m]
    it = iter_times[-1] if iter_times else None
    if it is None:
        raise SystemExit("STOP: no iteration time parsed - refusing to report a row without a number")
    return wall, it


out = ["position: " + FEN, f"reps per row: {REPS}", "",
       "movetime overhead plan | wall median (plan+delta) | kept-iteration time median (plan-time) | "
       "wall>=plan"]
for movetime, overhead in ROWS:
    plan = max(1, movetime - overhead)
    walls = []
    its = []
    for _ in range(REPS):
        w, i = one(movetime, overhead)
        walls.append(w)
        its.append(i)
    wm = statistics.median(walls)
    im = statistics.median(its)
    out.append(f"{movetime:8d} {overhead:8d} {plan:4d} | {wm:8.2f} (+{wm-plan:6.2f}) | "
               f"{im:6.0f} ({im-plan:+6.0f}) | {sum(1 for w in walls if w >= plan)}/{REPS}")
    print(out[-1])

text = "\n".join(out) + "\n"
with open(OUT, "w") as fh:
    fh.write(text)
