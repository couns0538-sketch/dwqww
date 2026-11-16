#!/usr/bin/env python3
"""overshoot_test.py EXE OUT.txt : test the SUSPICION that the stop time is set by iteration
granularity, not by the deadline.

Method: for movetime 50 with overhead 0 and default, print EVERY info line's depth and time for one search,
so the iteration boundaries are visible. If the search stops at the first depth boundary at or after the
deadline, then the final time brackets the plan from above by less than one iteration.
Also run a LONGER movetime (2000) where a single iteration is short compared with the budget: there the
overhead subtraction should be clearly visible if it is the mechanism.
"""
import re
import subprocess
import sys
import time

EXE, OUT = sys.argv[1], sys.argv[2]
FEN = "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"


def trace(fen, movetime, overhead):
    setup = ["uci", "isready", "setoption name OwnBook value false", "isready",
             "setoption name Threads value 1", "isready", "setoption name Hash value 16", "isready"]
    if overhead is not None:
        setup += [f"setoption name Move Overhead value {overhead}", "isready"]
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    for c in setup:
        p.stdin.write(c + "\n")
        p.stdin.flush()
    p.stdin.write(f"position fen {fen}\nisready\ngo movetime {movetime}\n")
    p.stdin.flush()
    rows = []
    while True:
        line = p.stdout.readline()
        if not line:
            break
        if line.startswith("info depth"):
            d = re.search(r"depth (\d+)", line)
            t = re.search(r"\btime (\d+)", line)
            s = re.search(r"score (cp|mate) (-?\d+)", line)
            if d and t:
                rows.append((int(d.group(1)), int(t.group(1)),
                             f"{s.group(1)} {s.group(2)}" if s else "?"))
        if line.startswith("bestmove"):
            break
    try:
        p.stdin.write("quit\n")
        p.stdin.flush()
        p.wait(timeout=5)
    except Exception:
        p.kill()
    return rows


out = []
for movetime, overhead in ((50, None), (50, 0), (2000, None), (2000, 0)):
    rows = trace(FEN, movetime, overhead)
    plan = movetime - (10 if overhead is None else overhead)
    out.append(f"### movetime {movetime} overhead {overhead} (plan {plan} ms)")
    for d, t, sc in rows:
        out.append(f"   depth {d:2d}  time {t:5d} ms  score {sc}")
    last = rows[-1] if rows else None
    out.append(f"   -> final depth {last[0] if last else None} at {last[1] if last else None} ms "
               f"(plan {plan}, overshoot {(last[1]-plan) if last else None} ms)")
    out.append("")
text = "\n".join(out) + "\n"
print(text)
with open(OUT, "w") as fh:
    fh.write(text)
