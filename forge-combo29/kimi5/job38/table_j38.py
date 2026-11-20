#!/usr/bin/env python3
"""Job 38 Step 5: the price list. Prints how many records it read.

Rows: F, P RAISED 1/0/-1 (job 34's committed oracle files), Q, S, N captures,
N quiet checks, W cause L, W cause F, W without a hidden quiet (job 38 oracle),
then the splits. Columns: class total on R (K2 cell from s2/cnt_R.prc.log),
records, BEATS, BEATS per 1,000 with 95% Wilson interval, PRICE =
class total / 1,200 * BEATS share. D2 decides, D1 printed beside it.
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
J34 = os.path.join(HERE, "..", "..", "tests_kimi5_job34", "oracle")

def load(path):
    with open(path) as f:
        rows = [json.loads(l) for l in f]
    print(f"records read: {path} {len(rows)}")
    return rows

def wilson(k, n, z=1.959964):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    c = p + z * z / (2 * n)
    w = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (p, max(0.0, (c - w) / den), min(1.0, (c + w) / den))

# ---- K2 class totals on R from the counting copy's PRC lines (positional fields) ----
FIELDS = "B T QP QPc Q Q1 FE F Fc SR S Sc Spv NR NRc NRq NRp CF NS N Nc Nq Npv L Lc Lpv X WL WF HL HF HLc HFc HP HC W0".split()
tot = {k: 0 for k in FIELDS}
nprc = 0
for line in open(os.path.join(HERE, "s2", "cnt_R.prc.log")):
    if "PRC" not in line:
        continue
    vals = line.split("PRC", 1)[1].split()
    assert len(vals) == len(FIELDS), f"PRC field count {len(vals)}"
    nprc += 1
    for k, v in zip(FIELDS, vals):
        tot[k] += int(v)
print(f"PRC lines read: {nprc}")
print("K2 totals on R: " + " ".join(f"{k}={tot[k]}" for k in ["Q", "S", "Nc", "Nq", "WL", "WF", "F", "W0"]))

# ---- inputs ----
q1 = load(os.path.join(HERE, "oracle", "q_d1_all.jsonl")); q2 = load(os.path.join(HERE, "oracle", "q_d2_all.jsonl"))
s1 = load(os.path.join(HERE, "oracle", "s_d1_all.jsonl")); s2 = load(os.path.join(HERE, "oracle", "s_d2_all.jsonl"))
n1 = load(os.path.join(HERE, "oracle", "n_d1_all.jsonl")); n2 = load(os.path.join(HERE, "oracle", "n_d2_all.jsonl"))
w1 = load(os.path.join(HERE, "oracle", "w_d1_all.jsonl")); w2 = load(os.path.join(HERE, "oracle", "w_d2_all.jsonl"))
f1 = load(os.path.join(J34, "f_d1_all.jsonl")); f2 = load(os.path.join(J34, "f_d2_all.jsonl"))
p1 = load(os.path.join(J34, "p_d1_all.jsonl")); p2 = load(os.path.join(J34, "p_d2_all.jsonl"))
for r in w1 + w2:
    if r["n"] == 0:
        assert r["beats"] is None, "n=0 W record must have no BEATS"

def beats(rows):
    return sum(1 for r in rows if r["beats"])

def cell(rows_d1, rows_d2, total=None):
    k1, k2, n = beats(rows_d1), beats(rows_d2), len(rows_d2)
    p1_, lo1, hi1 = wilson(k1, len(rows_d1))
    p2_, lo2, hi2 = wilson(k2, n)
    price = (total / 1200 * p2_) if total is not None and n else None
    return dict(n=n, k1=k1, k2=k2, p1=p1_ * 1000, lo1=lo1 * 1000, hi1=hi1 * 1000,
                p2=p2_ * 1000, lo2=lo2 * 1000, hi2=hi2 * 1000, price=price)

def fmt(name, c, total=None):
    t = f"{total:>10}" if isinstance(total, int) else f"{'—':>10}"
    pr = f"{c['price']:9.2f}" if c["price"] is not None else f"{'—':>9}"
    return (f"{name:<26}|{t} |{c['n']:>6} |{c['k1']:>6} |{c['p1']:>7.1f} [{c['lo1']:>6.1f},{c['hi1']:>6.1f}] "
            f"|{c['k2']:>6} |{c['p2']:>7.1f} [{c['lo2']:>6.1f},{c['hi2']:>6.1f}] |{pr}")

print("\nrow                       | class total|  recs |D1 beat| D1 per1000 [95% Wilson]   |D2 beat| D2 per1000 [95% Wilson]   | D2 price")
MAIN = {}
w1h = [r for r in w1 if r["n"] >= 1]; w2h = [r for r in w2 if r["n"] >= 1]
rows_spec = [
    ("F (job 34)", f1, f2, tot["F"]),
    ("P RAISED=1 (job 34)", [r for r in p1 if r["r"] == 1], [r for r in p2 if r["r"] == 1], None),
    ("P RAISED=0 (job 34)", [r for r in p1 if r["r"] == 0], [r for r in p2 if r["r"] == 0], None),
    ("P RAISED=-1 (job 34)", [r for r in p1 if r["r"] == -1], [r for r in p2 if r["r"] == -1], None),
    ("Q", q1, q2, tot["Q"]),
    ("S", s1, s2, tot["S"]),
    ("N captures", [r for r in n1 if r["t"] == "c"], [r for r in n2 if r["t"] == "c"], tot["Nc"]),
    ("N quiet checks", [r for r in n1 if r["t"] == "q"], [r for r in n2 if r["t"] == "q"], tot["Nq"]),
    ("W cause L", [r for r in w1h if r["c"] == "L"], [r for r in w2h if r["c"] == "L"], tot["WL"]),
    ("W cause F", [r for r in w1h if r["c"] == "F"], [r for r in w2h if r["c"] == "F"], tot["WF"]),
    ("W no hidden quiet", [r for r in w1 if r["n"] == 0], [r for r in w2 if r["n"] == 0], tot["W0"]),
]
for name, a, b, t in rows_spec:
    c = cell(a, b, t)
    MAIN[name] = c
    print(fmt(name, c, t))

print("\n== splits (records/BEATS/per-1,000 only) ==")
def split(title, pairs):
    print(title)
    for name, a, b in pairs:
        c = cell(a, b)
        print(fmt("  " + name, c))
    return {name: cell(a, b) for name, a, b in pairs}

PV = {}
for nm, a, b in (("Q", q1, q2), ("S", s1, s2), ("N", n1, n2), ("W", w1h, w2h)):
    PV[nm] = split(f"-- {nm} by PV node (W: records with a hidden quiet) --",
                   [(f"{nm} PV", [r for r in a if r["p"] == 1], [r for r in b if r["p"] == 1]),
                    (f"{nm} non-PV", [r for r in a if r["p"] == 0], [r for r in b if r["p"] == 0])])
for nm, a, b in (("S", s1, s2), ("N", n1, n2)):
    split(f"-- {nm} by in check --",
          [(f"{nm} in check", [r for r in a if r["k"] == 1], [r for r in b if r["k"] == 1]),
           (f"{nm} not in check", [r for r in a if r["k"] == 0], [r for r in b if r["k"] == 0])])
for nm, a, b in (("Q", q1, q2), ("S", s1, s2)):
    split(f"-- {nm} by lmr_depth --",
          [(f"{nm} lmr 0-1", [r for r in a if r["l"] <= 1], [r for r in b if r["l"] <= 1]),
           (f"{nm} lmr 2-3", [r for r in a if 2 <= r["l"] <= 3], [r for r in b if 2 <= r["l"] <= 3]),
           (f"{nm} lmr 4+", [r for r in a if r["l"] >= 4], [r for r in b if r["l"] >= 4])])
split("-- W by depth (records with a hidden quiet) --",
      [("W d 1-2", [r for r in w1h if r["d"] <= 2], [r for r in w2h if r["d"] <= 2]),
       ("W d 3-4", [r for r in w1h if 3 <= r["d"] <= 4], [r for r in w2h if 3 <= r["d"] <= 4]),
       ("W d 5+", [r for r in w1h if r["d"] >= 5], [r for r in w2h if r["d"] >= 5])])
split("-- W by number of hidden quiets --",
      [("W hq 1-5", [r for r in w1h if r["n"] <= 5], [r for r in w2h if r["n"] <= 5]),
       ("W hq 6-20", [r for r in w1h if 6 <= r["n"] <= 20], [r for r in w2h if 6 <= r["n"] <= 20]),
       ("W hq >20", [r for r in w1h if r["n"] > 20], [r for r in w2h if r["n"] > 20])])

print("\n== readings (D2 decides; D1 printed beside) ==")
pp = cell(p1, p2)
half = pp["p2"] / 2
print(f"P records pooled: {pp['n']} read, D2 BEATS {pp['k2']} = {pp['p2']:.1f}/1000 (D1 {pp['p1']:.1f}); half = {half:.2f}/1000")
for nm in ("Q", "S", "N captures", "N quiet checks"):
    c = MAIN[nm]
    verdict = "THE RULE SELECTS" if c["p2"] <= half else "THE RULE DOES NOT SELECT"
    print(f"- {nm}: D2 {c['p2']:.1f}/1000 (D1 {c['p1']:.1f}) vs half of P {half:.1f} -> {verdict}")
race = [(nm, MAIN[nm]) for nm in ("F (job 34)", "Q", "S", "N captures", "N quiet checks", "W cause L", "W cause F")]
print("- THE DEAREST CLASS, order of all seven by D2 price:")
for i, (nm, c) in enumerate(sorted(race, key=lambda x: -x[1]["price"]), 1):
    print(f"    {i}. {nm}: price {c['price']:.2f} (total/1200 x {c['p2']:.1f}/1000)")
print("- PV DEARER:")
for nm in ("Q", "S", "N", "W"):
    pv, npv = PV[nm][f"{nm} PV"], PV[nm][f"{nm} non-PV"]
    ratio = pv["p2"] / npv["p2"] if npv["p2"] > 0 else float("inf")
    disjoint = pv["lo2"] > npv["hi2"] or npv["lo2"] > pv["hi2"]
    if ratio >= 1.5 and disjoint:
        v = "PV IS DEARER"
    elif ratio <= 1.2:
        v = "PV IS NOT DEARER"
    else:
        v = "UNCLEAR"
    print(f"    {nm}: PV {pv['p2']:.1f} [{pv['lo2']:.1f},{pv['hi2']:.1f}] vs non-PV {npv['p2']:.1f} [{npv['lo2']:.1f},{npv['hi2']:.1f}] (D2); "
          f"D1 {pv['p1']:.1f} vs {npv['p1']:.1f}; ratio {ratio:.2f}, intervals {'disjoint' if disjoint else 'overlap'} -> {v}")
