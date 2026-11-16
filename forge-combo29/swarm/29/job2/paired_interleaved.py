#!/usr/bin/env python3
"""Interleaved paired benchmark: base vs patched, 12 rounds, order inside each round alternating.

Design: for each round, run base then patched, then patched then base in the next round (ABBA). Both sides are
built twice, so each side's two builds are also interleaved, which shows whether build-to-build differences swamp
the effect. This controls for slow machine drift (other swarm seats are sharing the 4 cores), which a
"10 runs of A, then 10 runs of B" design does not.

Measured value: the engine's own `bench 13` milliseconds (steady_clock around the search only, so start-up and the
one-time TT clear are excluded). Nodes are checked identical in every run; a run whose node count differs is
reported and excluded (there should be none).

Statistics: ratio patched/base per pair, mean, and a 95% interval by paired bootstrap (10000 resamples, seed 2901).
"""
import random, statistics, subprocess, sys, time

ROUNDS = 12
CMD = "uci\nsetoption name Hash value 16\nsetoption name Threads value 1\nisready\nbench 13\nquit\n"
EXPECTED_NODES = 862329


def one_run(exe):
    out = subprocess.run([exe], input=CMD, capture_output=True, text=True).stdout
    ms = nodes = None
    for line in out.splitlines():
        if line.startswith("info string bench depth 13"):
            f = line.split()
            for i, tok in enumerate(f):
                if tok == "time":
                    ms = int(f[i + 1])
                if tok == "nodes":
                    nodes = int(f[i + 1])
    return ms, nodes


exes = {"baseA": sys.argv[1], "baseB": sys.argv[2], "patchA": sys.argv[3], "patchB": sys.argv[4]}
pairs = []          # (base_ms, patch_ms)
dropped = 0
for r in range(ROUNDS):
    for side_b, side_p in (("baseA", "patchA"), ("baseB", "patchB")):
        bs = [side_b, side_p] if r % 2 == 0 else [side_p, side_b]
        got = {}
        for name in bs:
            ms, nodes = one_run(exes[name])
            if ms is None or nodes != EXPECTED_NODES:
                dropped += 1
                print(f"round {r+1} {name}: DROPPED (ms={ms} nodes={nodes})")
                got[name] = None
            else:
                got[name] = ms
        if got[side_b] is not None and got[side_p] is not None:
            pairs.append((got[side_b], got[side_p]))
            print(f"round {r+1:2d} {side_b[:6]:6s} {got[side_b]:4d} ms | {side_p[:6]:6s} {got[side_p]:4d} ms "
                  f"| ratio {got[side_p]/got[side_b]:.4f}")

base = [p[0] for p in pairs]
pat = [p[1] for p in pairs]
ratios = [b / a for a, b in pairs]
print()
print(f"pairs used: {len(pairs)}   dropped: {dropped}")
print(f"base   mean {statistics.mean(base):.1f} ms  median {statistics.median(base)}  min {min(base)}  max {max(base)}")
print(f"patched mean {statistics.mean(pat):.1f} ms  median {statistics.median(pat)}  min {min(pat)}  max {max(pat)}")
random.seed(2901)
boots = sorted(statistics.mean([random.choice(ratios) for _ in ratios]) for _ in range(10000))
lo, hi = boots[250], boots[9750]
m = statistics.mean(ratios)
print()
print(f"patched/base = {m:.4f}   -> {100*(1/m-1):+.2f}% speed "
      f"95% CI [{lo:.4f}, {hi:.4f}]")
print("verdict:", "patched faster (CI entirely below 1)" if hi < 1.0 else
      "patched slower (CI entirely above 1)" if lo > 1.0 else "INDISTINGUISHABLE (CI spans 1)")
