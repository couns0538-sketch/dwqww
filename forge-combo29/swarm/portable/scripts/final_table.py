"""Final table: every ratio slot-corrected the same way, with its own validation.

The estimator is median over positions of sqrt(fwd_i * rev_i^-1). Two arms per
comparison, run in opposite slot order, so a constant multiplicative slot bias s
cancels: fwd = s*T, rev^-1 = T/s, geomean = T.

Validation is NOT the A/A control (which cancels to 1.0 by construction and so
proves nothing about the estimator). Validation is the implied bias
sqrt(fwd/rev^-1), which the four raw medians fix and the estimator cannot tune;
it must land on the separately measured A/A value.
"""

import json
import math
import os
import random
import statistics
import sys
from math import comb

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

import paths

PAIRS = [
    ("x86-64-v2, FORGE_PORTABLE=ON", "abba-native-v2.json", "abba-rev-v2.json"),
    ("x86-64-v3, FORGE_PORTABLE=ON", "abba-native-v3.json", "abba-rev-v3.json"),
    ("x86-64-v3, PEXT=1 ZMM=0 (hand-built)", "abba-v3pext.json", "abba-rev-v3pext.json"),
    ("x86-64-v4, PEXT=1 ZMM=1 (CMake default, closest to native)",
     "abba-v4both.json", "abba-rev-v4both.json"),
    ("x86-64-v4, PEXT=0 ZMM=0 (v4 ISA, no switches)",
     "abba-v4-avx2-nopext-nopext.json", "abba-rev-v4-avx2-nopext-nopext.json"),
    ("x86-64-v4, PEXT=1 ZMM=0 (only ZMM off)",
     "abba-v4-avx2-pext.json", "abba-rev-v4-avx2-pext.json"),
    ("x86-64-v4, PEXT=0 ZMM=1 (only PEXT off)",
     "abba-v4-zmm-nopext.json", "abba-rev-v4-zmm-nopext.json"),
]


def ratios(name, invert=False):
    """One ABBA arm from the work dir, validated.

    A missing or empty arm raises rather than contributing a silently wrong
    median: the whole point of this table is that each number is a real
    measurement of two real runs.
    """
    path = paths.in_path(name)
    if not os.path.isfile(path):
        raise paths.InputError(f"ABBA arm {name!r} not found -- run scripts/abba.py for it first")
    with open(path, encoding="utf-8") as f:
        rows = json.load(f)["rows"]
    if not rows:
        raise paths.InputError(f"ABBA arm {name!r} has no rows")
    return [(1.0 / (row["B_med"] / row["A_med"])) if invert else (row["B_med"] / row["A_med"])
            for row in rows]


def boot_ci(values, n=20000, seed=4242):
    rnd = random.Random(seed)
    k = len(values)
    meds = sorted(statistics.median([values[rnd.randrange(k)] for _ in range(k)]) for _ in range(n))
    return meds[int(0.025 * n)], meds[int(0.975 * n)]


def sign_p(faster, slower):
    n = faster + slower
    if n == 0:
        return 1.0
    k = min(faster, slower)
    return min(1.0, 2 * sum(comb(n, j) for j in range(k + 1)) / (2 ** n))


def main():
    try:
        s_aa = statistics.median(ratios("abba-AA.json"))
    except paths.InputError as exc:
        print(f"final_table.py: {exc}", file=sys.stderr)
        return 2

    print(f"slot bias measured by the A/A control: s = {s_aa:.4f} "
          f"(B slot {(1-s_aa)*100:.2f}% faster than A slot, same binary both slots)")
    print()

    hdr = (f"{'build':48s} {'ratio':>7s} {'cost':>8s} {'CI95':>17s} "
           f"{'faster':>10s} {'implied s':>10s} {'vs A/A':>7s}")
    print(hdr)
    print("-" * len(hdr))

    rows_out = []
    for label, fwd_name, rev_name in PAIRS:
        try:
            fwd = ratios(fwd_name)
            rev = ratios(rev_name, invert=True)
        except paths.InputError as exc:
            print(f"{label:48s} SKIPPED -- {exc}")
            continue
        if len(fwd) != len(rev):
            print(f"{label:48s} SKIPPED -- arms have different lengths "
                  f"({len(fwd)} vs {len(rev)}); they are not paired")
            continue

        f = statistics.median(fwd)
        rv = statistics.median(rev)
        implied = math.sqrt(f / rv)
        per = [(a * b) ** 0.5 for a, b in zip(fwd, rev)]
        est = statistics.median(per)
        lo, hi = boot_ci(per)
        faster = sum(1 for x in per if x < 1.0)
        slower = sum(1 for x in per if x > 1.0)
        p = sign_p(faster, slower)
        print(f"{label:48s} {est:7.4f} {(est-1)*100:+7.2f}% "
              f"[{lo:.4f},{hi:.4f}] {faster:4d}/{len(per):<5d} {implied:10.4f} "
              f"{abs(implied-s_aa)/s_aa*100:6.2f}%")
        rows_out.append({
            "build": label, "ratio": est, "cost_pct": (est - 1) * 100,
            "ci95": [lo, hi], "faster": faster, "slower": slower, "n": len(per),
            "sign_p": p, "implied_slot_bias": implied,
            "raw_forward_median": f, "raw_reverse_inverted_median": rv,
        })

    print()
    print("'ratio' is portable/native on wall time at a fixed 'go nodes 200000':")
    print("  ratio > 1 means the portable build is SLOWER by (ratio-1).")
    print("'implied s' is sqrt(fwd / rev^-1) -- a prediction fixed by the raw medians.")
    print("  It must match the A/A s above; the last column is the disagreement.")
    print()
    print("Both-arms table, and the sign test on the per-position direction:")
    print(f"{'build':48s} {'sign p':>10s}")
    for r in rows_out:
        print(f"{r['build']:48s} {r['sign_p']:10.2e}")

    with open(paths.out_path("final-timing.json"), "w", encoding="utf-8") as f:
        json.dump({"slot_bias_s": s_aa, "rows": rows_out}, f, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
