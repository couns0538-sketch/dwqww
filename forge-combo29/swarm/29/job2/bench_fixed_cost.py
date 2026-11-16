#!/usr/bin/env python3
"""How much of a `bench N` run is fixed cost (table allocation + 8 TT clears) that the depth does not scale?

For N in 1,2,4,8,13: measure the engine's reported `time` (inside the bench timer) and the process wall time.
A straight-line fit of reported time against N gives the per-depth cost; the intercept is the fixed part of the
MEASURED window. Subtracting the measured window from the process wall time gives the unmeasured start-up.

This matters because bench numbers are used all over the swarm as a speed proxy, and a fixed 30 ms in a 450 ms
bench is 7% of every nps figure, which shrinks as depth grows (benching deeper than 13 makes the fixed part
proportionally smaller and so flatters nps).
"""
import statistics, subprocess, sys, time

EXE = sys.argv[1]
REPS = 5
rows = []
for d in (1, 2, 4, 8, 13, 16):
    eng, wall = [], []
    for _ in range(REPS):
        cmd = f"uci\nsetoption name Hash value 16\nsetoption name Threads value 1\nisready\nbench {d}\nquit\n"
        t0 = time.monotonic()
        out = subprocess.run([EXE], input=cmd, capture_output=True, text=True).stdout
        wall.append((time.monotonic() - t0) * 1000.0)
        for line in out.splitlines():
            if line.startswith(f"info string bench depth {d}"):
                f = line.split()
                eng.append(int(f[f.index("time") + 1]))
    rows.append((d, statistics.median(eng), statistics.median(wall)))
    print(f"bench {d:2d}: reported time median {statistics.median(eng):7.1f} ms   process wall median {statistics.median(wall):7.1f} ms"
          f"   (reported: {eng})")

# least squares on (depth, reported ms)
n = len(rows)
sx = sum(r[0] for r in rows); sy = sum(r[1] for r in rows)
sxx = sum(r[0] ** 2 for r in rows); sxy = sum(r[0] * r[1] for r in rows)
slope = (n * sxy - sx * sy) / (n * sxx - sx * sx)
inter = (sy - slope * sx) / n
print()
print(f"reported_ms = {inter:.2f} + {slope:.2f} * depth     (least squares over the {n} depths above)")
print(f"=> fixed part of the measured window: {inter:.1f} ms (~{inter/4.5:.0f}k nodes' worth at bench-13 nps)")
print(f"=> at bench 13 ({rows[4][1]:.0f} ms) that fixed part is {100*inter/rows[4][1]:.1f}% of the reported time")
startup = [w - e for (d, e, w) in rows]
print(f"=> process wall minus reported window, per depth: {[round(x) for x in startup]} ms "
      f"(start-up + UCI parsing + exit, outside the timer)")
