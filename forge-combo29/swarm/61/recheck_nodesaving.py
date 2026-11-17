#!/usr/bin/env python3
"""Re-derive the PC20 node-saving row: 8.7% fewer nodes, CI [0.8752, 0.9528], n=464.

The report's significance table states:

    | PC20 node count, aggregate | 0.9131 | [0.8752, 0.9528] | ~60% | REAL pooled saving (8.7%) |

`raw_result.txt` commits all 464 per-position node pairs, so the point estimate AND an interval
can both be recomputed rather than quoted.  Two interval constructions are reported because the
source does not say which produced [0.8752, 0.9528]:
  (a) paired bootstrap over positions, resampling the POOLED ratio;
  (b) the mean-of-ln ratio with a normal interval.
A claim is only supported if the committed data reproduces the published interval under at least
one honest construction, so both are printed with the method named.
"""
import math
import random
import re
import statistics as st
import sys

PATH = "evidence/pc20_raw_464.txt"
REPORT_POINT = 0.9131
REPORT_CI = (0.8752, 0.9528)
REPORT_SAVING = 8.69
REPORT_SHARE = (278, 464)

random.seed(20261117)


def load():
    rows = []
    pat = re.compile(r"\s*(\d+) S14\s+(\d+) ms/\s*(\d+) n \| PC20\s+(\d+) ms/\s*(\d+) n \| ratio (\S+)")
    for ln in open(PATH):
        m = pat.match(ln)
        if m:
            rows.append({"s14n": int(m.group(3)), "pcn": int(m.group(5))})
    return rows


rows = load()
ns14 = sum(r["s14n"] for r in rows)
npcn = sum(r["pcn"] for r in rows)
pooled = npcn / ns14
per = [r["pcn"] / r["s14n"] for r in rows]
lns = [math.log(x) for x in per]
mean_ln = st.mean(lns)
se = st.stdev(lns) / math.sqrt(len(lns))
mean_ln_ratio = math.exp(mean_ln)
normal_ci = (math.exp(mean_ln - 1.96 * se), math.exp(mean_ln + 1.96 * se))

# paired bootstrap on the pooled ratio
boot = []
n = len(rows)
for _ in range(10000):
    idx = [random.randrange(n) for _ in range(n)]
    a = sum(rows[i]["pcn"] for i in idx)
    b = sum(rows[i]["s14n"] for i in idx)
    boot.append(a / b)
boot.sort()
boot_ci = (boot[int(0.025 * len(boot))], boot[int(0.975 * len(boot))])

# bootstrap on the mean-of-ln
boot_ln = []
for _ in range(10000):
    idx = [random.randrange(n) for _ in range(n)]
    boot_ln.append(math.exp(st.mean(lns[i] for i in idx)))
boot_ln.sort()
boot_ln_ci = (boot_ln[int(0.025 * len(boot_ln))], boot_ln[int(0.975 * len(boot_ln))])

print("rows parsed: %d" % len(rows))
print()
print("  pooled node ratio      : %.4f  (saving %.2f%%)" % (pooled, (1 - pooled) * 100))
print("  mean-of-ln node ratio  : %.4f" % mean_ln_ratio)
print("  median node ratio      : %.4f" % st.median(per))
print("  bootstrap 95%% (pooled) : [%.4f, %.4f]" % boot_ci)
print("  bootstrap 95%% (meanln) : [%.4f, %.4f]" % boot_ln_ci)
print("  normal    95%% (meanln) : [%.4f, %.4f]" % normal_ci)
print("  sign share (fewer)     : %d / %d = %.1f%%"
      % (sum(1 for x in per if x < 1), len(per), 100 * sum(1 for x in per if x < 1) / len(per)))
print()

checks = 0
agree = 0
disagree = []


def check(label, ok, detail):
    global checks, agree
    checks += 1
    if ok:
        agree += 1
        print("  AGREE     %-50s %s" % (label, detail))
    else:
        disagree.append(label)
        print("  DISAGREE  %-50s %s" % (label, detail))


check("pooled point estimate 0.9131",
      abs(pooled - REPORT_POINT) < 5e-5, "mine %.4f" % pooled)
check("saving 8.69%",
      abs((1 - pooled) * 100 - REPORT_SAVING) < 0.01, "mine %.2f%%" % ((1 - pooled) * 100))
check("sign share 278/464",
      sum(1 for x in per if x < 1) == REPORT_SHARE[0],
      "mine %d/%d" % (sum(1 for x in per if x < 1), len(per)))

# the published interval: does ANY honest construction land on it?
cands = {"pooled-bootstrap": boot_ci, "meanln-bootstrap": boot_ln_ci, "meanln-normal": normal_ci}
best_name, best = min(cands.items(),
                      key=lambda kv: abs(kv[1][0] - REPORT_CI[0]) + abs(kv[1][1] - REPORT_CI[1]))
lo_b, hi_b = best
gap = abs(lo_b - REPORT_CI[0]) + abs(hi_b - REPORT_CI[1])
check("published CI reproduced (any construction, within 0.01 total)",
      gap < 0.01,
      "closest is %s: [%.4f, %.4f] vs published [%.4f, %.4f] (total gap %.4f)"
      % (best_name, lo_b, hi_b, REPORT_CI[0], REPORT_CI[1], gap))

check("published interval excludes 1.0 and so does every recomputed one",
      all(ci[1] < 1.0 for ci in cands.values()),
      "highest upper bound %.4f (published %.4f)" % (max(ci[1] for ci in cands.values()), REPORT_CI[1]))

print("\nrows examined: %d" % checks)
print("agree: %d / %d" % (agree, checks))
if disagree:
    print("HEADLINE DISAGREEMENTS:")
    for d in disagree:
        print("  - %s" % d)
sys.exit(0 if not disagree else 1)
