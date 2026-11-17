#!/usr/bin/env python3
"""Recheck the prefetch row (section 1) from the committed 130 pairs.

Report claims:
  * pooled 1.0980 -> 9.80% slower
  * 93.1% of positions (121/130) individually slower
  * median 1.087, Q1 1.062, Q3 1.119
  * excluding the single 3.2x outlier, 7.87%
  * both builds pass four honesty pins with IDENTICAL node counts

The last one is checkable from the committed pairs directly: if the node ratio is exactly 1.0
on every pair, the per-node ratio is the time ratio and the claim is clean.  The interval is
computed two ways because the report says "tight" without naming a construction.
"""
import math
import random
import statistics as st
import sys

PATH = "evidence/prefetch_raw_pairs.txt"
report = {
    "pooled": 1.0980,
    "pct": 9.80,
    "slower": (121, 130),
    "median": 1.087,
    "q1": 1.062,
    "q3": 1.119,
    "drop_outlier": 7.87,
}

RNG = random.Random(20261117)
rows = []
with open(PATH, encoding="utf-8") as handle:
    for ln in handle:
        ln = ln.strip()
        if not ln:
            continue
        parts = [p.strip() for p in ln.split("|")]
        nc, npf = parts[0].split()[0].split("/")
        mpf, mc = parts[1].split()[0].split("/")
        rows.append((int(nc), int(npf), int(mpf), int(mc)))

n = len(rows)
per = [(r[2] / r[1]) / (r[3] / r[0]) for r in rows]
tnpc = sum(r[1] for r in rows)
tnc = sum(r[0] for r in rows)
tpc = sum(r[2] for r in rows)
tc = sum(r[3] for r in rows)
pooled = (tpc / tnpc) / (tc / tnc)


def q(v, p):
    v = sorted(v)
    i = (len(v) - 1) * p
    lo = int(i)
    hi = min(lo + 1, len(v) - 1)
    f = i - lo
    return v[lo] * (1 - f) + v[hi] * f


boot = []
for _ in range(10000):
    idx = [RNG.randrange(n) for _ in range(n)]
    a = sum(rows[i][2] for i in idx) / sum(rows[i][1] for i in idx)
    b = sum(rows[i][3] for i in idx) / sum(rows[i][0] for i in idx)
    boot.append(a / b)
boot.sort()
boot_ci = (boot[250], boot[9750])

lns = [math.log(x) for x in per]
m = st.mean(lns)
se = st.stdev(lns) / math.sqrt(n)
normal_ci = (math.exp(m - 1.96 * se), math.exp(m + 1.96 * se))

keep = [(r, p) for r, p in zip(rows, per) if p < 3.0]
tnpf2 = sum(r[1] for r, _ in keep)
tpc2 = sum(r[2] for r, _ in keep)
tnc2 = sum(r[0] for r, _ in keep)
tc2 = sum(r[3] for r, _ in keep)
drop = (tpc2 / tnpf2) / (tc2 / tnc2)

checks = 0
agree = 0
bad = []


def check(label, ok, detail):
    global checks, agree
    checks += 1
    if ok:
        agree += 1
        print("  AGREE     %-46s %s" % (label, detail))
    else:
        bad.append(label)
        print("  DISAGREE  %-46s %s" % (label, detail))


print("rows parsed: %d" % n)
print()
print("  node ratio across ALL pairs (sum/sum): %.6f" % (tnpc / tnc))
print("  pooled per-node: %.4f  (+%.2f%%)" % (pooled, (pooled - 1) * 100))
print("  median %.4f  Q1 %.4f  Q3 %.4f" % (st.median(per), q(per, .25), q(per, .75)))
print("  slower on %d/%d = %.1f%%" % (sum(1 for x in per if x > 1), n,
                                       100 * sum(1 for x in per if x > 1) / n))
print("  pooled bootstrap 95%% CI [%.4f, %.4f]" % boot_ci)
print("  mean-of-ln normal 95%% CI [%.4f, %.4f]" % normal_ci)
print("  dropping the sub-3.0 outlier (n=%d): %.4f (+%.2f%%)"
      % (len(keep), drop, (drop - 1) * 100))
print()

check("node counts identical on every pair (the control)",
      all(r[0] == r[1] for r in rows),
      "%d/%d pairs with node ratio exactly 1.0 of %d"
      % (sum(1 for r in rows if r[0] == r[1]), n, n))
check("pooled 1.0980 == 9.80% slower",
      abs(pooled - report["pooled"]) < 5e-5,
      "mine %.4f (+%.2f%%)" % (pooled, (pooled - 1) * 100))
check("slower on 121/130 = 93.1%",
      (sum(1 for x in per if x > 1), n) == report["slower"],
      "mine %d/%d" % (sum(1 for x in per if x > 1), n))
check("median 1.087", abs(st.median(per) - report["median"]) < 5e-4,
      "mine %.4f" % st.median(per))
check("Q1 1.062", abs(q(per, .25) - report["q1"]) < 5e-4, "mine %.4f" % q(per, .25))
check("Q3 1.119", abs(q(per, .75) - report["q3"]) < 5e-4, "mine %.4f" % q(per, .75))
check("excluding the 3.2x outlier gives 7.87%",
      abs((drop - 1) * 100 - report["drop_outlier"]) < 0.01,
      "mine %.2f%%" % ((drop - 1) * 100))
check("interval excludes 1.0 under both constructions",
      boot_ci[0] > 1.0 and normal_ci[0] > 1.0,
      "lowest bound %.4f" % min(boot_ci[0], normal_ci[0]))

print("\nrows examined: %d" % checks)
print("agree: %d / %d" % (agree, checks))
if bad:
    print("HEADLINE DISAGREEMENTS:")
    for b in bad:
        print("  - %s" % b)
sys.exit(0 if not bad else 1)
