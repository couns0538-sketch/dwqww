#!/usr/bin/env python3
"""node_limit_control.py : the CONTROL for 23-F17 ("go nodes N stops short of N").

A "stops short" claim is only measured if the same harness can also see a run that reaches or exceeds N.
This script:
  - sends `go nodes N` for small N where a single depth's cost is tiny, so the engine can come close to N;
  - drains stdout to `bestmove` before sending anything else (a pipelined quit fabricates `bestmove a2a3`
    with 0 nodes — seat 19's 19-F12 — and would fake this control);
  - reports, per N, the last info-line node count and whether it is <, = or > N.

A healthy result here means: the harness reports real node counts (not the fabricated 0/a2a3), so the
shortfall measured at N = 20000/50000/250000 is a property of the engine, not of the runner.
"""
import re
import subprocess
import sys

EXE = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/pcbuild/forge"
FEN = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
INFO = re.compile(r"^info depth (\d+).*?nodes (\d+)")

print("exe", EXE)
print("position", FEN)
print()
print("| N | info lines | last nodes | vs N | bestmove |")
print("|---|---|---|---|---|")
for n in (1, 26, 100, 500, 1000, 2000, 5000, 20000, 50000, 250000):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    while True:
        l = p.stdout.readline()
        if not l or l.strip() == "uciok":
            break
    p.stdin.write("position fen %s\n" % FEN); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("go nodes %d\n" % n); p.stdin.flush()
    last = None
    count = 0
    bm = None
    while True:
        line = p.stdout.readline()
        if not line:
            raise RuntimeError("engine died")
        s = line.strip()
        m = INFO.match(s)
        if m:
            count += 1
            last = int(m.group(2))
        if s.startswith("bestmove"):
            bm = s.split()[1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    rel = "< N" if (last or 0) < n else ("= N" if last == n else "> N")
    print("| %d | %d | %s | %s | %s |" % (n, count, last if last is not None else "none", rel, bm))
