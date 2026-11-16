#!/usr/bin/env python3
"""drive_counters.py EXE FENS DEPTH LIMIT : drive searches the safe way and capture the instrumented
PICKBEST counter line, which the instrumented build prints to stderr at exit.

Why this exists rather than reusing drive_search.py: that script merges stderr into stdout and reads only what
arrives before `quit`, so the counter line printed at exit was never written to the raw file (it is buffered
until the process ends). Here stderr goes to its own file.
"""
import os
import subprocess
import sys

exe, fens, depth, limit, errpath = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
for v in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
    os.environ.pop(v, None)

positions = [l.strip() for l in open(fens) if l.strip()][:limit]
err = open(errpath, "w")
proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=err, text=True, bufsize=1)


def send(line):
    proc.stdin.write(line + "\n")
    proc.stdin.flush()


def read_to(pred):
    while True:
        line = proc.stdout.readline()
        if not line:
            return False
        if pred(line):
            return True


send("uci")
read_to(lambda l: l.startswith("uciok"))
send("isready")
read_to(lambda l: l.startswith("readyok"))
send("setoption name OwnBook value false")
send("isready")
read_to(lambda l: l.startswith("readyok"))

nodes_total = 0
zero = 0
for fen in positions:
    send("position fen " + fen)
    send("isready")
    read_to(lambda l: l.startswith("readyok"))
    send("go depth %d" % depth)
    best = 0
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        if " nodes " in line:
            try:
                best = max(best, int(line.split("nodes ")[1].split()[0]))
            except (IndexError, ValueError):
                pass
        if line.startswith("bestmove"):
            break
    nodes_total += best
    if best == 0:
        zero += 1

send("quit")
proc.communicate(timeout=120)
err.close()
print("positions %d  depth %d  total nodes %d  zero-node searches %d" % (len(positions), depth, nodes_total, zero))
print(open(errpath).read().strip().splitlines()[-1] if open(errpath).read().strip() else "(no counter line)")
