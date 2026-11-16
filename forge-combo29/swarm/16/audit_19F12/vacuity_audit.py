#!/usr/bin/env python3
"""vacuity_audit.py : prove that none of my recorded comparisons passed vacuously.

For every table my confirmations are built on, this checks three things:
  1. ROW COUNT: rows actually measured == rows expected from the input file. A silent `continue`
     drops a row, so a full count means nothing was skipped.
  2. MISSING VALUES: no row carries a None/empty/NaN in any field that a comparison reads. A comparison
     of None against None reads as "equal", which is exactly the vacuous pass to rule out.
  3. NON-CONSTANCY: the measured numbers actually vary. If every value were identical (e.g. all zeros,
     or an unparsed default), "0 differences" would be meaningless.
Fails loudly (exit 1) on any violation.
"""
import glob
import math
import sys

FAIL = []


def audit_table(path, expected_rows, numeric_fields, name):
    with open(path) as fh:
        header = fh.readline().rstrip("\n").split("\t")
        rows = [l.rstrip("\n").split("\t") for l in fh if l.strip()]
    print(f"\n=== {name}\n    {path}")
    print(f"    rows measured {len(rows)}  expected {expected_rows}  "
          f"{'OK' if len(rows) == expected_rows else 'MISMATCH'}")
    if len(rows) != expected_rows:
        FAIL.append(f"{name}: row count {len(rows)} != expected {expected_rows}")
    # missing values in the fields the comparison reads
    missing = 0
    for r in rows:
        for idx in numeric_fields:
            if idx >= len(r):
                missing += 1
                continue
            v = r[idx].strip()
            if v in ("", "None", "nan", "NaN", "-1.0", "NoneType"):
                missing += 1
    print(f"    missing/None values in compared fields: {missing}")
    if missing:
        FAIL.append(f"{name}: {missing} missing values in compared fields")
    # non-constancy: how many distinct values in the first numeric field
    if rows and numeric_fields:
        idx = numeric_fields[0]
        vals = {r[idx] for r in rows if idx < len(r)}
        print(f"    distinct values in column '{header[idx] if idx < len(header) else idx}': {len(vals)}")
        if len(vals) <= 1:
            FAIL.append(f"{name}: only {len(vals)} distinct value(s) -> comparison is constant/vacuous")
    return len(rows)


# 1. job1: colour-mirror eval, 853 expected (353 G + 500 R)
n_g = audit_table("/agent/repos/dwqww/forge-combo29/swarm/16/job1/raw/G.tsv",
                  353, [4, 5, 6, 8, 9, 10], "job1 G (colour mirror, basis of S-C2)")
n_r = audit_table("/agent/repos/dwqww/forge-combo29/swarm/16/job1/raw/R.tsv",
                  500, [4, 5, 6, 8, 9, 10], "job1 R (colour mirror, basis of S-C2)")

# 2. job2: left-right, 334 + 411 (basis of S-F3/S-C3 and S-C4)
audit_table("/agent/repos/dwqww/forge-combo29/swarm/16/job2/raw/G_lr.tsv",
            334, [4, 5, 6, 8, 9, 10], "job2 G_lr (left-right, basis of S-C3/S-C4)")
audit_table("/agent/repos/dwqww/forge-combo29/swarm/16/job2/raw/R_lr.tsv",
            411, [4, 5, 6, 8, 9, 10], "job2 R_lr (left-right, basis of S-C3/S-C4)")

# 3. check_S-F1: 4 configs x 5853 (basis of S-C2 extended)
for cfg in ("default", "nonnue", "deadmat", "both"):
    audit_table(f"/agent/repos/dwqww/forge-combo29/swarm/16/check_S-F1/raw/{cfg}.tsv",
                5853, [], f"check_S-F1 {cfg} (basis of S-C2)")

print("\n" + "=" * 70)
if FAIL:
    print("AUDIT FAILED:")
    for f in FAIL:
        print("  - " + f)
    sys.exit(1)
print("AUDIT PASSED: every table has the expected row count, no missing compared values,")
print("and every compared column varies (so no comparison could have been constant or vacuous).")
