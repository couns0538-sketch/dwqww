#!/usr/bin/env python3
"""opus_step0_verify.py - re-check the R14-cont Step 0 input md5s from the committed blobs (own code).

Step 0 (2026-11-04 09:20 Vienna) checked seven files in the working tree before any change. Two of them changed later
on purpose (PROD_SEPARATION.json regenerated, PLAN.md got the R14-cont section), so this re-check reads each file's
blob from the commit that holds the Step 0 state: aa78a56 (Job 1 committed the PC-only state as found) and, for
PLAN.md, 7636122b (the R14-cont section was appended right after Step 0). All seven files are -text or LF, so the blob
bytes are the working-tree bytes Step 0 hashed. Prints one line per file and PASS / FAIL; exit 0 only on PASS.
"""
import hashlib
import subprocess
import sys

CHECKS = [
    ('aa78a56', 'sep/overlap-production03/REPORT.json', '1607d19e2b66dbe3512d0997942523c4'),
    ('aa78a56', 'sep/segments-production02/REPORT.json', 'fcb488f8c726326e013f648e1d202760'),
    ('aa78a56', 'sep/PROD_SEPARATION.json', '04ffdcebf3cb1aee4005b76f60187458'),
    ('aa78a56', 'sep/R14B_SEPARATION.json', 'a0d35125ddf1ce471740195d6a3c7acd'),
    ('aa78a56', 'evidence/R14_OPEN_ISSUES.md', 'a485ab0705ea07b16bcba89f4d91f24e'),
    ('aa78a56', 'sep/GUARD_BAND_PLAN.md', 'b95d0b0d97bc483b98fd381849ff95fb'),
    ('7636122b', 'PLAN.md', '48effbe5f64fecb3ca68f9398981c056'),
]


def main():
    bad = 0
    for rev, path, want in CHECKS:
        blob = subprocess.run(['git', '-C', 'D:/a14', 'show', f'{rev}:{path}'], capture_output=True, check=True).stdout
        got = hashlib.md5(blob).hexdigest()
        ok = got == want
        bad += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {rev}:{path} md5 {got} (Step 0 pin {want})")
    print(f"step 0 re-check {'PASS' if not bad else 'FAIL'}: {len(CHECKS)} files, {bad} mismatches")
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
