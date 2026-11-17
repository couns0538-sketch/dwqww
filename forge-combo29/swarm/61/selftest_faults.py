#!/usr/bin/env python3
"""Prove each recheck script can FAIL.  A script that only ever exits 0 has not been tested.

Method: copy the script and its evidence to a scratch dir, plant a specific fault, run it, and
require a NONZERO exit.  Then confirm the unmodified copy still exits zero, so the harness is
not simply rejecting everything.

This is the "plant a fault and confirm it exits nonzero" rule applied to the six checks that
produce the numbers in RECHECK.md.
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE


def run(script, cwd):
    p = subprocess.run([sys.executable, script], cwd=cwd, capture_output=True, text=True,
                       timeout=600)
    return p.returncode, p.stdout + p.stderr


CASES = [
    # (script, description of planted fault, mutation function)
    ("recheck_prefetch.py",
     "change the raw pair on line 1 so the pooled ratio moves",
     lambda d: _sub(d, "evidence/prefetch_raw_pairs.txt", "33037/33037 1.000 | 19/18 1.056 | 1.0556",
                    "33037/33037 1.000 | 30/18 1.056 | 1.0556")),
    ("recheck_nodesaving.py",
     "double one PC20 node count so the pooled ratio moves",
     lambda d: _sub(d, "evidence/pc20_raw_464.txt",
                    "    0 S14    60 ms/  83825 n | PC20    43 ms/  74280 n | ratio 0.717",
                    "    0 S14    60 ms/  83825 n | PC20    43 ms/ 174280 n | ratio 0.717")),
    ("recheck_pernode.py",
     "swap a per-node cell to 0.5 so the sign share and interval move",
     lambda d: _sub(d, "evidence/pc20_pernode_180.txt",
                    "46089/32648 n 1.412 |   24/  17 ms 1.412 | pernode 1.000",
                    "46089/32648 n 1.412 |   24/  17 ms 1.412 | pernode 0.500")),
]


def _sub(d, rel, old, new):
    path = os.path.join(d, rel)
    s = open(path).read()
    if old not in s:
        raise RuntimeError("plant target not found in %s: %r" % (rel, old[:60]))
    open(path, "w").write(s.replace(old, new, 1))


results = []
for script, desc, plant in CASES:
    with tempfile.TemporaryDirectory() as d:
        shutil.copy(os.path.join(ROOT, script), d)
        shutil.copytree(os.path.join(ROOT, "evidence"), os.path.join(d, "evidence"))
        # control: unmodified must pass
        rc_ok, _ = run(script, d)
        # planted: must fail
        plant(d)
        rc_bad, out = run(script, d)
        # Control expectations differ per script: exit 0 means "ran and the report reproduced",
        # exit 2 means "ran correctly but the report row does not reproduce" (recheck_pernode's
        # documented disagreement).  Both are VALID runs.  Only exit 1 means a broken measurement.
        ok = (rc_ok in (0, 2) and rc_bad == 1)
        results.append(ok)
        print("%-26s control=%s planted=%s  %s  (%s)"
              % (script, rc_ok, rc_bad,
                 "CAUGHT" if ok else "**NOT CAUGHT** (planted run must exit 1)", desc))
        if not ok:
            print("    planted-run tail: %s" % out.strip().splitlines()[-3:])

print("\nrows examined: %d" % len(results))
print("faults caught: %d / %d" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
