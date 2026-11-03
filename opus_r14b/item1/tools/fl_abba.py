#!/usr/bin/env python3
"""fl_abba.py - Opus R14-B: palindromic ABBA speed comparison of two loader arms (own code, stdlib only).

Each run is a fresh fl_equal.py process (`dump --no-hash`) on the same CPU mask and priority, reading the same file
from its start; the order is A B B A A B B A ... so slow drifts of the PC cancel. Speed = kept positions per second
over the timed batches (after the warm-up batches). ADVISORY: Engine QA does the official timing.

usage: python -I -B fl_abba.py --out DIR --pairs 10 --a old:<dll>:2 --b fast:<dll>:2 [--batches 420 --warmup 20]
       [--mask 0xC] [--priority BelowNormal] [--data <binpack>]
Writes DIR/run_XX_<arm>.tsv per run and DIR/summary.txt (per-run speeds, per-pair ratio B/A, median, mean, 95% CI).
"""

import argparse
import math
import os
import statistics
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = r"F:\forge_j1_data\forge_train_001-039_ex013-014_j2.binpack"
# Student t, two-sided 95 %, by degrees of freedom (pairs - 1), checked against scipy.stats.t.ppf(0.975, dof);
# 1.96 beyond 30. (Until 2026-11-02 19:15 only 10 pairs used t; other counts used 1.96, a too narrow CI.)
T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
        11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086,
        21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060, 26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045, 30: 2.042}


def parse_arm(arm):
    """loader:dll:workers (the DLL path itself contains a drive colon); None if malformed."""
    loader, _, rest = arm.partition(":")
    dll, _, workers = rest.rpartition(":")
    if loader not in ("old", "fast") or not dll or not workers.isdigit() or int(workers) < 1:
        return None
    return loader, dll, workers


def run_one(arm, out_tsv, a):
    loader, dll, workers = parse_arm(arm)
    cmd =[sys.executable, "-I", "-B", os.path.join(HERE, "fl_equal.py"), "dump", "--loader", loader, "--dll", dll,
           "--workers", workers, "--data", a.data, "--batches", str(a.batches), "--warmup", str(a.warmup),
           "--no-hash", "--out", out_tsv, "--mask", a.mask, "--priority", a.priority]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
    with open(out_tsv, encoding="utf-8") as f:
        for line in f:
            if line.startswith("# batches="):
                fields = dict(kv.split("=", 1) for kv in line[2:].split())
                return float(fields["kept_per_s"])
    raise RuntimeError(f"no speed line in {out_tsv}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--pairs", type=int, default=10)
    ap.add_argument("--a", required=True, help="loader:dll:workers")
    ap.add_argument("--b", required=True, help="loader:dll:workers")
    ap.add_argument("--batches", type=int, default=420)
    ap.add_argument("--warmup", type=int, default=20)
    ap.add_argument("--mask", default="0xC")
    ap.add_argument("--priority", default="BelowNormal", choices=["BelowNormal", "Idle"])
    ap.add_argument("--data", default=DATA)
    a = ap.parse_args()
    # bug hunt #16: these used to fail after the output folder was made (0 pairs: a traceback; 1 pair: a "95% CI" of
    # zero width from one ratio; a malformed arm, a bad mask or an existing folder: tracebacks)
    problems = [f"--{k} {v!r} is not loader:dll:workers with loader old|fast, an existing DLL and workers >= 1"
                for k, v in (("a", a.a), ("b", a.b)) if not parse_arm(v) or not os.path.isfile(parse_arm(v)[1])]
    if a.pairs < 2:
        problems.append("--pairs must be at least 2 (the confidence interval needs two pairs)")
    try:
        if int(a.mask, 16) <= 0:
            raise ValueError
    except ValueError:
        problems.append(f"--mask {a.mask!r} is not a hexadecimal CPU mask naming at least one CPU")
    if not os.path.isfile(a.data):
        problems.append(f"--data {a.data}: file not found")
    if os.path.exists(a.out) or not os.path.isdir(os.path.dirname(os.path.abspath(a.out))):
        problems.append(f"--out {a.out}: exists or its folder is missing (outputs are never overwritten)")
    if problems:
        print("fl_abba: " + "\nfl_abba: ".join(problems), file=sys.stderr)
        return 2
    os.makedirs(a.out, exist_ok=False)
    order = []
    for p in range(a.pairs):
        order += ["A", "B"] if p % 2 == 0 else ["B", "A"]
    speeds = {"A": [], "B": []}
    lines = [f"A = {a.a}", f"B = {a.b}", f"pairs {a.pairs}, batches {a.batches} (warm-up {a.warmup}), mask {a.mask}, "
             f"{a.priority}, data {a.data}", f"start {time.strftime('%Y-%m-%d %H:%M:%S')}", ""]
    for i, arm in enumerate(order):
        spec = a.a if arm == "A" else a.b
        try:
            s = run_one(spec, os.path.join(a.out, f"run_{i:02d}_{arm}.tsv"), a)
        except (subprocess.CalledProcessError, RuntimeError, OSError) as e:  # was a traceback (bug hunt #16)
            print(f"fl_abba: run {i:02d} ({arm}) failed: {e} - no speed figures", file=sys.stderr)
            return 1
        speeds[arm].append(s)
        lines.append(f"run {i:02d} {arm} {s:,.0f} kept/s")
        print(lines[-1], flush=True)
    ratios = [b / x for x, b in zip(speeds["A"], speeds["B"])]
    mean = statistics.fmean(ratios)
    sd = statistics.stdev(ratios) if len(ratios) > 1 else 0.0
    half = T975.get(len(ratios) - 1, 1.96) * sd / math.sqrt(len(ratios))
    lines += ["", f"A median {statistics.median(speeds['A']):,.0f} kept/s, B median {statistics.median(speeds['B']):,.0f}",
              "per-pair B/A: " + " ".join(f"{r:.3f}" for r in ratios),
              f"B/A median {statistics.median(ratios):.3f}, mean {mean:.3f}, 95% CI {mean - half:.3f} .. {mean + half:.3f}"
              f" (t, n={len(ratios)})", f"end {time.strftime('%Y-%m-%d %H:%M:%S')}"]
    with open(os.path.join(a.out, "summary.txt"), "x", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines[-4:]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
