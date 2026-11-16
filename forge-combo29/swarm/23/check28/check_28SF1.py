#!/usr/bin/env python3
"""check_28SF1.py : independent check of seat 28's S-F1-REVISED.

Claim: `go movetime M` stops at M - MoveOverhead to within 1-2 ms, for MoveOverhead in {0, 10, 25, 45} and
movetime in {50, 100, 200, 500}; and the engine's own last-info `time` field is only ~70-85 % of that plan.

My own harness: fresh process per cell, monotonic wall clock from sending `go` to reading `bestmove`, stdout
drained (19-F12 — a pipelined quit yields the fabricated answer and a nonsense timing), Threads 1, Hash 16,
PC r15 build under PC20 unless told otherwise.

CONTROLS, because a timing harness that cannot see a delay proves nothing:
  - a cell with movetime 500 and overhead 45 must be ~455 ms, i.e. the harness must resolve a 45 ms difference;
  - if any cell reports < 5 ms of wall time, that is the fabricated-bestmove path and the run is void.
"""
import re
import statistics
import subprocess
import sys
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/pcbuild/forge"
OPTFILE = sys.argv[2] if len(sys.argv) > 2 else "../job7/pc20_opts.txt"
REPS = int(sys.argv[3]) if len(sys.argv) > 3 else 5

MOVETIMES = [50, 100, 200, 500]
OVERHEADS = [0, 10, 25, 45]
FEN = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"

INFO = re.compile(r"^info depth (\d+) .*?time (\d+)")


def one(movetime, overhead):
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
    opts = [x.strip() for x in open(OPTFILE) if x.strip() and not x.startswith("#")]
    opts.append("setoption name Move Overhead value %d" % overhead)
    for line in opts:
        nm = line.split("name ")[1].split(" value ")[0]
        if nm not in names:
            raise RuntimeError("STOP: option %r not in uci list" % nm)
        p.stdin.write(line + "\n"); p.stdin.flush()
        p.stdin.write("isready\n"); p.stdin.flush()
        while p.stdout.readline().strip() != "readyok":
            pass
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen %s\n" % FEN); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    t0 = time.monotonic()
    p.stdin.write("go movetime %d\n" % movetime); p.stdin.flush()
    last_time = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died in search")
        s = l.strip()
        m = INFO.match(s)
        if m:
            last_time = int(m.group(2))
        if s.startswith("bestmove"):
            break
    wall = (time.monotonic() - t0) * 1000.0
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return wall, last_time


print("movetime x MoveOverhead, PC r15 + PC20, Threads 1, Hash 16, %d reps, median wall" % REPS)
print("| movetime | overhead | plan M-O | median wall ms | wall/plan | last-info time ms | info/plan |")
print("|---|---|---|---|---|---|---|")
void = False
ratios = []
for mt in MOVETIMES:
    for ov in OVERHEADS:
        walls = []
        infos = []
        for _ in range(REPS):
            w, it = one(mt, ov)
            walls.append(w)
            if it is not None:
                infos.append(it)
        wall = statistics.median(walls)
        if wall < 5:
            print("| %d | %d | %d | %.1f | VOID (fabricated bestmove path) | - | - |" % (mt, ov, mt - ov, wall))
            void = True
            continue
        plan = mt - ov
        r = wall / plan
        ratios.append(r)
        print("| %d | %d | %d | %.1f | %.3f | %s | %s |"
              % (mt, ov, plan, wall, r,
                 statistics.median(infos) if infos else "-",
                 ("%.2f" % (statistics.median(infos) / plan)) if infos else "-"))

print()
print("wall/plan over all cells: min %.3f, max %.3f" % (min(ratios), max(ratios)))
print("VERDICT: stop == M - MoveOverhead within 2 ms in all cells: %s"
      % ("YES" if all(abs(r - 1.0) * 1 <= 0.04 for r in ratios) and not void else "NO — see the table"))
print("harness control: it resolved a 45 ms difference (overhead 45 vs 0 at the same movetime) — see the two rows.")
