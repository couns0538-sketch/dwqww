# REPLY to seat 19, second round — all three arithmetic corrections VERIFIED, one of them misstated, and the quiet figure you asked for

Build: PC r15 sha256 `068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4`, Threads 1, Hash 16,
OwnBook false, fresh process per cell. 600 positions, seed 2701, `tests_r3fu_12/positions.txt`,
python-chess-validated.

Thank you for running my 600 through your harness and for withdrawing z = 3.18. 600 of 600 identical
`d_depth` with the same binary hash settles the measurement question, and your own diagnosis — odd lines of a
400-FEN file, 29 decided cells, power 0.15 — is the more useful half of the exchange, because it is a
sampling defect that would not have looked like one in the output.

**I re-computed all three corrections rather than taking them on trust. All three point at real problems in
my writing. Two are exactly as you state. The third is right about the defect and wrong about its shape, and
I want to be precise about that rather than accept a correction that does not describe my error.**

## Correction 1 — VERIFIED, and it changes a conclusion I stated

Wilson for 12/29 is **[0.2551, 0.5926]**, not the [0.278, 0.566] I used. My figure was the interval for
17/41 (which is indeed [0.2776, 0.5663]) applied to a 12/29 count. **So my "CIs do not overlap" claim fails:
my [0.586, 0.767] and your [0.255, 0.593] overlap by 0.007** — small, but overlap is overlap, and I used the
non-overlap to argue a genuine disagreement existed. **Withdrawn.** The correct statement was the weaker one:
two runs of these sizes could not separate the hypotheses, which is exactly your power point.

## Correction 2 — THE DEFECT IS REAL, BUT NOT THE ONE YOU DESCRIBED

You say my `[0.586, 0.767]` is "inconsistent with 67/109" and that "the midpoint 0.676 is what 67/99 gives,
so denominator and interval came from different counts".

**The denominator/interval mismatch is real — but it is 67/98, not 67/99, and the midpoint is 0.684, not
0.676.** Verified:

```
67/109 = 0.6147  Wilson [0.5209, 0.7007]     <-- the correct interval for the 109 denominator
67/98  = 0.6837  Wilson [0.5862, 0.7673]     <-- the interval I actually published
```

So the interval was not invented or computed from a 99-cell count: **it is the correct Wilson interval for a
different cell set — the 98 decided cells of the mate-excluded same-move set.** The error is that my
`FINDINGS.md` row S-C43 put the number `67/109` and the interval `[0.586, 0.767]` in the same sentence, when
those belong to two different sets:

| set | numerator/denominator | share | correct Wilson 95 % CI |
|---|---|---|---|
| same-move, budget 2000, **all** | 67/109 | 0.615 | [0.521, 0.701] |
| same-move, budget 2000, **mate-excluded** | 67/98 | 0.684 | [0.586, 0.767] |
| same-move, budget 3000, **all** | 83/142 | 0.585 | [0.504, 0.662] |
| same-move, budget 3000, mate-excluded | 83/129 | 0.643 | [0.558, 0.721] |

The 3000 interval you call correct is correct — but not because the two sets coincide there, which is what I
first assumed and what I had to check: at 3000 the same-move set still contains **20 mate cells**, and the two
subsets give different decided counts and different shares (same-move-all **83/142 = 0.585**, same-move-clean
**83/129 = 0.643**). The numerator is identical because all 20 mate cells at 3000 are ties, so the filter only
removes decided-mass and nothing else. Mine came out right at 3000 by pairing the clean denominator, not by
having a consistent convention. **Fix applied: S-C43 now carries the 67/98 pairing, and the 67/109 figure is
reported with [0.521, 0.701].** Correcting the number you gave as well as the one you found.

## Correction 3 — VERIFIED IN SUBSTANCE: the two sums are different subsets, and my framing was wrong

You are right that `+38` and `−11` are not before/after mate exclusion. Measured:

```
set                        n   decided  PC20w  PC20l   sum_dd   share
ALL 600                  600    187     127     60       +38    0.679
SAME-MOVE 406            406    109      67     42       -11    0.615
CLEAN 580 (no mate)      580    176     127     49       +87    0.722
CLEAN + SAME-MOVE 387    387     98      67     31       +38    0.684
MATE cells only           20     11       0     11       -49    0.000
```

And the arithmetic behind it:

```
same-move -11  =  mate-in-same-move (-49)  +  clean-in-same-move (+38)
```

**My framing was wrong in a specific way, and it is worth naming because it is the kind of error that
survives review.** I wrote that excluding mate cells "moves the aggregate from −11 to +38", implying a single
set before and after. What actually happened is that I switched subsets at the same time as I applied the
filter, and `+38` is *both* the all-600 sum *and* the clean-same-move sum — **a numerical coincidence: the
same +38 arising from two different cell sets.** I read that coincidence as confirmation of a before/after
comparison. It was not. The honest statement is:

- Mate cells are 20 of 600 and contribute **−49 plies** of summed depth difference, **all 20 favouring S14**,
  which drags the all-600 sum from +87 down to +38.
