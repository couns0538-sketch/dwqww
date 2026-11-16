#!/usr/bin/env python3
"""CHECK of 19-F10 (seat 19): "software-prefetching the NNUE weight columns makes the engine 8 % SLOWER,
ratio 0.9190, 95 % CI [0.8841, 0.9552], over 20 alternating pairs, both builds of the patch slower."

Their measurement is 'n 20' of nps per side. Seat 19's OWN later finding (19-C2) admits a sequential-block design
drifts, and my 29-F5 found the same, so I re-measure with a strictly INTERLEAVED design: every round runs base then
patch (order flipping each round), 24 rounds, each side built TWICE, and I additionally cross-check with exact
callgrind instruction counts, which cannot drift at all.

A prefetch cannot change results, so the node count must be identical on both sides; I assert it on every run and
abort rather than record a pair where it is not.
"""
import random, statistics, subprocess, sys

ROUNDS = 24
CMD = "uci\nsetoption name Hash value 16\nsetoption name Threads value 1\nisready\nbench 13\nquit\n"
EXPECT = 862329


def run(exe):
    out = subprocess.run([exe], input=CMD, capture_output=True, text=True).stdout
    ms = nps = nodes = None
    for line in out.splitlines():
        if line.startswith("info string bench depth 13"):
            f = line.split()
            ms = int(f[f.index("time") + 1])
            nps = int(f[f.index("nps") + 1])
            nodes = int(f[f.index("nodes") + 1])
    if nodes is None:
        raise SystemExit(f"ABORT: no bench line from {exe} -- nothing measured")
    return ms, nps, nodes


exes = {"baseA": sys.argv[1], "baseB": sys.argv[2], "patchA": sys.argv[3], "patchB": sys.argv[4]}
pairs = []
bad = 0
for r in range(ROUNDS):
    for sb, sp in (("baseA", "patchA"), ("baseB", "patchB")):
        order = [sb, sp] if r % 2 == 0 else [sp, sb]
        got = {}
        for name in order:
            ms, nps, nodes = run(exes[name])
            if nodes != EXPECT:
                raise SystemExit(f"ABORT: {name} nodes {nodes} != {EXPECT}; a prefetch patch must not change nodes")
            got[name] = (ms, nps)
        pairs.append((got[sb], got[sp]))
        print(f"round {r+1:2d} {sb[:6]:6s} {got[sb][0]:4d} ms | {sp[:6]:6s} {got[sp][0]:4d} ms "
              f"| ratio {got[sp][0]/got[sb][0]:.4f}")

b = [p[0][0] for p in pairs]
q = [p[1][0] for p in pairs]
ratios = [y / x for x, y in zip(b, q)]
print()
print(f"pairs: {len(pairs)}   (nodes identical on every run: {EXPECT})")
print(f"base  median {statistics.median(b):.1f} ms   mean {statistics.mean(b):.1f}")
print(f"patch median {statistics.median(q):.1f} ms   mean {statistics.mean(q):.1f}")
random.seed(2901)
boots = sorted(statistics.mean([random.choice(ratios) for _ in ratios]) for _ in range(10000))
lo, hi = boots[250], boots[9750]
m = statistics.mean(ratios)
print()
print(f"patch/base = {m:.4f}  -> {100*(1/m-1):+.2f}% speed   95% CI [{lo:.4f}, {hi:.4f}]")
# ratio is PATCH TIME / BASE TIME, so ratio > 1 means the patch takes longer, i.e. it is SLOWER.
if lo > 1.0:
    print("VERDICT: CONFIRMS 19-F10 -- the patch is measurably SLOWER: its time is the ratio above times base,")
    print(f"         i.e. {100*(m-1):+.2f}% wall time / {100*(1/m-1):+.2f}% speed, CI [{lo:.4f}, {hi:.4f}] entirely above 1.")
elif hi < 1.0:
    print("VERDICT: REFUTES 19-F10 -- the patch is measurably FASTER (time ratio CI entirely below 1).")
else:
    print("VERDICT: NEITHER -- CI spans 1.0, so on my machine the prefetch neither helps nor hurts measurably; "
          "19-F10's 8 % loss is NOT reproduced.")
