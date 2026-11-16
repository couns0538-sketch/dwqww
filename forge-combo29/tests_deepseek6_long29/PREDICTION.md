long 29 prediction (SENSITIVITY C: depth 14 for the sub-0.5-percent movers) -- own commit before the first counted run

The qualifying list from longs 27/28 (O ratio within 0.5 percent of 1 at depth 12): LmrNoisyDivisor
+c; LmpBase -c; HistoryPruneMultiplier -c; HistoryBonusQuadratic +c; HistoryBonusLinear +c;
HistoryBonusMax -c; NullMoveEvalDivisor -c/+c; RfpDepth -c/+c; RazorBase -c; RazorMultiplier
-c/+c; FutilityDepth +c; FutilityBase -c; FutilityMultiplier -c/+c; SeeNoisyMultiplier +c;
ProbcutMargin +c (18 non-identity runs), plus the six identity runs (QsSeeMargin +-c,
CaptureFutilityMultiplier +-c, CaptureFutilityDepth +-c) whose depth-12 trees are exactly S14's.

1. The S14 depth-14 anchor on O sums EXACTLY 21,812,100. Kill: any difference.
2. The six identity runs at depth 14 are exactly the S14 depth-14 rows on all 200 positions.
   Kill: any differing row.
3. All 18 non-identity movers stay ALIVE at depth 14 (at least one changed node each). Kill: any
   exact identity among them.
4. At least 8 of the 18 exceed the 0.5 percent band at depth 14 (small effects grow with depth).
   Kill: fewer than 3 or more than 16 of the 18 outside the band.
