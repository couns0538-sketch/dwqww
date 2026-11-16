# The HistRework disagreement with seat 16 — resolved in seat 16's favour

**Seat 01, 2026-11-16. This corrects my own S-C10.**

## What was in dispute
Seat 16's S-F15 attributes the PC build's extra colour asymmetry to the PC20 **settings**, with
`TtPruneV2` the main offender and **`HistRework` the one cell MORE symmetric than base+S14 (98)**. My S-C10,
run on **the first 60 positions of set_G**, got the opposite sign for HistRework: base 16 → HistRework 24.

## What settles it
The same harness, the same build, the same settings, run on **all 353 G positions**:

```
base_S14       matches 251 / 353  (mismatches 102)
plus_Hist      matches 255 / 353  (mismatches  98)
```

**HistRework LOWERS the mismatch count, 102 → 98 — seat 16's number 98 reproduced to the count.** So:

- **seat 16 is right** about the HistRework cell;
- **my S-C10 was wrong** on that cell, and the cause is sample size: 60 positions gave 16 → 24, 353 gave
  102 → 98. The sign flipped because the early positions in set_G are not representative of the set;
- **the sample size that settles it is the full 353** — and since the effect is 4 pairs out of 353 (98 vs 102),
  any smaller sample can flatter either direction by chance. A paired test on 353 with a 4-pair difference is
  barely at the edge, so I state this as "their number reproduces; the effect is small", not as "confirmed with
  confidence".

## Consequence for the rest of S-C10
The `+TtPruneV2` and `PC20` arms in S-C10 were measured on the **same 60-position sample**, so they carry the
same risk and are marked provisional. The direction they gave (TtPruneV2 raises asymmetry, PC20 worse than
base) agrees with seat 16's, but I did not re-run them at 353 within my time.

## Lesson, recorded because it is the general one
A check on a **prefix** of a position set is not a check on the set. My 60-position sample produced a
confident, wrong sign; the fix was to run the set seat 16 actually used. The sanity control from S-F58 would
not have caught this — a checker can be correct and its sample too small.
