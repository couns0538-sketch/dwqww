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
import random
import statistics

AA = "/tmp/build/abba-AA.json"

PAIRS = [
    ("x86-64-v2, FORGE_PORTABLE=ON", "/tmp/build/abba-native-v2.json", "/tmp/build/abba-rev-v2.json"),
    ("x86-64-v3, FORGE_PORTABLE=ON", "/tmp/build/abba-native-v3.json", "/tmp/build/abba-rev-v3.json"),
    ("x86-64-v3, PEXT=1 ZMM=0 (hand-built)",
     "/tmp/build/abba-v3pext.json", "/tmp/build/abba-rev-v3pext.json"),
    ("x86-64-v4, PEXT=1 ZMM=1 (CMake default, closest to native)",
     "/tmp/build/abba-v4both.json", "/tmp/build/abba-rev-v4both.json"),
    ("x86-64-v4, PEXT=0 ZMM=0 (v4 ISA, no switches)",
     "/tmp/build/abba-v4-avx2-nopext-nopext.json", "/tmp/build/abba-rev-v4-avx2-nopext-nopext.json"),
    ("x86-64-v4, PEXT=1 ZMM=0 (only ZMM off)",
     "/tmp/build/abba-v4-avx2-pext.json", "/tmp/build/abba-rev-v4-avx2-pext.json"),
    ("x86-64-v4, PEXT=0 ZMM=1 (only PEXT off)",
     "/tmp/build/abba-v4-zmm-nopext.json", "/tmp/build/abba-rev-v4-zmm-nopext.json"),
]


def ratios(path, invert=False):
    rows = json.load(open(path))["rows"]
    x = [row["B_med"] / row["A_med"] for row in rows]
    return [1.0 / v for v in x] if invert else x


def boot_ci(values, n=20000, seed=4242):
    rnd = random.Random(seed)
    k = len(values)
    meds = sorted(statistics.median([values[rnd.randrange(k)] for _ in range(k)]) for _ in range(n))
    return meds[int(0.025 * n)], meds[int(0.975 * n)]


def sign_p(faster, slower):
    from math import comb
    n = faster + slower
    if n == 0:
        return 1.0
    k = min(faster, slower)
    return min(1.0, 2 * sum(comb(n, j) for j in range(k + 1)) / (2 ** n))


s_aa = statistics.median(ratios(AA))
print(f"slot bias measured by the A/A control: s = {s_aa:.4f} "
      f"(B slot {(1-s_aa)*100:.2f}% faster than A slot, same binary both slots)")
print()

hdr = (f"{'build':48s} {'ratio':>7s} {'cost':>8s} {'CI95':>17s} "
       f"{'faster':>10s} {'implied s':>10s} {'vs A/A':>7s}")
print(hdr)
print("-" * len(hdr))
rows_out = []
for label, fwd, rev in PAIRS:
    f = statistics.median(ratios(fwd))
    rv = statistics.median(ratios(rev, invert=True))
    implied = math.sqrt(f / rv)
    per = [(a * b) ** 0.5 for a, b in zip(ratios(fwd), ratios(rev, invert=True))]
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
json.dump({"slot_bias_s": s_aa, "rows": rows_out},
          open("/tmp/build/final-timing.json", "w"), indent=1)
for r in rows_out:
    print(f"{r['build']:48s} {r['sign_p']:10.2e}")
