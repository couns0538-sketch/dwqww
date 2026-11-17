#!/usr/bin/env python3
"""Re-derive the PC20 per-node row from the committed 180 rows, and test the CI pairing.

The consolidated report's row is:

    | PC20 per-node cost | +6.4% | [1.0670, 1.0876] | 90.0% (162/180, direct n=180 arm) |

Three numbers, and this script asks whether they are three views of ONE quantity:

  * +6.4% is the POOLED ratio (total ms / total nodes) = 1.0643 in the committed rows.
  * [1.0670, 1.0876] is, in pernode_result.txt, the CI of the MEAN-OF-LN estimator (1.0773).
  * 162/180 is the sign share.

EXIT CODE SEMANTICS (deliberately split, because conflating them hides faults):

  0  the measurement ran correctly: every row parsed, the per-position ratios recompute, and
     the pooled ratio is reproducible from the committed columns.
  1  the measurement is BROKEN or the data is internally inconsistent -- do not trust the row.
  2  the measurement is sound but the REPORT's row does not reproduce from it.

A disagreement with the report is data, not a crash; a harness fault is a crash.  Keeping them
in different exit codes is what lets the fault-injection test tell them apart.
"""
import math
import re
import statistics as st
import sys

PATH = "evidence/pc20_pernode_180.txt"
EXPECTED_N = 180
REPORT_POOLED = 1.0643
REPORT_CI = (1.0670, 1.0876)
REPORT_SHARE = (162, 180)


def load():
    rows = []
    pat = re.compile(r"\s*(\d+)/\s*(\d+) n (\S+) \|\s*(\d+)/\s*(\d+) ms (\S+) \| pernode (\S+)")
    for ln in open(PATH):
        m = pat.match(ln)
        if m:
            rows.append({
                "npc": int(m.group(1)), "ns14": int(m.group(2)),
                "tpc": int(m.group(4)), "ts14": int(m.group(5)),
                "pn_printed": float(m.group(7)),
            })
    return rows


rows = load()
print("source rows parsed: %d (expected %d)" % (len(rows), EXPECTED_N))

# ---- harness validity gate -------------------------------------------------
broken = []
if len(rows) != EXPECTED_N:
    broken.append("parsed %d rows, expected %d" % (len(rows), EXPECTED_N))

calc = [(r["tpc"] / r["npc"]) / (r["ts14"] / r["ns14"]) for r in rows]
mismatch = [(i, r["pn_printed"], c) for i, (r, c) in enumerate(zip(rows, calc))
            if abs(r["pn_printed"] - c) > 0.002]
if mismatch:
    broken.append("%d rows disagree with their own printed per-node ratio, first: %r"
                  % (len(mismatch), mismatch[0]))

if broken:
    print("MEASUREMENT BROKEN:")
    for b in broken:
        print("  - %s" % b)
    sys.exit(1)
print("per-position ratios recompute from the committed columns on all %d rows" % len(rows))

npc = sum(r["npc"] for r in rows)
ns14 = sum(r["ns14"] for r in rows)
tpc = sum(r["tpc"] for r in rows)
ts14 = sum(r["ts14"] for r in rows)
pooled = (tpc / npc) / (ts14 / ns14)
lns = [math.log(c) for c in calc]
mean_ln = st.mean(lns)
se = st.stdev(lns) / math.sqrt(len(lns))
ci = (math.exp(mean_ln - 1.96 * se), math.exp(mean_ln + 1.96 * se))

print()
print("  pooled (total ms/total nodes) : %.4f  = +%.2f%%" % (pooled, (pooled - 1) * 100))
print("  mean of ln ratios             : %.4f  = +%.2f%%"
      % (math.exp(mean_ln), (math.exp(mean_ln) - 1) * 100))
print("  arithmetic mean               : %.4f" % st.mean(calc))
print("  median                        : %.4f" % st.median(calc))
print("  95%% CI (mean-of-ln, sample sd): [%.4f, %.4f]" % ci)
print()

checks = 0
agree = 0
disagree = []


def check(label, ok, detail):
    global checks, agree
    checks += 1
    if ok:
        agree += 1
        print("  AGREE     %-52s %s" % (label, detail))
    else:
        disagree.append("%s (%s)" % (label, detail))
        print("  DISAGREE  %-52s %s" % (label, detail))


print("1. is the report's point estimate the POOLED ratio?")
check("pooled re-derives to 1.0643 (+6.4%)",
      abs(pooled - REPORT_POOLED) < 5e-5,
      "mine %.4f vs report %.4f" % (pooled, REPORT_POOLED))

print("\n2. does the report's CI contain the report's point estimate?")
inside = REPORT_CI[0] <= REPORT_POOLED <= REPORT_CI[1]
checks += 1
if inside:
    agree += 1
    print("  AGREE     point estimate lies inside its own interval")
else:
    disagree.append("pooled point estimate 1.0643 lies OUTSIDE [1.0670, 1.0876]")
    print("  DISAGREE  pooled 1.0643 is OUTSIDE [1.0670, 1.0876]")
    print("            the interval is centred on the mean-of-ln %.4f, not on the pooled %.4f"
          % (math.exp(mean_ln), pooled))

print("\n3. which estimator does the quoted CI belong to?")
check("CI is a mean-of-ln interval, near the published bounds",
      abs(ci[0] - REPORT_CI[0]) < 0.008 and abs(ci[1] - REPORT_CI[1]) < 0.008,
      "mine [%.4f, %.4f] vs report [%.4f, %.4f]"
      % (ci[0], ci[1], REPORT_CI[0], REPORT_CI[1]))

print("\n4. the sign share")
above = sum(1 for c in calc if c > 1.0)
check("162/180 above 1.0 reproduces",
      (above, len(rows)) == REPORT_SHARE,
      "mine %d/%d above 1.0 (%d at or above)" % (above, len(rows), sum(1 for c in calc if c >= 1.0)))

print("\n5. does the CONCLUSION survive the pairing fault?")
check("every estimator excludes 1.0 with margin (the tax is real)",
      ci[0] > 1.0, "lowest interval bound %.4f" % ci[0])

print("\nrows examined: %d" % checks)
print("agree: %d / %d" % (agree, checks))
if disagree:
    print("DISAGREEMENTS (exit 2 -- measurement sound, report row does not reproduce):")
    for d in disagree:
        print("  - %s" % d)
    sys.exit(2)
sys.exit(0)
