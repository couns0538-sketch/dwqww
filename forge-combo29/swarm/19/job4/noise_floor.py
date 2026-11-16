#!/usr/bin/env python3
"""noise_floor.py EXE FENS OUTDIR ROUNDS : the noise floor of a TIMED R_1911 run, base against base.

This measures the thing RECIPE_tt_validation.md could not give: how small a speed change a timed run of this
workload can actually resolve. It runs the SAME binary twice, alternating, so the measured ratio is 1.0 by
construction and every deviation from 1.0 is noise.

Design (deliberately mirroring job2/pair_bench.sh's logic, applied to this workload):
  - one fresh engine process per run
  - runs ALTERNATE A/B, never blocked (blocking drifts with machine load; 19-C2 proved that on bench)
  - both sides are the SAME exe, so the true ratio is exactly 1.0
  - report mean, sd, and the 95 % CI of the ratio; the CI's half-width IS the detectable effect size

Timing: monotonic clock around the whole 200-position sweep, one process, Hash 16, OwnBook false.
"""
import os
import re
import statistics
import subprocess
import sys
import time

exe, fens, outdir, rounds = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
os.makedirs(outdir, exist_ok=True)
positions = [l.strip() for l in open(fens) if l.strip()][:200]


def sweep():
    """One timed 200-position sweep in a single fresh process. Returns seconds and the node total."""
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True, bufsize=1)

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
    for opt, val in (("Hash", "16"), ("OwnBook", "false")):
        send("setoption name %s value %s" % (opt, val))
        send("isready")
        read_to(lambda l: l.startswith("readyok"))

    nodes = 0
    t0 = time.monotonic()
    for fen in positions:
        send("position fen " + fen)
        send("isready")
        read_to(lambda l: l.startswith("readyok"))
        send("go depth 12")
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            if " nodes " in line:
                try:
                    nodes = max(nodes, int(line.split("nodes ")[1].split()[0]))
                except (IndexError, ValueError):
                    pass
            if line.startswith("bestmove"):
                break
    t1 = time.monotonic()
    send("quit")
    try:
        proc.communicate(timeout=120)
    except subprocess.TimeoutExpired:
        proc.kill()
    return t1 - t0, nodes


rows = []
for r in range(rounds):
    ta, na = sweep()
    tb, nb = sweep()
    rows.append((r, ta, tb, na, nb))
    print("round %2d  A %.3f s  B %.3f s  ratio %.4f  nodes %d/%d" % (r, ta, tb, tb / ta, na, nb))

a = [r[1] for r in rows]
b = [r[2] for r in rows]
nodes = sorted({r[3] for r in rows} | {r[4] for r in rows})


def mean(v):
    return sum(v) / len(v)


def sd(v):
    m = mean(v)
    return (sum((x - m) ** 2 for x in v) / (len(v) - 1)) ** 0.5


ratio = mean(b) / mean(a)
rel_a, rel_b = sd(a) / mean(a), sd(b) / mean(b)
# 95 % CI half-width of the ratio from the two relative sds (independent samples, n each)
n = len(a)
halfwidth = 1.96 * ((rel_a ** 2 / n + rel_b ** 2 / n) ** 0.5)

with open(os.path.join(outdir, "RESULT.txt"), "w") as fh:
    fh.write("noise floor of a timed R_1911 sweep (base vs base, alternating, %d rounds)\n\n" % rounds)
    fh.write("positions per run: 200   depth 12   Hash 16   one fresh process per run\n\n")
    fh.write("| quantity | value |\n|---|---|\n")
    fh.write("| node totals seen | %s |\n" % nodes)
    fh.write("| mean A | %.3f s |\n" % mean(a))
    fh.write("| mean B | %.3f s |\n" % mean(b))
    fh.write("| sd A | %.3f s (%.2f %% of mean) |\n" % (sd(a), 100 * rel_a))
    fh.write("| sd B | %.3f s (%.2f %% of mean) |\n" % (sd(b), 100 * rel_b))
    fh.write("| A-vs-B ratio (true value 1.0000) | %.4f |\n" % ratio)
    fh.write("| 95 %% CI half-width | +/- %.2f %% |\n" % (100 * halfwidth))
    fh.write("\nDetectable effect at this noise and this sample size: about %.1f %% or larger.\n"
             % (100 * halfwidth))
print(open(os.path.join(outdir, "RESULT.txt")).read())
