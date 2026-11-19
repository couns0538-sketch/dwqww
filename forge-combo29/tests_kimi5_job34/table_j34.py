#!/usr/bin/env python3
"""kimi5 job 34 Step 4 table (prints how many records it read).
Rows: all F; pivW & stale W; pivW & fresh W; not pivW; pivM & stale M; pivM & fresh M; pivC;
none; in check; lmr_depth 0,1,2,3; fired with a stale NONZERO W; fired with a stale NONZERO M;
then P RAISED=1, 0, -1. Columns: records, BEATS, BEATS per 1,000 with a 95% Wilson interval,
D1 and D2 side by side. Then the declared readings.
Usage: table_j34.py <out.txt> <f_d1_glob> <f_d2_glob> <p_d1_glob> <p_d2_glob>
"""
import glob
import json
import sys

OUT = sys.argv[1]
F_D1, F_D2, P_D1, P_D2 = sys.argv[2:6]

def load(pat):
    recs = []
    for f in sorted(glob.glob(pat)):
        recs += [json.loads(l) for l in open(f)]
    return recs

f1, f2, p1, p2 = load(F_D1), load(F_D2), load(P_D1), load(P_D2)
lines = []
def w(s=""):
    lines.append(s)

w(f"records read: F D1 {len(f1)}, F D2 {len(f2)}, P D1 {len(p1)}, P D2 {len(p2)}")
w(f"noscore: F D1 {sum(r['noscore'] for r in f1)}, F D2 {sum(r['noscore'] for r in f2)}, "
  f"P D1 {sum(r['noscore'] for r in p1)}, P D2 {sum(r['noscore'] for r in p2)}")

def wilson(b, n):
    if n == 0:
        return (0.0, 0.0, 0.0)
    z = 1.959964
    ph = b / n
    den = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / den
    half = z * ((ph * (1 - ph) + z * z / (4 * n)) / n) ** 0.5 / den
    return (1000 * ph, 1000 * max(0.0, c - half), 1000 * min(1.0, c + half))

def sel(recs, pred):
    return [r for r in recs if pred(r)]

F_ROWS = [
    ("all F", lambda r: True),
    ("pivW & stale W", lambda r: r["p"][1] == "1" and r["s"][1] == "1"),
    ("pivW & fresh W", lambda r: r["p"][1] == "1" and r["s"][1] == "0"),
    ("not pivW", lambda r: r["p"][1] == "0"),
    ("pivM & stale M", lambda r: r["p"][0] == "1" and r["s"][0] == "1"),
    ("pivM & fresh M", lambda r: r["p"][0] == "1" and r["s"][0] == "0"),
    ("pivC", lambda r: r["p"][2] == "1"),
    ("none", lambda r: r["p"] == "000"),
    ("in check", lambda r: r["k"] == 1),
    ("lmr_depth 0", lambda r: r["l"] == 0),
    ("lmr_depth 1", lambda r: r["l"] == 1),
    ("lmr_depth 2", lambda r: r["l"] == 2),
    ("lmr_depth 3", lambda r: r["l"] == 3),
    ("stale NONZERO W", lambda r: r["s"][1] == "1" and r["w"] != 0),
    ("stale NONZERO M", lambda r: r["s"][0] == "1" and r["m"] != 0),
]
P_ROWS = [("P RAISED=1", lambda r: r["r"] == 1), ("P RAISED=0", lambda r: r["r"] == 0),
          ("P RAISED=-1", lambda r: r["r"] == -1)]

def emit(title, rows, d1, d2):
    w(f"\n{title}")
    w(f"{'row':22s} | {'recs':>6s} | {'D1 beats':>9s} | {'D1 per1000 [95% Wilson]':>26s} | {'D2 beats':>9s} | {'D2 per1000 [95% Wilson]':>26s}")
    out = {}
    for name, pred in rows:
        s1, s2 = sel(d1, pred), sel(d2, pred)
        b1, b2 = sum(r["beats"] for r in s1), sum(r["beats"] for r in s2)
        r1 = wilson(b1, len(s1))
        r2 = wilson(b2, len(s2))
        w(f"{name:22s} | {len(s1):6d} | {b1:9d} | {r1[0]:7.1f} [{r1[1]:7.1f},{r1[2]:7.1f}] | {b2:9d} | {r2[0]:7.1f} [{r2[1]:7.1f},{r2[2]:7.1f}]")
        out[name] = (len(s1), b1, r1, len(s2), b2, r2)
    return out

fa = emit("F records (fired prunes)", F_ROWS, f1, f2)
pa = emit("P records (every 400th not-fired eligible test)", P_ROWS, p1, p2)

w("\nReadings (D2 decides, D1 printed beside it):")
f_all = fa["all F"]
p_all3 = (sum(pa[n][3] for n, _ in P_ROWS), sum(pa[n][4] for n, _ in P_ROWS))
p_rate = wilson(p_all3[1], p_all3[0])
w(f"- THE RULE SELECTS when all-F D2 per1000 <= half of the P records' (three rows together):")
w(f"  all F D2 {f_all[5][0]:.1f} vs P together D2 {p_rate[0]:.1f} (half {p_rate[0]/2:.1f}) "
  f"[P: {p_all3[1]}/{p_all3[0]}]")
w(f"  -> {'THE RULE SELECTS' if f_all[5][0] <= p_rate[0]/2 else 'THE RULE DOES NOT SELECT'}")

def carried(stale, fresh, label):
    ns, bs, rs, nf, bf, rf = stale[3], stale[4], stale[5], fresh[3], fresh[4], fresh[5]
    ratio = rs[0] / rf[0] if rf[0] else float("inf")
    overlap = not (rs[1] > rf[2] or rf[1] > rs[2])
    if ratio >= 1.5 and not overlap:
        v = f"{label} IS WORSE"
    elif ratio <= 1.2:
        v = f"{label} IS NOT WORSE"
    else:
        v = f"{label}: UNCLEAR"
    w(f"- {label}: stale {rs[0]:.1f} [{rs[1]:.1f},{rs[2]:.1f}] (D1 {stale[2][0]:.1f}) vs fresh "
      f"{rf[0]:.1f} [{rf[1]:.1f},{rf[2]:.1f}] (D1 {fresh[2][0]:.1f}); ratio {ratio:.2f}, "
      f"intervals {'overlap' if overlap else 'disjoint'} -> {v}")
    return ratio

carried(fa["pivW & stale W"], fa["pivW & fresh W"], "CARRIED (W)")
carried(fa["pivM & stale M"], fa["pivM & fresh M"], "CARRIED (M)")

with open(OUT, "w") as fh:
    fh.write("\n".join(lines) + "\n")
print("\n".join(lines))
