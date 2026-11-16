#!/usr/bin/env python3
"""check_29F3.py EXE OUTDIR : independent check of seat 29's 29-F3.

29-F3 claims: a depth-independent ~14 ms of every `bench N` report is one-time work inside the bench timer
(the Searcher construction plus its 16 MB transposition table being cleared once per FEN, 8 times), so nps
from shallow benches is understated.

How I test it, without reading their script:
  The claim is "a FIXED cost per bench report, independent of depth". A fixed cost shows up as a non-zero
  intercept when reported time is plotted against reported nodes. So I run bench 1..8 (nodes grow fast with
  depth) in fresh processes, several times each, and fit time = a + b*nodes. If a is clearly positive and
  of the order of 10-15 ms, the claim holds for the intercept.

  Then I test the SECOND half of their claim, that the cost lives in the Searcher construction and the
  per-FEN clear: with depth so low that searching is nearly free (depth 1), the reported time must be
  almost entirely that fixed cost. bench 1 is the direct probe.

Verdict rule, fixed before running:
  CONFIRMS if bench 1's median reported time is >= 8 ms (i.e. a fixed cost of that order exists) AND the
  fitted intercept is between 8 and 25 ms AND the fitted intercept is under 30 % of bench 13's median time
  (their "3.2 %" is for the 14 ms figure; I state the actual ratio rather than require theirs).
  REFUTES otherwise, and the output shows which clause failed.
"""
import os
import re
import statistics
import subprocess
import sys

exe, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
for v in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
    os.environ.pop(v, None)

REPS = 9
data = {}
for depth in (1, 2, 4, 6, 8, 10, 13):
    rows = []
    for _ in range(REPS):
        proc = subprocess.run([exe], input="bench %d\nquit\n" % depth, capture_output=True,
                              text=True, timeout=600)
        m = re.search(r"bench depth %d nodes (\d+) time (\d+) nps (\d+)" % depth, proc.stdout)
        if not m:
            print("no bench line for depth", depth)
            continue
        rows.append((int(m.group(1)), int(m.group(2))))
    data[depth] = rows

with open(os.path.join(outdir, "bench_by_depth.txt"), "w") as fh:
    fh.write("exe: %s\nreps per depth: %d\n\n| depth | nodes | median time ms | min | max |\n"
             "|---|---|---|---|---|\n" % (os.path.abspath(exe), REPS))
    for depth, rows in data.items():
        times = [t for _, t in rows]
        nodes = sorted({n for n, _ in rows})
        fh.write("| %d | %s | %.1f | %d | %d |\n" % (depth, nodes, statistics.median(times),
                                                     min(times), max(times)))

# least squares over the per-run points: time = a + b*nodes
pts = [(n, t) for rows in data.values() for n, t in rows]
N = len(pts)
sx = sum(n for n, _ in pts)
sy = sum(t for _, t in pts)
sxx = sum(n * n for n, _ in pts)
sxy = sum(n * t for n, t in pts)
den = N * sxx - sx * sx
b = (N * sxy - sx * sy) / den
a = (sy - b * sx) / N

bench1 = statistics.median([t for _, t in data[1]])
bench13 = statistics.median([t for _, t in data[13]])
ratio = 100.0 * a / bench13

with open(os.path.join(outdir, "RESULT.txt"), "w") as fh:
    fh.write("least squares over %d runs across depths 1,2,4,6,8,10,13\n" % N)
    fh.write("fitted intercept (fixed cost per report): %.2f ms\n" % a)
    fh.write("fitted slope: %.6f ms per node\n" % b)
    fh.write("median bench 1 time: %.1f ms ; median bench 13 time: %.1f ms\n" % (bench1, bench13))
    fh.write("intercept as a share of a bench 13 report: %.2f %%\n" % ratio)
    clause1 = bench1 >= 8.0
    clause2 = 8.0 <= a <= 25.0
    clause3 = ratio < 30.0
    fh.write("\nclause 1 (bench 1 median >= 8 ms): %s\n" % clause1)
    fh.write("clause 2 (8 <= intercept <= 25 ms): %s\n" % clause2)
    fh.write("clause 3 (intercept < 30 %% of bench 13): %s\n" % clause3)
    fh.write("\nVERDICT %s 29-F3\n" % ("CONFIRMS" if (clause1 and clause2 and clause3) else "REFUTES"))
print(open(os.path.join(outdir, "RESULT.txt")).read())
print(open(os.path.join(outdir, "bench_by_depth.txt")).read())
