#!/usr/bin/env python3
"""movetime_check.py EXE OUT.txt : does `go movetime M` stop at M - MoveOverhead?

For each (movetime, overhead) pair, 25 searches from the same position, recording the engine's own reported
`time` from the last info line and the wall time with a monotonic clock. Prints median/p99/max of both.
"""
import re
import statistics
import subprocess
import sys
import time

EXE, OUT = sys.argv[1], sys.argv[2]
FEN = "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"
RUNS = 25
CASES = [(10, None), (50, None), (200, None), (50, 0), (200, 0), (50, 45)]


def one(fen, movetime, overhead):
    setup = ["uci", "isready", "setoption name OwnBook value false", "isready",
             "setoption name Threads value 1", "isready", "setoption name Hash value 16", "isready"]
    if overhead is not None:
        setup += [f"setoption name Move Overhead value {overhead}", "isready"]
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    for c in setup:
        p.stdin.write(c + "\n")
        p.stdin.flush()
    t0 = time.monotonic()
    p.stdin.write(f"position fen {fen}\nisready\ngo movetime {movetime}\n")
    p.stdin.flush()
    lines = []
    while True:
        line = p.stdout.readline()
        if not line:
            break
        lines.append(line.rstrip("\n"))
        if line.startswith("bestmove"):
            break
    wall = (time.monotonic() - t0) * 1000.0
    try:
        p.stdin.write("quit\n")
        p.stdin.flush()
        p.wait(timeout=5)
    except Exception:
        p.kill()
    eng_time = None
    for l in lines:
        m = re.search(r"\btime (\d+)", l)
        if l.startswith("info") and m:
            eng_time = int(m.group(1))
    best = next((l.split()[1] for l in lines if l.startswith("bestmove")), None)
    return eng_time, wall, best


out = []
for movetime, overhead in CASES:
    eng_times = []
    walls = []
    for _ in range(RUNS):
        et, w, best = one(FEN, movetime, overhead)
        if et is not None:
            eng_times.append(et)
        walls.append(w)
    tag = f"movetime {movetime:3d} overhead {str(overhead):>4s}"
    out.append(f"{tag}: engine_time median {statistics.median(eng_times) if eng_times else None:>6} "
               f"p99 {sorted(eng_times)[int(0.99*len(eng_times))-1] if eng_times else None:>6} "
               f"max {max(eng_times) if eng_times else None:>6} | "
               f"wall median {statistics.median(walls):7.2f} p99 "
               f"{sorted(walls)[int(0.99*len(walls))-1]:7.2f} max {max(walls):7.2f}")
    print(out[-1])
text = "\n".join(["position: " + FEN, f"runs per case: {RUNS}", ""] + out) + "\n"
with open(OUT, "w") as fh:
    fh.write(text)
