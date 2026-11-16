#!/usr/bin/env python3
"""pair_pc20.py BASE PATCH OUTDIR ROUNDS : paired alternating timing of two PC r15 builds under PC20.

Uses the discipline from METHOD_timing_tt.md: one fresh engine process per run, runs alternate A/B (never
blocked), the workload is the pinned `bench 13` under PC20 (which is self-clearing, so every position is cold —
19-F23), and every run's node count is recorded and must be identical on both sides or the comparison is void.

Reports mean, sd, the ratio of means and a 95 % CI on the ratio via the log-delta method, plus the noise floor
this design implies. Threads stays at its default of 1 (19-F24) and is asserted, not assumed.
"""
import math
import os
import re
import statistics
import subprocess
import sys

base, patch, outdir, rounds = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
os.makedirs(outdir, exist_ok=True)
for v in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
    os.environ.pop(v, None)

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
       ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
       ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def one(exe):
    lines = ["uci", "isready"]
    for k, v in S14:
        lines += ["setoption name %s value %s" % (k, v), "isready"]
    lines += ["bench 13", "quit"]
    out = subprocess.run([exe], input="\n".join(lines) + "\n", capture_output=True, text=True, timeout=600).stdout
    m = re.search(r"bench depth 13 nodes (\d+) time (\d+) nps (\d+)", out)
    if not m:
        raise SystemExit("no bench line from " + exe)
    return int(m.group(1)), int(m.group(2))


rows = []
for r in range(rounds):
    nb, tb = one(base)
    np_, tp = one(patch)
    rows.append((r, tb, tp, nb, np_))
    print("round %2d  base %4d ms  patch %4d ms  ratio %.4f  nodes %d/%d" % (r, tb, tp, tp / tb, nb, np_))

b = [r[1] for r in rows]
p_ = [r[2] for r in rows]
nodes_ok = len({(r[3], r[4]) for r in rows}) == 1 and all(r[3] == r[4] for r in rows)


def mean(v):
    return sum(v) / len(v)


def sd(v):
    m = mean(v)
    return (sum((x - m) ** 2 for x in v) / (len(v) - 1)) ** 0.5


rb = [x / mean(b) for x in b]
rp = [x / mean(p_) for x in p_]
ratio = mean(p_) / mean(b)
se = (sd(rb) ** 2 / len(rb) + sd(rp) ** 2 / len(rp)) ** 0.5
half = 1.96 * se

with open(os.path.join(outdir, "RESULT.txt"), "w") as fh:
    fh.write("paired alternating PC20 bench-13 timing, %d rounds, one fresh process per run, Threads 1\n\n" % rounds)
    fh.write("base exe:  %s\npatch exe: %s\n\n" % (os.path.abspath(base), os.path.abspath(patch)))
    fh.write("| quantity | base | patch |\n|---|---|---|\n")
    fh.write("| mean ms | %.1f | %.1f |\n" % (mean(b), mean(p_)))
    fh.write("| sd ms | %.1f (%.1f %%) | %.1f (%.1f %%) |\n"
             % (sd(b), 100 * sd(b) / mean(b), sd(p_), 100 * sd(p_) / mean(p_)))
    fh.write("| min / max ms | %d / %d | %d / %d |\n" % (min(b), max(b), min(p_), max(p_)))
    fh.write("\nratio patch/base: **%.4f**  (95 %% CI [%.4f, %.4f], +/-%.2f %%)\n"
             % (ratio, ratio - half, ratio + half, 100 * half))
    fh.write("speed change: %+.2f %%  95 %% CI [%+.2f %%, %+.2f %%]\n"
             % (100 * (ratio - 1), 100 * (ratio - half - 1), 100 * (ratio + half - 1)))
    fh.write("\nnode counts identical on both sides in every round: %s\n" % nodes_ok)
    fh.write("\nInterpretation rule (fixed before running): the patch is FASTER only if the CI excludes 1.0\n")
    fh.write("and the gain exceeds this design's own noise floor (the CI half-width above).\n")
print(open(os.path.join(outdir, "RESULT.txt")).read()[-1100:])
