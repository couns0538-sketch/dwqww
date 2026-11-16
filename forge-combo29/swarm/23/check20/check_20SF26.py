#!/usr/bin/env python3
"""check_20SF26.py : independent check of seat 20's S-F26.

Claim: the wtime at which `winc 1000` starts to change the answer (the "increment-ignored boundary") TRACKS
Move Overhead and equals roughly overhead + 4: first wtime where winc 1000 changes anything is 5 at overhead 0,
14 at overhead 10 (default), 35 at overhead 30.

Method: for each overhead and each wtime in a small sweep, search the SAME position twice — once with winc 0 and
once with winc 1000 — and compare the reported node counts (a node-count difference is the cleanest signal that
the increment was used). Threads 1, Hash 16, drained, fresh process per search.

CONTROL: at a large wtime the two must DIFFER (the increment is obviously usable then), otherwise the test cannot
detect anything and the whole table is meaningless.
"""
import re
import subprocess
import sys

EXE = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/build/forge"
OPTFILE = sys.argv[2] if len(sys.argv) > 2 else ""
FEN = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
INFO = re.compile(r"^info depth (\d+) .*?nodes (\d+)")

OVERHEADS = [0, 10, 30]
WTIMES = [1, 3, 5, 8, 12, 14, 16, 20, 30, 35, 40, 60, 200, 2000]


def nodes_for(wtime, winc, overhead, opts):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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
    # OwnBook must be OFF: FABLE_TO_swarm_3 records that OwnBook defaults to TRUE and answers a book move with no
    # search at all, which would make every node count 0 and the whole sweep meaningless.
    allopts = list(opts) + ["setoption name Move Overhead value %d" % overhead,
                            "setoption name OwnBook value false"]
    for line in allopts:
        nm = line.split("name ")[1].split(" value ")[0]
        if nm not in names:
            raise RuntimeError("STOP: %r not in uci list" % nm)
        p.stdin.write(line + "\n"); p.stdin.flush()
        p.stdin.write("isready\n"); p.stdin.flush()
        while p.stdout.readline().strip() != "readyok":
            pass
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen %s\n" % FEN); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("go wtime %d btime %d winc %d binc %d\n" % (wtime, wtime, winc, winc))
    p.stdin.flush()
    last = 0
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died in search")
        s = l.strip()
        m = INFO.match(s)
        if m:
            last = int(m.group(2))
        if s.startswith("bestmove"):
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return last


opts = []
if OPTFILE:
    opts = [x.strip() for x in open(OPTFILE) if x.strip() and not x.startswith("#")]

print("increment-ignored boundary vs Move Overhead — base build, Threads 1, Hash 16")
print("node count with winc 0 vs winc 1000 at the same wtime; 'changes' means the counts differ")
print()
print("| overhead | wtime | nodes (winc 0) | nodes (winc 1000) | changes |")
print("|---|---|---|---|---|")
first_change = {}
for ov in OVERHEADS:
    fc = None
    for wt in WTIMES:
        a = nodes_for(wt, 0, ov, opts)
        b = nodes_for(wt, 1000, ov, opts)
        ch = a != b
        if ch and fc is None:
            fc = wt
        print("| %d | %d | %d | %d | %s |" % (ov, wt, a, b, "yes" if ch else "no"))
    first_change[ov] = fc
    print("| %d | -- | first wtime where it changes: %s -- | | |" % (ov, fc))

print()
print("| overhead | first changing wtime | overhead + 4 |")
print("|---|---|---|")
for ov in OVERHEADS:
    print("| %d | %s | %d |" % (ov, first_change[ov], ov + 4))

print()
print("CONTROL: at wtime 2000 the counts must differ for every overhead — %s"
      % ("see the table rows at 2000" if all(
          nodes_for(2000, 0, ov, opts) != nodes_for(2000, 1000, ov, opts) for ov in OVERHEADS)
          else "CONTROL FAILED"))
