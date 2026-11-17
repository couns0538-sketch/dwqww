#!/usr/bin/env python3
"""kimi5 job15 Step 2: sum the ALQ counter lines of one run's full output.
Usage: sum_alq.py <run_full.txt>
Prints searches summed and totals. Layout of a line:
info string ALQ v1 raised_pv N raised_nonpv N reduced d3..d11 (9 nums)
reduced_other N qs_seen k1..k16 (16 nums) qs_seen_17plus N qs_skipped N
qs_kept_recapture N
"""
import sys

raised_pv = raised_nonpv = 0
reduced = [0] * 9
reduced_other = 0
qs_seen = [0] * 16
qs_seen_17plus = 0
qs_skipped = qs_kept_recapture = 0
n = 0
with open(sys.argv[1]) as f:
    for line in f:
        if "info string ALQ v1" not in line:
            continue
        n += 1
        p = line.split()
        i = p.index("v1") + 1
        assert p[i] == "raised_pv" and p[i + 2] == "raised_nonpv"
        raised_pv += int(p[i + 1])
        raised_nonpv += int(p[i + 3])
        i += 4
        assert p[i] == "reduced"
        for d in range(9):
            reduced[d] += int(p[i + 1 + d])
        i += 10
        assert p[i] == "reduced_other"
        reduced_other += int(p[i + 1])
        i += 2
        assert p[i] == "qs_seen"
        for k in range(16):
            qs_seen[k] += int(p[i + 1 + k])
        i += 17
        assert p[i] == "qs_seen_17plus" and p[i + 2] == "qs_skipped" and p[i + 4] == "qs_kept_recapture"
        qs_seen_17plus += int(p[i + 1])
        qs_skipped += int(p[i + 3])
        qs_kept_recapture += int(p[i + 5])
print(f"searches summed: {n}")
print(f"raised_pv {raised_pv} raised_nonpv {raised_nonpv}")
print(f"reduced[d=3..11] {' '.join(str(x) for x in reduced)} reduced_other {reduced_other}")
print(f"qs_seen[k=1..16] {' '.join(str(x) for x in qs_seen)} qs_seen_17plus {qs_seen_17plus}")
print(f"qs_skipped {qs_skipped} qs_kept_recapture {qs_kept_recapture}")
