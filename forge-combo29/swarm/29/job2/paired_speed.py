#!/usr/bin/env python3
"""Paired speed test: base vs patched, both built TWICE, 10 alternating `bench 13` runs per build.

Each run is a fresh process; the measured value is the engine's own `bench 13` wall milliseconds as reported on
its `info string bench depth 13 ... time N` line (steady_clock, so it excludes process start-up and the TT clear,
which is what we want: the patch only touches search work), plus an independent wall clock around the process.

Output: every raw run, then per-build means, then the base/patched ratio with a 95% interval by the paired
bootstrap over the 10 alternating pairs (patched_time / base_time), and the same for the build-to-build spread
so the 1.5%-class noise between two builds of one source is visible.
"""
import random, statistics, subprocess, sys, time

RUNS = 10
CMD = "uci\nsetoption name Hash value 16\nsetoption name Threads value 1\nisready\nbench 13\nquit\n"


def one_run(exe):
    t0 = time.monotonic()
    out = subprocess.run([exe], input=CMD, capture_output=True, text=True).stdout
    wall = time.monotonic() - t0
    engine_ms = None
    for line in out.splitlines():
        if line.startswith("info string bench depth 13"):
            for tok, nxt in zip(line.split(), line.split()[1:]):
                if tok == "time":
                    engine_ms = int(nxt)
    return engine_ms, wall * 1000.0


def measure(exe):
    r = [(one_run(exe)) for _ in range(RUNS)]
    return r


builds = {
    "base-A": sys.argv[1],
    "base-B": sys.argv[2],
    "patch-A": sys.argv[3],
    "patch-B": sys.argv[4],
}

raw = {}
for name, exe in builds.items():
    raw[name] = measure(exe)
    eng = [x[0] for x in raw[name]]
    print(f"{name:8s} engine_ms: {eng}  mean {statistics.mean(eng):.1f} median {statistics.median(eng)}")
    print(f"{'':8s} wall_ms  : {[round(x[1]) for x in raw[name]]}  mean {statistics.mean([x[1] for x in raw[name]]):.1f}")

print()
print("| build | engine_ms mean | engine_ms sd | wall_ms mean |")
print("|---|---|---|---|")
for name in builds:
    eng = [x[0] for x in raw[name]]
    wl = [x[1] for x in raw[name]]
    print(f"| {name} | {statistics.mean(eng):.1f} | {statistics.stdev(eng):.2f} | {statistics.mean(wl):.1f} |")

# Paired comparison: run i of base-A against run i of patch-A, etc.
def paired(a, b, label):
    ratios = [x[0] / y[0] for x, y in zip(raw[a], raw[b])]
    random.seed(2901)
    boots = []
    for _ in range(10000):
        boots.append(statistics.mean([random.choice(ratios) for _ in ratios]))
    boots.sort()
    lo, hi = boots[int(0.025 * len(boots))], boots[int(0.975 * len(boots))]
    mean = statistics.mean(ratios)
    print(f"{label}: patched/base = {mean:.4f}  "
          f"(speedup {100*(1/mean - 1):+.2f}%)  95% CI [{lo:.4f}, {hi:.4f}]  "
          f"({'patched faster' if hi < 1.0 else 'patched slower' if lo > 1.0 else 'INDISTINGUISHABLE'})")
    return mean, lo, hi

print()
print("paired ratios, patched_time / base_time (engine_ms), < 1 means the patch is faster:")
paired("base-A", "patch-A", "A builds")
paired("base-B", "patch-B", "B builds")
paired("base-A", "base-B", "base vs base  (build noise)")
paired("patch-A", "patch-B", "patch vs patch (build noise)")
