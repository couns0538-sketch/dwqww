# REPORT_check_S-F5 — CONFIRMS seat 06's S-F5 (area 6), seat 16

**What was asked:** check seat 06's S-F5: "`total` is clamp(hce+nnue) because `nnue_weights.inc:3` defines
`FORGE_NNUE_RESIDUAL 1`; on 3 of 764 positions the PSQT delta exactly cancelled the net delta so `total` was
bit-identical under a left-right flip while both components moved".

**The answer:** CONFIRMED, on data I had already collected before reading the finding — my own job-2
left-right table over 745 positions, from an independent harness and an independent position set.

```
P1  total != hce+nnue : 0 of 745
P2  total exactly equal left-right while hce and/or nnue differ: 3 of 745
P3  in all 3, dhce == -dnnue exactly (signed, not just in magnitude)
P4  src/eval.cpp:611  parts.total = std::clamp(handcrafted + parts.nnue, ...)
    src/nnue_weights.inc:3  #define FORGE_NNUE_RESIDUAL 1
```

The three positions, with signs:

```
4b3/pp2kpbp/4p1p1/4N3/8/1PN4P/1PPr1PP1/4R1K1 w - - 0 1   dhce  -53  dnnue  +53   total -176 vs -176
8/8/3n4/1Pk5/5P2/1N1K4/8/8 b - - 0 1                     dhce   +5  dnnue   -5   total -150 vs -150
2k5/5R2/6p1/6P1/1n2N1n1/6R1/r7/5K2 b - - 32 109           dhce  +44  dnnue  -44   total -302 vs -302
```

Two of the three cancel in the +hce/−nnue direction and one in the −hce/+nnue direction, so the cancellation
is not a one-way artifact.

**How sure:** high. The count (3) matches the finding's own count (3), the arithmetic is exact, and the code
line is where the finding says it is. The denominator differs (my 745 vs its 764) because we used different
position sets; the phenomenon is the same and the rate is comparable (0.40 % vs 0.39 %).

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-release/forge   (the build that produced ../job2/raw/*_lr.tsv)
sha256  e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
bench 11 312866  bench 13 862329  bench 16 3024920  go perft 5 4865609   (all equal)
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| P1 total == hce+nnue | done | `raw_check.txt` | 0 of 745 violate |
| P2 count of exact cancellations | done | `raw_check.txt` | 3 of 745 (0.40 %) |
| P3 signed exactness | done | `raw_check.txt` | 3 of 3 have dhce == −dnnue |
| P4 code lines | done | `src/eval.cpp:604-611`, `src/nnue_weights.inc:1-4` (read at those lines) | both present as described |
| re-run with a NEW position set | not needed | — | the point is that an independent, earlier dataset agrees |
| sanitizer run | NOT done (not asked) | — | would say nothing about this claim |

## Findings

`S-C4 | CONFIRMS S-F5 | check_S-F5/raw_check.txt (again: `python3 check_S-F5/check_sf5.py`) | on my own 745-position left-right table, total == hce+nnue on 745/745 and exactly 3 positions have total bit-identical under a left-right flip while both components move, each with dhce == -dnnue exactly (two of one sign, one of the other); src/eval.cpp:611 is the clamp and src/nnue_weights.inc:3 is FORGE_NNUE_RESIDUAL 1 |`

## Suspicions, not proven

- With `UseNNUE false` (residual path not taken) `total == nnue == 0` would hold; my table has only 1 such row,
  so I cannot say anything statistical about that configuration from this data.

## What I did NOT do

- Did not re-run with seat 06's position set; different sets are the point of an independent check.
- Did not investigate whether a near-cancellation (|dhce+dnue| == 1 or 2) is common — only the exact zeros.

## What I am NOT sure about

- Whether the clamp at `eval.cpp:611` was ever active on these positions (it binds only near mate scores).
  My |total| values here are all below 400, so the clamp never bound and the plain sum held.

## Times

`stamps.txt`, every line a `date -u`.

## Last command output

(pasted into `last_cmd.txt` at commit time)

## Last command output

```
$ git status --short
 M check_S-F5/stamps.txt
?? REPORT_check_S-F5.md
?? check_S-F5/check_sf5.py
?? check_S-F5/last_cmd.txt
?? check_S-F5/raw_check.txt
$ ls
check_S-F1
check_S-F2
check_S-F3
check_S-F5
FINDINGS.md
honesty.sh
HONESTY.txt
job0_honesty
job1
job2
job3
ownbook_check
REPORT_check_S-F1.md
REPORT_check_S-F2.md
REPORT_check_S-F3.md
REPORT_check_S-F5.md
REPORT_job1.md
REPORT_job2.md
REPORT_job3.md
REPORT_ownbook_check.md
SEAT.txt
STATUS.md
$ ls check_S-F5
check_sf5.py
last_cmd.txt
prediction.txt
raw_check.txt
stamps.txt
```
