#!/usr/bin/env python3
"""check_sf5.py : verify "total = clamp(hce+nnue)" and the exact-cancellation claim
from my own job-2 left-right table (745 rows), which was collected before I read the finding.
"""
import collections

rows = []
for path in ("../job2/raw/G_lr.tsv", "../job2/raw/R_lr.tsv"):
    with open(path) as fh:
        fh.readline()
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 15:
                rows.append(p)

print(f"rows: {len(rows)} (job2 left-right table: 334 G-no-castling + 411 R-no-castling)")

# P1
bad_sum = [r for r in rows if int(r[6]) != int(r[4]) + int(r[5])]
print(f"P1  total != hce+nnue : {len(bad_sum)} of {len(rows)}")
for r in bad_sum[:5]:
    print(f"    {r[2]} hce {r[4]} nnue {r[5]} total {r[6]}")

# P2 / P3
canc = []
for r in rows:
    hce_a, hce_b = int(r[4]), int(r[8])
    nn_a, nn_b = int(r[5]), int(r[9])
    tot_a, tot_b = int(r[6]), int(r[10])
    if hce_a == hce_b and nn_a == nn_b:
        continue
    if tot_a == tot_b:
        canc.append((r[2], hce_a - hce_b, nn_a - nn_b, tot_a, tot_b))

print(f"\nP2  positions where total is EXACTLY equal left-right while hce and/or nnue differ: "
      f"{len(canc)} of {len(rows)}")
exact = 0
for fen, dh, dn, ta, tb in canc:
    ok = (dh == -dn)
    exact += ok
    print(f"    {fen}")
    print(f"      dhce {dh:+5d}  dnnue {dn:+5d}  dhce+dnnue {dh+dn:+5d}  total {ta} vs {tb}"
          f"  exact negative: {ok}")
print(f"\nP3  of those, dhce == -dnnue exactly: {exact} of {len(canc)}")

# which configurations matter: does any row break once UseNNUE would be off (nnue 0)?
zero_nnue = [r for r in rows if int(r[5]) == 0 and int(r[9]) == 0]
print(f"\nrows with nnue 0 on both sides (would be UseNNUE false): {len(zero_nnue)}")
