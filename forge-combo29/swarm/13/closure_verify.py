#!/usr/bin/env python3
"""Recompute every aggregate in MOVE_GENERATION_CLOSED.md from the committed files.

A closure note is worthless if its totals are typed by hand, so this script produces them and the
note quotes its output. Run: python3 closure_verify.py
"""
import json
import os

SETS = {
    "job1  R_1301 (synthetic)": "job1/R_1301.fens",
    "job1b R_1311 (synthetic)": "job1b/R_1311.fens",
    "job2  special500 (edge cases)": "job2/special500.fens",
    "job3  all230 (R+G)": "job3/all230.fens",
    "job4  R200 (synthetic)": "job4/R200.fens",
    "job6  G200 (real game)": "job6/G200_spread.fens",
}
allf = set()
total = 0
print("| set | positions |")
print("|---|---|")
for name, path in SETS.items():
    fs = [l.strip() for l in open(path) if l.strip()]
    total += len(fs)
    allf |= set(fs)
    print("| %s | %d |" % (name, len(fs)))
print()
print("sum of set sizes:", total)
print("distinct FENs:", len(allf))

pairs = 0
for job, keys in (("job1", ["base_none"]), ("job1b", ["base_none"]),
                  ("job2", ["base_none"]), ("job3", ["base_none"])):
    pass
# totals-granularity pairs, read from the comparison files' own summary lines
def total_line(path, label):
    for line in open(path):
        if line.startswith(label):
            return int(line.split(":")[1].strip())
    return None

t = {}
for job, path, label in (
    ("job1", "job1/comparison_hardened.md", "TOTAL pairs actually compared (both sides OK):"),
    ("job1b", "job1b/comparison.md", "TOTAL pairs actually compared (both sides OK):"),
    ("job2", "job2/comparison.md", "TOTAL pairs actually compared (both sides OK):"),
    ("job3", "job3/comparison.md", "TOTAL pairs actually compared (both sides OK):"),
):
    t[job] = total_line(path, label)
print()
print("totals-granularity pairs (read from each comparison.md):")
for k, v in t.items():
    print("  %-6s %s" % (k, v))
pairs_total = sum(v for v in t.values() if v)
print("  TOTAL   %d" % pairs_total)

print()
print("divide-granularity root moves (read from each JSON summary):")
div = {}
for job, f, key in (("job2 d2", "job2/out_divide/VERDICT.md", None),
                    ("job4 d4", "job4/pc_pc20.json", "root_moves_compared"),
                    ("job6 d4", "job6/pc_pc20.json", "root_moves_compared")):
    if key:
        s = json.load(open(f))["summary"]
        div[job] = s[key]
        print("  %-8s %d" % (job, s[key]))
# job2 divide count: 494 positions
import re
txt = open("job2/out_divide/VERDICT.md").read()
m = re.search(r"positions differing in root move set or counts: \*\*(\d+) of (\d+)\*\*", txt)
if m:
    div["job2 d2"] = int(m.group(2))
    print("  job2 d2  %s (from VERDICT.md: %s of %s differed)" % (m.group(2), m.group(1), m.group(2)))
div_total = sum(div.values())
print("  TOTAL    %d" % div_total)

print()
print("differences found anywhere:", 0 if all(
    x == 0 for x in [
        int(re.search(r"TOTAL differing pairs: (\d+)", open("job2/comparison.md").read()).group(1)),
        int(re.search(r"TOTAL differing pairs: (\d+)", open("job1/comparison_hardened.md").read()).group(1)),
        int(re.search(r"TOTAL differing pairs: (\d+)", open("job3/comparison.md").read()).group(1)),
        int(re.search(r"TOTAL differing pairs: (\d+)", open("job1b/comparison.md").read()).group(1)),
        json.load(open("job4/pc_pc20.json"))["summary"]["positions_differing"],
        json.load(open("job6/pc_pc20.json"))["summary"]["positions_differing"],
        int(m.group(1)) if m else 1,
    ]) else "NOT ALL ZERO")
