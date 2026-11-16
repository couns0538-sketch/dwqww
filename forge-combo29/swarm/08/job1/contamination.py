#!/usr/bin/env python3
"""contamination.py — compares the first (contaminated: a stray run_job1.sh from my own hung first attempt
re-ran concurrently from 21:16 to 21:19) timing files with the clean re-run (raw2), run under a guard that
refused to start unless no other engine process existed and load < 0.5.
Prints, per run, median/p99/max for both, so the reader can see how much the contamination moved them.
"""
import json
import os
import sys

B = sys.argv[1] if len(sys.argv) > 1 else "."


def load(p):
    with open(p) as fh:
        return [json.loads(l) for l in fh if l.strip()]


def pct(v, p):
    s = sorted(v)
    if not s:
        return float("nan")
    k = (len(s) - 1) * p / 100.0
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


pairs = [("job1/raw/base_mt50_a.jsonl", "job1/raw2/base_a.jsonl", "movetime 50 baseline A"),
         ("job1/raw/mt500.jsonl", "job1/raw2/mt500.jsonl", "movetime 500"),
         ("job1/raw/tc1000.jsonl", "job1/raw2/tc1000.jsonl", "wtime 1000 inc 10"),
         ("job1/raw/tc10000.jsonl", "job1/raw2/tc10000.jsonl", "wtime 10000 inc 100")]

print("| run | first run n | first median | first p99 | first max | clean n | clean median | clean p99 | clean max | median moved by |")
print("|---|---|---|---|---|---|---|---|---|---|")
for old, new, lab in pairs:
    po, pn = os.path.join(B, old), os.path.join(B, new)
    if not (os.path.exists(po) and os.path.exists(pn)):
        print("| %s | (a file is missing) | | | | | | | | |" % lab)
        continue
    wo = [r["wall_ms"] for r in load(po)]
    wn = [r["wall_ms"] for r in load(pn)]
    print("| %s | %d | %.1f | %.1f | %.1f | %d | %.1f | %.1f | %.1f | %+.1f ms |" %
          (lab, len(wo), pct(wo, 50), pct(wo, 99), max(wo),
           len(wn), pct(wn, 50), pct(wn, 99), max(wn), pct(wn, 50) - pct(wo, 50)))
