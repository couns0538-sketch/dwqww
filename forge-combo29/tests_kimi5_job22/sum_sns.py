#!/usr/bin/env python3
"""kimi5 job 22 step 3 summer: totals of the SNS v1 counter lines over ALL searches of a
counting run. Prints how many searches it summed and checks the TAKEN classes add up to
the tests run. usage: sum_sns.py <full.txt> ..."""
import re
import sys

FIELDS = ["tests", "sing", "mc", "b2", "b3", "none", "wtoday", "wnew", "wmate"]
PAT = re.compile(r"info string SNS v1 " + r" ".join(rf"{f} (\d+)" for f in FIELDS))

def summ(path):
    tot = {f: 0 for f in FIELDS}
    n = 0
    with open(path) as fh:
        for line in fh:
            m = PAT.search(line)
            if m:
                n += 1
                for f, v in zip(FIELDS, m.groups()):
                    tot[f] += int(v)
    return n, tot

grand_n = 0
for path in sys.argv[1:]:
    n, t = summ(path)
    grand_n += n
    taken = t["sing"] + t["mc"] + t["b2"] + t["b3"] + t["none"]
    ok = "OK " if taken == t["tests"] else "BAD"
    per1000 = lambda x: f"{1000.0 * x / t['tests']:.1f}" if t["tests"] else "n/a"
    print(f"{ok} {path}: searches summed {n}")
    print("   " + " ".join(f"{f} {t[f]}" for f in FIELDS))
    print(f"   taken sum {taken} vs tests {t['tests']} | per 1000 tests: mc {per1000(t['mc'])} "
          f"b2 {per1000(t['b2'])} b3 {per1000(t['b3'])} none {per1000(t['none'])} sing {per1000(t['sing'])}")
    print(f"   wtoday {per1000(t['wtoday'])} wnew {per1000(t['wnew'])} wmate {per1000(t['wmate'])} per 1000 tests")
print(f"total searches summed: {grand_n}")
