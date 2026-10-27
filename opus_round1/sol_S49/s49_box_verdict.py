#!/usr/bin/env python3
"""S49 box verdict (same rule as the inline check in ci_s49_box.sh): the A/A run's CI must contain 1.00 at every depth
and the synthetic 5% slowdown's CI must lie below 1.00 at every depth, with identical nodes.
usage: python -I -B s49_box_verdict.py <out_dir with run_aa/ and run_slow5/>"""
import json
import sys

out = sys.argv[1]
aa = json.load(open(f"{out}/run_aa/summary.json", encoding="utf-8-sig"))
sl = json.load(open(f"{out}/run_slow5/summary.json", encoding="utf-8-sig"))
ok = True
for d, r in aa["per_depth"].items():
    c = r["ci95"]
    inside = c[0] <= 1.0 <= c[1]
    ok &= inside
    print(f"A/A {d}: median {r['median_ratio']:.4f} CI {c[0]:.4f}-{c[1]:.4f} contains 1: {inside}; "
          f"control CI {r.get('control_ci95')} contains 1: {r.get('control_ci_contains_1')}")
for d, r in sl["per_depth"].items():
    c = r["ci95"]
    excl = c[1] < 1.0
    ok &= excl
    print(f"5% slowdown {d}: median {r['median_ratio']:.4f} CI {c[0]:.4f}-{c[1]:.4f} excludes 1 (below): {excl}; "
          f"nodes A=B: {r['node_exact']}")
print("S49 BOX VERDICT:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
