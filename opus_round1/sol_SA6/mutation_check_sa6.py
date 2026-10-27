#!/usr/bin/env python3
"""Planted-bug check for opus_sa6_plan_check.py: every mutant copy must make test_opus_sa6.py fail.

usage: python -I -B mutation_check_sa6.py --work <new dir>   (copies only; nothing is deleted)
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = ["opus_sa6_plan_check.py", "test_opus_sa6.py"]
MUTANTS = [
    ("iterations_ignore_pairs", 'n_iter = st["games"] // (2 * st["pairs_per_iteration"])', 'n_iter = st["games"] // 2'),
    ("game_time_one_side", "return 2.0 * (share * base + inc * moves)", "return (share * base + inc * moves)"),
    ("missing_check_off", "if missing:", "if False:"),
    ("range_floor_off", "if rng < 50:", "if rng < 5:"),
    ("c_end_upper_off", "if not (1 <= c_end <= 0.1 * rng):", "if not (1 <= c_end):"),
    ("gamma_sign", 'c = c_end * n_iter ** sch["gamma"]', 'c = c_end / n_iter ** sch["gamma"]'),
]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", type=Path, required=True)
    a = ap.parse_args()
    a.work.mkdir(parents=True, exist_ok=False)
    base = a.work / "unmutated"
    base.mkdir()
    for f in FILES:
        shutil.copy2(HERE / f, base / f)
    r = subprocess.run([sys.executable, "-I", "-B", str(base / "test_opus_sa6.py")], capture_output=True, text=True)
    print(f"unmutated: exit {r.returncode}")
    if r.returncode:
        print(r.stderr)
        return 1
    caught = 0
    for name, old, new in MUTANTS:
        d = a.work / name
        d.mkdir()
        for f in FILES:
            shutil.copy2(HERE / f, d / f)
        t = (d / FILES[0]).read_text(encoding="utf-8")
        assert t.count(old) == 1, (name, t.count(old))
        (d / FILES[0]).write_bytes(t.replace(old, new).encode("utf-8"))
        r = subprocess.run([sys.executable, "-I", "-B", str(d / "test_opus_sa6.py")], capture_output=True, text=True)
        fails = [ln for ln in r.stderr.splitlines() if ln.startswith(("FAIL:", "ERROR:"))]
        caught += r.returncode != 0
        print(f"{'CAUGHT' if r.returncode else 'MISSED'} {name}: {fails[:2]}")
    print(f"RESULT {caught}/{len(MUTANTS)} mutants caught")
    return 0 if caught == len(MUTANTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
