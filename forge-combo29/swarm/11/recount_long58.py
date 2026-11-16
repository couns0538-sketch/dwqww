#!/usr/bin/env python3
"""recount_long58.py LSDIR — seat 11's INDEPENDENT recount of deepseek6's REPORT_deepseek6_long58.md.

Reads ONLY the raw files (runs/*.rows, plan.tsv). deepseek6's table58.py was not read or
imported; this is written from the report's stated rule:
    sum   = total nodes over the 100 rows of a run
    ratio = run sum / S14 base sum
    best moves changed = rows where the run's bestmove differs from the base's

Checks every number the report claims:
  A. the base run twice is identical and sums to 12,377,717
  B. all 32 settings have both a -c and a +c run (64 runs)
  C. each run has 100 rows
  D. |ratio-1| for each setting; the reported top-10 ranking and the 0.0100..0.1914 range
  E. "all 32 alive" at the report's own threshold (|ratio-1| > 0.001)
  F. best moves changed is 6..33 per run
  G. SingularMargin's two ratios are 1.1914 and 0.8220
"""
import csv, os, sys

LS = sys.argv[1]
RUNS = os.path.join(LS, "runs")


def read_rows(path):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("|")
            if len(parts) != 3:
                return None, f"malformed row: {line!r}"
            rows.append((int(parts[0]), int(parts[1]), parts[2]))
    return rows, None


def load(name):
    p = os.path.join(RUNS, name + ".rows")
    if not os.path.exists(p):
        return None
    rows, err = read_rows(p)
    return rows


fail = []
def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{('  — ' + detail) if detail else ''}")
    if not ok:
        fail.append(name)


print("=== A. the base twice ===")
b1, b2 = load("BASE1"), load("BASE2")
if b1 is None or b2 is None:
    print("  MEASUREMENT FAILED: runs/BASE1.rows or BASE2.rows missing or unreadable.")
    print("  No verdict is given: a missing raw file is never a result.")
    sys.exit(2)
if not b1:
    print("  MEASUREMENT FAILED: BASE1.rows parsed to zero rows.")
    sys.exit(2)
s1 = sum(r[1] for r in b1)
s2 = sum(r[1] for r in b2)
print(f"  BASE1 sum {s1}, BASE2 sum {s2}, rows {len(b1) if b1 else 0}/{len(b2) if b2 else 0}")
check("base sums to 12,377,717", s1 == 12377717, f"got {s1}")
check("base is reproducible (both runs equal)",
      b1 == b2, "row-for-row identical" if b1 == b2 else "rows differ")

print("\n=== C. every run has 100 rows ===")
bad_rows = []
for name in ("BASE1", "BASE2"):
    pass
for fn in sorted(os.listdir(RUNS)):
    if not fn.endswith(".rows"):
        continue
    rows = read_rows(os.path.join(RUNS, fn))[0]
    if rows is None or len(rows) != 100:
        bad_rows.append((fn, len(rows) if rows else "unreadable"))
check("all runs have exactly 100 rows", not bad_rows, str(bad_rows[:5]))

print("\n=== B. 32 settings, two ends each ===")
plan = []
with open(os.path.join(LS, "plan.tsv")) as f:
    header = None
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if header is None:
            header = parts          # first non-comment line is the column header
            continue
        plan.append(parts)
settings = sorted({p[0] for p in plan if p and p[0]})
print(f"  plan.tsv lists {len(plan)} rows, {len(settings)} distinct settings")
missing = []
for s in settings:
    for end in ("m", "p"):
        if not os.path.exists(os.path.join(RUNS, f"{s}_{end}.rows")):
            missing.append(f"{s}_{end}")
check("every setting has both a -c and +c run", not missing, str(missing))
check("32 distinct settings", len(settings) == 32, f"got {len(settings)}")

print("\n=== D. ratios and ranking ===")
base_moves = {r[0]: r[2] for r in b1}
res = []
for s in settings:
    for end, sign in (("m", -1), ("p", 1)):
        rows = load(f"{s}_{end}")
        if rows is None:
            continue
        total = sum(r[1] for r in rows)
        ratio = total / s1
        changed = sum(1 for r in rows if base_moves.get(r[0]) != r[2])
        res.append((s, end, total, ratio, changed))

dev = {}
for s, end, total, ratio, changed in res:
    dev.setdefault(s, {})[end] = ratio
largest = sorted(((s, abs(v["p"] - 1), abs(v["m"] - 1)) for s, v in dev.items() if len(v) == 2),
                 key=lambda t: -(max(t[1], t[2])))
print("  setting                        -c ratio   +c ratio   largest |dev|")
for s, dp, dm in largest:
    print(f"  {s:30} {dev[s]['m']:9.4f} {dev[s]['p']:9.4f} {max(dp,dm):12.4f}")

top10_reported = ["SingularMargin", "LmrQuietDivisor", "AspirationDelta", "SingularDepth",
                  "LmrCutoffThreshold", "FutilityMultiplier", "IirDepth",
                  "HistoryPruneMultiplier", "FutilityBase", "HistoryBonusMax"]
top10_mine = [s for s, _, _ in largest[:10]]
print(f"\n  reported top-10: {top10_reported}")
print(f"  my       top-10: {top10_mine}")
check("the top-10 ranking matches the report", top10_mine == top10_reported)

mx = max(max(dp, dm) for _, dp, dm in largest)
mn = min(max(dp, dm) for _, dp, dm in largest)
print(f"\n  largest |dev| range: {mn:.4f} .. {mx:.4f}   (report says 0.0100 .. 0.1914)")
check("max |dev| is 0.1914", abs(mx - 0.1914) < 0.0001, f"got {mx:.4f}")
check("min |dev| is 0.0100", abs(mn - 0.0100) < 0.0001, f"got {mn:.4f}")

print("\n=== E. are all 32 alive at the report's 0.1 % threshold? ===")
dead = [s for s, dp, dm in largest if max(dp, dm) <= 0.001]
check("all 32 alive (|ratio-1| > 0.001)", not dead, str(dead))

print("\n=== F. best moves changed ===")
ch = [c for _, _, _, _, c in res]
print(f"  changed per run: min {min(ch)}, max {max(ch)}   (report says 6..33)")
check("changed within 6..33", min(ch) >= 6 and max(ch) <= 33, f"min {min(ch)} max {max(ch)}")

print("\n=== G. SingularMargin ===")
sm = dev.get("SingularMargin", {})
print(f"  -c {sm.get('m')}, +c {sm.get('p')}   (report says 1.1914 and 0.8220)")
check("SingularMargin -c is 1.1914", abs(sm.get("m", 0) - 1.1914) < 0.0001)
check("SingularMargin +c is 0.8220", abs(sm.get("p", 0) - 0.8220) < 0.0001)

print(f"\n=== verdict: {len(fail)} failed check(s) ===")
if fail:
    print("NOT matching the report on: " + ", ".join(fail))
    sys.exit(1)
else:
    print("every checked number in REPORT_deepseek6_long58.md equals what its raw files give.")
    sys.exit(0)
