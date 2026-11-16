#!/usr/bin/env python3
"""probe_selftests.py -- the missing-parse control for the two scripts that judge MY OWN python checkers rather
than an engine, so the no-score stub engine cannot reach them:

  job1/dtm2_selftest.py  judges dtm2.py
  job1/dtm_selftest.py   judges dtm.py (deleted; superseded by dtm2.py)

Method: put a stub `dtm2.py` / `dtm.py` EARLIER on the path (a copy of the script's own directory, in /tmp) that
prints NOTHING, then run the selftest against it. A safe selftest must NOT print PASS or a per-case MISMATCH
derived from an absent verdict.
"""
import os
import shutil
import subprocess
import sys

ROOT = "/agent/repos/dwqww/forge-combo29/swarm/05"
CASES = [
    ("job1/dtm2_selftest.py", "dtm2.py"),
    ("job1/dtm_selftest.py", "dtm.py"),
]

print("=" * 96)
print("MISSING-PARSE CONTROL for the two selftests (they judge my own checkers, not an engine)")
print("=" * 96)
print()
for rel, stub_name in CASES:
    src = os.path.join(ROOT, rel)
    if not os.path.exists(src):
        print(f"{rel}: SCRIPT MISSING")
        continue
    d = f"/tmp/pselftest_{stub_name.replace('.', '_')}"
    os.makedirs(d, exist_ok=True)
    shutil.copy(src, os.path.join(d, os.path.basename(rel)))
    # the stub that prints nothing at all
    with open(os.path.join(d, stub_name), "w") as f:
        f.write("import sys\nsys.exit(0)\n")
    p = subprocess.run([sys.executable, os.path.basename(rel)], cwd=d,
                       capture_output=True, text=True, timeout=600)
    out = p.stdout + p.stderr
    last = [l for l in out.splitlines() if l.strip()][-1:] or ["(no output)"]
    noparse = "NO_VERDICT" in out
    passed = "PASS" in out
    mism = out.count("MISMATCH")
    print(f"### {rel}   (with a {stub_name} that prints nothing)")
    print(f"    exit={p.returncode}  prints PASS={passed}  MISMATCH count={mism}  says NO_VERDICT={noparse}")
    print(f"    last line: {last[0][:110]}")
    if passed:
        print("    VERDICT: **UNSAFE — still prints PASS from a no-parse run**")
    elif noparse and p.returncode != 0:
        print("    VERDICT: safe — fails closed (no PASS, explicit NO_VERDICT, non-zero exit)")
    elif noparse:
        print("    VERDICT: safe on the text, but exit status is 0 — noted")
    else:
        print("    VERDICT: safe — no PASS printed")
    print()