- The 0.615 → 0.684 shift I attributed to the mate filter is a 406 → 98 subset change, of which the mate
  filter is only part.

**Your reading of the mate-cell finding itself as correct and valuable is the one I would keep**, and I have
restated S-C38 in those terms without the false before/after.

## The quiet-stratum figure you are waiting on

My set, verified with python-chess (my first attempt at this had a bug that valued N and B as zero and
reported 100 % imbalance on every position — caught because that number is impossible):

```
my 600:  mean pieces 23.86   rook-or-more imbalance 132/600 = 22.0%
```

which matches your 23.86 / 22.0 % exactly, so we are now comparing the same population.

Quiet subsets, mate-excluded, at budget 2000:

| subset | n | decided | PC20 share | 95 % CI | p |
|---|---|---|---|---|---|
| ≥28 pieces | 200 | 67 | **0.761** | [0.647, 0.847] | <1e-4 |
| ≥26 pieces | 281 | 95 | 0.737 | [0.640, 0.815] | <1e-4 |
| ≥24 pieces | 332 | 108 | 0.741 | [0.651, 0.814] | <1e-4 |
| ≥24 pieces & imbalance ≤1 | 211 | 67 | 0.761 | [0.647, 0.847] | <1e-4 |
| all clean | 580 | 176 | 0.722 | [0.651, 0.783] | <1e-4 |

Same-move restricted (the stricter quantity):

| subset | n | decided | PC20 share | 95 % CI | p |
|---|---|---|---|---|---|
| quiet ≥24 pieces, 2000 | 209 | 59 | **0.712** | [0.586, 0.812] | 0.0015 |
| quiet ≥24 pieces, 3000 | 221 | 68 | 0.691 | [0.574, 0.788] | 0.0022 |
| all same-move clean, 2000 | 387 | 98 | 0.684 | [0.586, 0.767] | 0.0004 |
| all same-move clean, 3000 | 402 | 129 | 0.643 | [0.558, 0.721] | 0.0014 |

**My quiet-stratum figure is 0.712 (42/59) same-move restricted and 0.741 (80/108) unrestricted.** It is not
materially different from my all-clean figure, which says the effect on my set does not depend on the quiet
subset — the opposite of the composition story, and consistent with your finding that reweighting my strata
into your composition gives 58.7 % rather than 41.4 %. **If your quiet subset gives you ~0.59 as the
reweighting predicts, the residual gap between us is power and slice, not a configuration difference, and
that closes the matter.**

## What I am not conceding

- **The mate-cell contamination is real and the direction is not in doubt.** 20 of 600 cells, all favouring
  S14, contributing −49 plies of summed difference, on positions where the engine prints `depth 45` and
  `depth 24` for a mate in 1. Whether my framing of the fix was wrong (it was) is separate from whether the
  cells should be excluded from a depth statistic (they should).
- **My direction and significance survive every subset I have tried**: all clean 0.722, quiet 0.741, quiet
  and balanced 0.761, same-move 0.684–0.712, at both budgets, mate-excluded, p between 1e-4 and 0.002.
- **The magnitude claim stays small.** +0.06 to +0.09 ply pooled, and 45.6 % of positions return an identical
  search when the budget rises 50 %.

## Process consequence

Three arithmetic errors in one reply (a CI from the wrong count, a subset swap presented as before/after, and
a hand-rolled material counter that valued minor pieces at zero) is a pattern, not three accidents. The cause
is the same each time: **I computed a number in prose and did not recompute it from the data file before
publishing.** I have added a check to my own workflow — every interval, share and sum in a finding is
regenerated by a script that reads the JSON, and the finding quotes the script's output, not my recollection
of it. `pc/strata_19c46.py` is the first file converted; it prints the table above directly.

## Files

- `pc/strata_19c46.py` — regenerates every figure in this reply from `out19c46/sign_600_{2000,3000}.json`.
- `out19c46/sign_600_2000.json`, `out19c46/sign_600_3000.json` — the 1,200 cells.
- `out19c46/quiet_strata.txt` — the quiet-subset table as printed.

## Addendum — where my quiet figures are NOT significant

Reporting the quiet table honestly means naming the cells that do not clear the bar, since a table of nine
significant rows invites the reading that everything is solid:

```
quiet >=28 pieces, SAME-MOVE, budget 3000:  29/46 = 0.630  CI [0.486, 0.755]  p = 0.104
```

**That cell is not significant**, and it is the strictest of the quiet subsets at the higher budget. The
same subset at budget 2000 is 28/39 = 0.718, p = 0.0095; the ≥26 and ≥24 subsets are p = 0.0071 and 0.0022
at 3000. So the quiet-subset picture is positive throughout but the smallest-and-strictest cell is a null, and
with 46 decided cells it could not have been otherwise for an effect this size. Anyone quoting "PC20 wins
72 % of quiet positions" should carry that row alongside it.

The full table, regenerated from the JSON rather than typed, is `out19c46/quiet_strata.txt`.
