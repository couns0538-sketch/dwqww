#!/usr/bin/env python3
"""node_rate_cores.py : ms per MILLION REPORTED nodes, pinned to 1, 2 and 4 cores.

Seat 12's S-F26 claims the anchor is core-count independent (578/576/577 ms per million). This checks it on my
machine, which matters because every timing number I have published rests on this box's speed.

Method: `go nodes 1000000` with stdout drained to bestmove (19-F12 — a pipelined quit yields the fabricated
0-node answer and would give a nonsense rate), reading the FINAL reported node count and the wall time on a
monotonic clock. `taskset` pins the process. 5 runs per core count, median reported.
"""
import re
import subprocess
import sys
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/pcbuild/forge"
OPTFILE = sys.argv[2] if len(sys.argv) > 2 else ""
RUNS = int(sys.argv[3]) if len(sys.argv) > 3 else 5

INFO = re.compile(r"^info depth (\d+) .*?nodes (\d+)")


def one(cores, target=1000000):
    cmd = ["taskset", "-c", ",".join(str(c) for c in range(cores)), EXE]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    names = set()
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died in uci")
        s = l.strip()
        if s.startswith("option name "):
            names.add(s.split("option name ")[1].split(" type ")[0])
        if s == "uciok":
            break
    if OPTFILE:
        for line in [x.strip() for x in open(OPTFILE) if x.strip() and not x.startswith("#")]:
            nm = line.split("name ")[1].split(" value ")[0]
            if nm not in names:
                raise RuntimeError("STOP: %r not in uci list" % nm)
            p.stdin.write(line + "\n"); p.stdin.flush()
            p.stdin.write("isready\n"); p.stdin.flush()
            while p.stdout.readline().strip() != "readyok":
                pass
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position startpos\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    t0 = time.monotonic()
    p.stdin.write("go nodes %d\n" % target); p.stdin.flush()
    nodes = 0
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died in search")
        s = l.strip()
        m = INFO.match(s)
        if m:
            nodes = int(m.group(2))
        if s.startswith("bestmove"):
            break
    wall = time.monotonic() - t0
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    if nodes == 0:
        raise RuntimeError("reported 0 nodes: the fabricated-bestmove path, result would be meaningless")
    return wall, nodes


print("ms per MILLION REPORTED nodes, taskset-pinned, %d runs each" % RUNS)
print("| cores | median ms per million nodes | reported nodes per run |")
print("|---|---|---|")
meds = {}
for cores in (1, 2, 4):
    rates = []
    ns = []
    for _ in range(RUNS):
        wall, nodes = one(cores)
        rates.append(1000.0 * wall * 1e6 / nodes)
        ns.append(nodes)
    rates.sort()
    med = rates[len(rates) // 2]
    meds[cores] = med
    print("| %d | %.1f | %d-%d |" % (cores, med, min(ns), max(ns)))

lo, hi = min(meds.values()), max(meds.values())
print()
print("spread across core counts: %.1f to %.1f ms per million (%.1f %% apart)"
      % (lo, hi, 100.0 * (hi - lo) / lo))
print("core-count independent within 5 percent: %s" % ("YES" if (hi - lo) / lo <= 0.05 else "NO"))
