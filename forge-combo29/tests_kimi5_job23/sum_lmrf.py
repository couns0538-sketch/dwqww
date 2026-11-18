#!/usr/bin/env python3
"""kimi5 job 23 step 3 totals: sums the LMRF counter lines of the counting runs,
prints how many it summed, and checks the file-23 known answers:
  fh gives r-1 only from its two positive bands, never r+1 / other / a moved
  non-positive history; fhr never "other", its band-outsides are zero; the classes
  of each form add up to the reductions counted.
Usage: sum_lmrf.py <full.txt> [<full.txt> ...]  (run from tests_kimi5_job23/)"""
import json
import sys

NAMES = ["total"] + \
    [f"fh_{c}_{s}" for c in ("rm1", "r", "rp1", "other") for s in ("neg", "zero", "pos")] + \
    [f"fhr_{c}_{s}" for c in ("rm1", "r", "rp1", "other") for s in ("neg", "zero", "pos")] + \
    ["fh_rm1_b1", "fh_rm1_b2", "fh_rm1_out", "fhr_rm1_b1", "fhr_rm1_b2", "fhr_rm1_out",
     "fhr_rp1_b1", "fhr_rp1_b2", "fhr_rp1_out"]

def main():
    files = sys.argv[1:]
    tot = [0] * 34
    nlines = 0
    for path in files:
        with open(path) as f:
            for line in f:
                if line.startswith("LMRF "):
                    vals = [int(x) for x in line.split()[1:]]
                    assert len(vals) == 34, (path, line)
                    for i, v in enumerate(vals):
                        tot[i] += v
                    nlines += 1
    print(f"searches summed: {nlines} over {len(files)} files")
    d = dict(zip(NAMES, tot))
    for k, v in d.items():
        print(f"{k:14s} {v}")
    total = d["total"]
    fh_sum = sum(d[f"fh_{c}_{s}"] for c in ("rm1", "r", "rp1", "other") for s in ("neg", "zero", "pos"))
    fhr_sum = sum(d[f"fhr_{c}_{s}"] for c in ("rm1", "r", "rp1", "other") for s in ("neg", "zero", "pos"))
    print(f"fh classes add up: {fh_sum} == total {total}: {fh_sum == total}")
    print(f"fhr classes add up: {fhr_sum} == total {total}: {fhr_sum == total}")
    bad = []
    for key in ("fh_rp1_neg", "fh_rp1_zero", "fh_rp1_pos",
                "fh_other_neg", "fh_other_zero", "fh_other_pos",
                "fh_rm1_neg", "fh_rm1_zero", "fhr_other_neg", "fhr_other_zero", "fhr_other_pos",
                "fh_rm1_out", "fhr_rm1_out", "fhr_rp1_out"):
        if d[key] != 0:
            bad.append((key, d[key]))
    print("forbidden classes nonzero:", bad if bad else "none (as required)")
    fh_rm1 = d["fh_rm1_neg"] + d["fh_rm1_zero"] + d["fh_rm1_pos"]
    fhr_rm1 = d["fhr_rm1_neg"] + d["fhr_rm1_zero"] + d["fhr_rm1_pos"]
    fhr_rp1 = d["fhr_rp1_neg"] + d["fhr_rp1_zero"] + d["fhr_rp1_pos"]
    print(f"fh r-1 total {fh_rm1} == band sum {d['fh_rm1_b1'] + d['fh_rm1_b2']}: "
          f"{fh_rm1 == d['fh_rm1_b1'] + d['fh_rm1_b2']}")
    print(f"fhr r-1 total {fhr_rm1} == band sum {d['fhr_rm1_b1'] + d['fhr_rm1_b2']}: "
          f"{fhr_rm1 == d['fhr_rm1_b1'] + d['fhr_rm1_b2']}")
    print(f"fhr r+1 total {fhr_rp1} == band sum {d['fhr_rp1_b1'] + d['fhr_rp1_b2']}: "
          f"{fhr_rp1 == d['fhr_rp1_b1'] + d['fhr_rp1_b2']}")
    if total:
        print(f"share in fh moving bands:  {fh_rm1}/{total} = {fh_rm1 / total:.4f}")
        print(f"share in fhr moving bands: {fhr_rm1 + fhr_rp1}/{total} = {(fhr_rm1 + fhr_rp1) / total:.4f}")

if __name__ == "__main__":
    main()
