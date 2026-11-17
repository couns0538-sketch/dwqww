#!/usr/bin/env python3
"""timing_selftest.py — POSITIVE CONTROL for the three-way verdict in timing.py.
The harness must say FASTER when the CI is above 1.0, SLOWER when below, NOT PROVEN when it spans.
A verdict function never exercised in two of its three branches is untested in those branches."""
import random, statistics, sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
from job_v3.timing import verdict_of   # added below

def check(name, base, patch, want):
    got = verdict_of(base, patch, seed=1101)
    ok = got.startswith(want)
    print(f"  {name:34} -> {got[:46]:48} {'PASS' if ok else 'FAIL (wanted ' + want + ')'}")
    return ok

rng = random.Random(7)
# clearly faster: patch ~5% above base, low noise
base  = [1_000_000 + rng.randrange(-2000, 2000) for _ in range(20)]
patch = [1_050_000 + rng.randrange(-2000, 2000) for _ in range(20)]
# clearly slower
slow  = [  950_000 + rng.randrange(-2000, 2000) for _ in range(20)]
# indistinguishable
same  = [1_000_000 + rng.randrange(-30000, 30000) for _ in range(20)]
ok = True
ok &= check("patch 5% faster", base, patch, "PATCH IS FASTER")
ok &= check("patch 5% slower", base, slow, "PATCH IS SLOWER")
ok &= check("identical, wide noise", base, same, "NOT PROVEN")
print(f"\n  verdict control {'PASSED - all three branches exercised' if ok else 'FAILED'}")
sys.exit(0 if ok else 1)
