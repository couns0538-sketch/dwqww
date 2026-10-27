#!/usr/bin/env python3
"""Planted-bug check for the A7 tools: each mutant is a copy of the tools with one line changed; the test file must
FAIL on every mutant. Copies go to --work (must not exist); nothing is deleted.

usage: python -I -B mutation_check_a7.py --work <new dir>
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = ["opus_a7_dryparse.py", "opus_a7_curve_stats.py", "test_opus_a7.py"]
MUTANTS = [
    ("spe_off_by_one", "opus_a7_dryparse.py", 'spe = n_train // ns["batch_size"]', 'spe = n_train // ns["batch_size"] + 1'),
    ("max_train_ignores_available", "opus_a7_dryparse.py",
     'n_train = min(ns["max_train"] or n_available, n_available)', 'n_train = ns["max_train"] or n_available'),
    ("side_effect_guard_off", "opus_a7_dryparse.py", "if not (ok_first and ok_rest):", "if False:"),
    ("pooled_sd_dof", "opus_a7_curve_stats.py", "ss += (n - 1) * sd * sd", "ss += n * sd * sd"),
    ("plateau_two_sd", "opus_a7_curve_stats.py", "if abs(b[e] - final_sub) <= sd)", "if abs(b[e] - final_sub) <= 2 * sd)"),
    ("epoch_prediction_scale", "opus_a7_curve_stats.py", "d = math.log2(e / 48.0)", "d = math.log2(e / 32.0)"),
]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", type=Path, required=True)
    a = ap.parse_args()
    a.work.mkdir(parents=True, exist_ok=False)
    py = sys.executable
    base = a.work / "unmutated"
    base.mkdir()
    for f in FILES:
        shutil.copy2(HERE / f, base / f)
    r = subprocess.run([py, "-I", "-B", str(base / "test_opus_a7.py")], capture_output=True, text=True)
    print(f"unmutated: exit {r.returncode} ({r.stderr.strip().splitlines()[-1] if r.stderr.strip() else ''})")
    if r.returncode != 0:
        print(r.stderr)
        return 1
    caught = 0
    for name, f, old, new in MUTANTS:
        d = a.work / name
        d.mkdir()
        for g in FILES:
            shutil.copy2(HERE / g, d / g)
        t = (d / f).read_text(encoding="utf-8")
        assert t.count(old) == 1, (name, t.count(old))
        (d / f).write_text(t.replace(old, new), encoding="utf-8", newline="\n")
        r = subprocess.run([py, "-I", "-B", str(d / "test_opus_a7.py")], capture_output=True, text=True)
        failed = [ln for ln in r.stderr.splitlines() if ln.startswith(("FAIL:", "ERROR:"))]
        ok = r.returncode != 0
        caught += ok
        print(f"{'CAUGHT' if ok else 'MISSED'} {name}: exit {r.returncode}; {failed[:3]}")
    print(f"RESULT {caught}/{len(MUTANTS)} mutants caught")
    return 0 if caught == len(MUTANTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
