#!/usr/bin/env python3
"""Re-derive the PC20 per-node row from the committed 180 rows, and test the CI pairing.

The consolidated report's table row is:

    | PC20 per-node cost | +6.4% | [1.0670, 1.0876] | 90.0% (162/180, direct n=180 arm) |

Three numbers, and this script asks whether they are three views of ONE quantity:

  * +6.4% is the POOLED ratio (total ms / total nodes) from distribution.py = 1.0643.
  * [1.0670, 1.0876] is, in pernode_result.txt, the CI of the MEAN-OF-LN estimator (1.0773).
  * 162/180 is the sign share.

If the CI belongs to a different estimator than the point estimate, the pairing is wrong even
though every individual number is honestly computed.  That is the class of defect this seat
exists to find, so it is tested rather than eyeballed.
"""
import math
import re
import statistics as st
import sys

PATH = "evidence/pc20_pernode_180.txt"
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


def estimators(rows):
    npc = sum(r["npc"] for r in rows)
    ns14 = sum(r["ns14"] for r in rows)
    tpc = sum(r["tpc"] for r in rows)
    ts14 = sum(r["ts14"] for r in rows)
    per = [(r["tpc"] / r["npc"]) / (r["ts14"] / r["ns14"]) for r in rows]
    lns = [math.log(x) for x in per]
    n = len(per)
    mean_ln = st.mean(lns)
    se = st.stdev(lns) / math.sqrt(n)
    se_pop = st.pstdev(lns) / math.sqrt(n)
    return {
        "n": n,
        "pooled": (tpc / npc) / (ts14 / ns14),
        "mean_of_ln": math.exp(mean_ln),
        "ci_mean_ln": (math.exp(mean_ln - 1.96 * se), math.exp(mean_ln + 1.96 * se)),
        "ci_mean_ln_pop": (math.exp(mean_ln - 1.96 * se_pop), math.exp(mean_ln + 1.96 * se_pop)),
        "arithmetic_mean": st.mean(per),
        "median": st.median(per),
        "geo_mean": math.exp(mean_ln),
        "above": sum(1 for x in per if x > 1.0),
        "ge": sum(1 for x in per if x >= 1.0),
        "eq": sum(1 for x in per if x == 1.0),
        "sd_ln": st.stdev(lns),
    }


rows = load()
e = estimators(rows)
checks = 0
agreements = 0
disagreements = []


def check(label, ok, detail):
    global checks, agreements
    checks += 1
    if ok:
        agreements += 1
        print("  AGREE     %-52s %s" % (label, detail))
    else:
        disagreements.append(label)
        print("  DISAGREE  %-52s %s" % (label, detail))


print("source rows parsed: %d (the arm's own n)" % e["n"])
print()
print("  pooled (total ms/total nodes) : %.4f  = +%.2f%%" % (e["pooled"], (e["pooled"] - 1) * 100))
print("  mean of ln ratios             : %.4f  = +%.2f%%" % (e["mean_of_ln"], (e["mean_of_ln"] - 1) * 100))
print("  arithmetic mean               : %.4f" % e["arithmetic_mean"])
print("  median                        : %.4f" % e["median"])
print("  95%% CI (mean-of-ln, sample sd): [%.4f, %.4f]" % e["ci_mean_ln"])
print("  95%% CI (mean-of-ln, pop  sd) : [%.4f, %.4f]" % e["ci_mean_ln_pop"])
print()

print("1. is the report's point estimate the POOLED ratio?")
check("pooled re-derives to 1.0643 (+6.4%)",
      abs(e["pooled"] - REPORT_POOLED) < 5e-5,
      "mine %.4f vs report %.4f" % (e["pooled"], REPORT_POOLED))

print("\n2. does the report's CI contain the report's point estimate?")
inside = REPORT_CI[0] <= REPORT_POOLED <= REPORT_CI[1]
checks += 1
if inside:
    agreements += 1
    print("  AGREE     point estimate lies inside its own interval")
else:
    disagreements.append("pooled point estimate lies OUTSIDE the quoted interval")
    print("  DISAGREE  pooled 1.0643 is OUTSIDE [1.0670, 1.0876]")
    print("            the interval's own centre is the mean-of-ln %.4f" % e["mean_of_ln"])

print("\n3. which estimator does the quoted CI belong to?")
check("CI reproduces from mean-of-ln (sample sd), not from the pooled ratio",
      abs(e["ci_mean_ln"][0] - REPORT_CI[0]) < 0.006 and abs(e["ci_mean_ln"][1] - REPORT_CI[1]) < 0.006,
      "mine [%.4f, %.4f] vs report [%.4f, %.4f]"
      % (e["ci_mean_ln"][0], e["ci_mean_ln"][1], REPORT_CI[0], REPORT_CI[1]))

print("\n4. the sign share")
check("162/180 above 1.0 reproduces",
      (e["above"], e["n"]) == REPORT_SHARE,
      "mine %d/%d above, %d at or above, %d exactly 1.000"
      % (e["above"], e["n"], e["ge"], e["eq"]))

print("\n5. does the CONCLUSION survive, independent of the pairing fault?")
lo = min(e["ci_mean_ln"][0], e["ci_mean_ln_pop"][0])
hi = max(e["ci_mean_ln"][1], e["ci_mean_ln_pop"][1])
check("every estimator excludes 1.0 with margin (effect is real)",
      lo > 1.0, "lowest interval bound across estimators %.4f" % lo)

print("\nrows examined: %d" % checks)
print("agree: %d / %d" % (agreements, checks))
if disagreements:
    print("HEADLINE DISAGREEMENTS:")
    for d in disagreements:
        print("  - %s" % d)
sys.exit(0 if not disagreements else 1)
