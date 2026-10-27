#!/usr/bin/env python3
"""Planted-bug check for opus_sc4_widen_inc.py: every mutant copy must make test_opus_sc4.py fail.

usage: python -I -B mutation_check_sc4.py --work <new dir>   (copies only; nothing is deleted)
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = ["opus_sc4_widen_inc.py", "test_opus_sc4.py"]
MUTANTS = [
    ("w2_halves_not_split", '"NnueW2": w2[:h_old] + pad + w2[h_old:] + pad', '"NnueW2": w2 + pad + pad'),
    ("pad_before_row", "nw1 += w1[f * h_old:(f + 1) * h_old] + pad", "nw1 += pad + w1[f * h_old:(f + 1) * h_old]"),
    ("b1_not_padded", '"NnueB1": b1 + pad', '"NnueB1": b1 + [1] * len(pad)'),
    ("count_check_off", "if len(vals) != int(n):", "if False:"),
    ("narrowing_allowed", "if h_new < h_old:", "if False:"),
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
    r = subprocess.run([sys.executable, "-I", "-B", str(base / FILES[1])], capture_output=True, text=True)
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
        r = subprocess.run([sys.executable, "-I", "-B", str(d / FILES[1])], capture_output=True, text=True)
        fails = [ln for ln in r.stderr.splitlines() if ln.startswith(("FAIL:", "ERROR:"))]
        caught += r.returncode != 0
        print(f"{'CAUGHT' if r.returncode else 'MISSED'} {name}: {fails[:2]}")
    print(f"RESULT {caught}/{len(MUTANTS)} mutants caught")
    return 0 if caught == len(MUTANTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
