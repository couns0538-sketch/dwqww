#!/usr/bin/env python3
"""Planted-bug check for evalscale_20261027.py: each mutant (one exact replacement) must make the unit tests fail.

  python -I -B mutation_check_s41.py [--work <new dir>]
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE / "evalscale_20261027.py"
TESTS = HERE / "test_evalscale_20261027.py"

MUTANTS = [
    ("lad_unweighted_median", "return weighted_median(y[m] / x[m], np.abs(x[m]))", "return float(np.median(y[m] / x[m]))"),
    ("sym_without_sqrt", "return math.sqrt(lad(x, y) / lad(y, x))", "return lad(x, y) / lad(y, x)"),
    ("engine_rounding_not_truncation", "return np.trunc(values * percent / 100.0)", "return np.round(values * percent / 100.0)"),
    ("netscale_wrong_direction", '"netscale_percent": int(round(100.0 / s)),', '"netscale_percent": int(round(100.0 * s)),'),
    ("in_check_not_excluded", 'base = ref["valid"] & cand["valid"] & ~ref["in_check"] & ~cand["in_check"]',
     'base = ref["valid"] & cand["valid"]'),
    ("sampler_partial_line", "f.readline()                      # finish the partial line", "pass"),
    ("theil_sen_keeps_dx_zero", "    m = dx != 0\n    slopes", "    m = dx == dx\n    slopes"),
    ("q_ratio_inverted", "(float(b / a) if a != 0", "(float(a / b) if b != 0"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work")
    a = ap.parse_args()
    work = Path(a.work) if a.work else Path(tempfile.mkdtemp(prefix="s41_mut_"))
    work.mkdir(parents=True, exist_ok=True)
    src = TOOL.read_text(encoding="utf-8")
    base = subprocess.run([sys.executable, "-I", "-B", str(TESTS)], capture_output=True, text=True,
                          env=dict(os.environ, EVALSCALE_TOOL=str(TOOL)))
    print(f"unmutated tool: tests {'PASS' if base.returncode == 0 else 'FAIL'}")
    if base.returncode != 0:
        print(base.stderr[-2000:])
        return 1
    caught = 0
    for name, old, new in MUTANTS:
        if src.count(old) != 1:
            print(f"{name}: pattern occurs {src.count(old)} times -> mutation not applicable (FAIL)")
            continue
        mutant = work / f"evalscale_{name}.py"
        mutant.write_text(src.replace(old, new), encoding="utf-8", newline="\n")
        r = subprocess.run([sys.executable, "-I", "-B", str(TESTS)], capture_output=True, text=True,
                           env=dict(os.environ, EVALSCALE_TOOL=str(mutant)))
        failed = [ln.split(" (")[0] for ln in r.stderr.splitlines() if ln.startswith(("FAIL:", "ERROR:"))]
        ok = r.returncode != 0
        caught += ok
        print(f"{name}: {'CAUGHT' if ok else 'NOT CAUGHT'} ({len(failed)} failing: {', '.join(failed[:4])})")
    print(f"mutants caught {caught}/{len(MUTANTS)}")
    return 0 if caught == len(MUTANTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
