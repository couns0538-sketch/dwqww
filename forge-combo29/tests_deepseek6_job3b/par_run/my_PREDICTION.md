# PREDICTION — deepseek6, job 3b (where capture futility prunes)

Written before the first counted run. Never edited after this commit.

## What C1 is

`S14 + CaptureFutilityBase 230`. The gate prunes a capture when `lmr_depth <= CaptureFutilityDepth` (6) AND
`static_eval + Base + Multiplier*lmr_depth + capture_value + history/8 <= alpha`, i.e. when the deficit
`e = alpha - (static_eval + capture_value + history/8)` is at least `Base + Multiplier*lmr_depth`
= 230 + 250*L. So the required deficit at L = 0 is 230, at L = 1 it is 480, at L = 2 it is 730.

That arithmetic is why I expect most prunes at SMALL L: every extra ply of `lmr_depth` demands another 250 cp of
deficit, which is enormous at a 12-ply search. Opus's reading says the same and asks me to count it.

## The prediction (the job asks for three things)

**1. C1 on O — the largest L with `pruned[L] > 0`: I predict L = 2.**
Kill: any L other than 2 as the largest.

**2. C1 on O and on G — the share of all prunes at L <= 2: I predict 100 % on O and 100 % on G.**
Kill: any prune at L >= 3 on either set (that would be a share below 100 %).

**3. C4 vs C5 and C6 on O (`Multiplier` 100 instead of 250, with depth 5 and 9):**
`C4 = C1 + Multiplier 100` lowers the per-ply cost to 100, so more plies qualify and more prunes happen.
I predict **both C5 and C6 differ from C4 on O in nodes** (they change `CaptureFutilityDepth`, which C4's lower
multiplier makes more likely to bind), and I predict **C6 (depth 9) differs from C4 by MORE than C5 (depth 5)
does**, because C5 tightens an already-tight limit while C6 relaxes it.
Kill: C5 or C6 equal to C4 on all 200 positions; or C5's differing-row count greater than C6's.

## Known answers I expect to be met, restated so a failure is unambiguous

- C1, O: `pruned[6] == 0` — because job 2's B3 (depth 5) was 200 of 200 identical to B0 (depth 6), and one prune
  at L = 6 would have removed nodes somewhere.
- C3, O: `pruned[7] >= 1`, and all of them in ONE position — because job 2's B4 differed from B0 on exactly one
  row, by one node.
- C1, G: `pruned[6] > 0` — because job 2's B3 differed from B0 on 50 of 353 G rows.
- Gate arithmetic, every run: `pruned_small_deficit == 0` and `gate_yes_not_pruned == 0`.
- The plant: C0 (base 0) has `pruned[L] == 0` for every L.

## What I expect the shapes to look like, so a reader can see my model

I expect the deficit distribution at small L to be broadly spread (a capture's deficit is set by the node's static
eval versus alpha and by the capture's value, not by L), and I expect `in_depth[L]` to be dominated by L = 0..6
because that is where `lmr_depth <= 6` holds. If `pruned[0]` alone carries almost everything, the reading "the
depth limit almost never binds" is exactly right; if prune counts are spread evenly over L = 0..6, the limit binds
often but the base still dominates.
