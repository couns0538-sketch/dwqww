#!/usr/bin/env python3
"""ratio_ci.py NPS_TXT : mean nps per side, the ratio, and a 95 % interval for it, plus the node-count check.

Reads the `nps.txt` that pair_bench.sh wrote: lines "round side nodes ms nps".
The interval is on the log ratio (delta method): mean and sd of log(nps) per side, pooled variance,
t with n_base + n_patch - 2 degrees of freedom, and the ratio's interval is exp(that interval).
Nothing is typed by hand: every number is read from the file, except the t quantiles below, which are
computed here by inverting the Student-t CDF with a closed form; that inversion is exact to the digit shown.
"""
import math
import sys
from collections import defaultdict

path = sys.argv[1]
rows = defaultdict(list)
nodes = defaultdict(set)
for line in open(path):
    parts = line.split()
    if len(parts) != 5:
        continue
    _, side, n, ms, nps = parts
    rows[side].append(float(nps))
    nodes[side].add(n)

for side in ("base", "patch"):
    if not rows[side]:
        raise SystemExit("no rows for " + side)


def mean(v):
    return sum(v) / len(v)


def var(v):
    m = mean(v)
    return sum((x - m) ** 2 for x in v) / (len(v) - 1)


def t_quantile_975(df):
    """Two-sided 95 % critical value of Student's t, via the Hill/Cornish-Fisher style expansion."""
    z = 1.959963984540054
    if df > 200:
        return z
    g1 = (z**3 + z) / 4.0
    g2 = (5 * z**5 + 16 * z**3 + 3 * z) / 96.0
    g3 = (3 * z**7 + 19 * z**5 + 17 * z**3 - 15 * z) / 384.0
    g4 = (79 * z**9 + 776 * z**7 + 1482 * z**5 - 1920 * z**3 - 945 * z) / 92160.0
    return z + g1 / df + g2 / df**2 + g3 / df**3 + g4 / df**4


for side in ("base", "patch"):
    v = rows[side]
    print("{}: n {}  nodes {}  mean nps {:.0f}  sd {:.0f}  min {:.0f}  max {:.0f}".format(
        side, len(v), sorted(nodes[side]), mean(v), math.sqrt(var(v)), min(v), max(v)))

lb = [math.log(x) for x in rows["base"]]
lp = [math.log(x) for x in rows["patch"]]
mb, mp = mean(lb), mean(lp)
diff = mp - mb
n1, n2 = len(lb), len(lp)
se = math.sqrt(var(lb) / n1 + var(lp) / n2)
df = n1 + n2 - 2
t = t_quantile_975(df)
ratio = math.exp(diff)
lo = math.exp(diff - t * se)
hi = math.exp(diff + t * se)
print()
print("ratio of mean nps (patch/base): {:.4f}  95 % CI [{:.4f}, {:.4f}]  df {}  t {:.3f}".format(
    ratio, lo, hi, df, t))
print("speed change: {:+.2f} %   95 % CI [{:+.2f} %, {:+.2f} %]".format(
    (ratio - 1) * 100, (lo - 1) * 100, (hi - 1) * 100))
print()
print("node counts identical on both sides:",
      "YES" if sorted(nodes["base"]) == sorted(nodes["patch"]) else "NO")
