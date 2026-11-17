#!/usr/bin/env python3
"""timing_clang.py — the same measurement as timing.py, but on CLANG builds of base and the
count-2 patch. Purpose: test my own environment table (S-F114), which predicts that a patch whose
result was negative under g++/no-LTO/no-PGO may behave differently under clang.

Single build per side here (only one clang build of each exists), so this is indicative only;
the g++ measurement with two builds per side remains the primary result.
"""
import random
import re
import statistics
import subprocess
import sys

sys.path.insert(0, '/agent/repos/dwqww/forge-combo29/swarm/11')
from pc20 import PC20
from job_v3.timing import verdict_of

BASE = "/tmp/cl_base/forge"
PATCH = "/tmp/cl_p3/forge"
NET = "/tmp/v3test.fnn3"
RUNS = int(sys.argv[1]) if len(sys.argv) > 1 else 20


def nps(exe):
    opts = PC20 + [f"NNUEArchFile {NET}", "NNUEArch true"]
    inp = "uci\n" + "".join(
        f"setoption name {o.partition(' ')[0]} value {o.partition(' ')[2]}\n" for o in opts
    ) + "bench 13\nquit\n"
    out = subprocess.run([exe], input=inp, capture_output=True, text=True, timeout=300).stdout
    m = re.search(r"nps (\d+)", out)
    return int(m.group(1)) if m else None


print("CLANG build: base vs count-2 patch, bench 13 under PC20 + test net")
print("(one build per side -- INDICATIVE only; the g++ two-build result is primary)\n")
b, p = [], []
for i in range(RUNS):
    nb = nps(BASE)
    np_ = nps(PATCH)
    if nb:
        b.append(nb)
    if np_:
        p.append(np_)
    if (i + 1) % 5 == 0:
        print(f"  after {i+1} rounds: base mean {statistics.mean(b):.0f}, patch mean {statistics.mean(p):.0f}")

mb, mp = statistics.median(b), statistics.median(p)
print(f"\n  base  median {mb:.0f} nps (n={len(b)})")
print(f"  patch median {mp:.0f} nps (n={len(p)})")
print(f"  RATIO {mp/mb:.4f}  ({(mp/mb-1)*100:+.2f}%)")
print(f"  verdict: {verdict_of(b, p)}")
print("\n  Compare with the g++ measurement (job_v3/timing_p3.txt): ratio 0.9954, CI [0.9913, 0.9989].")
print("  My environment table predicted the patch might behave DIFFERENTLY under clang -- not that")
print("  it would win. Either outcome confirms 'different'; neither is a ship recommendation.")
