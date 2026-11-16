job 3b prediction (own commit, before the first counted run; never edited)
2026-11-16T17:47:50Z

Runs C0..C6 as the job file lists, counter build (counters.patch.txt applied to clean 6b98f2170),
O and G, depth 12, S14 plus the named capture-futility settings.

1. C1 (CaptureFutilityBase 230, defaults otherwise) on O:
   - the largest L with pruned[L] > 0 is L = 5. Kill: 4 or lower, or any prune at L = 6 (job 2 already
     fixes pruned[6] = 0 on O: C2/B3 was an exact identity), or no prunes at all.
   - the share of all prunes at L <= 2 is 60 % or more. Kill: below 40 %.
2. C1 on G:
   - the largest L with pruned[L] > 0 is L = 6 (B3 differs from B0 in 50 rows of G, so L = 6 prunes
     exist; CFD = 6 caps it there). Kill: pruned[6] = 0.
   - the share of all prunes at L <= 2 is 50 % or more. Kill: below 30 %.
3. C4 (Multiplier 100) on O: BOTH C5 (CFD 5) and C6 (CFD 9) differ from C4 in rows. With the smaller
   multiplier the per-ply cost drops (L=6 needs e >= 830 instead of 1730), so L = 6 prunes should appear
   under C4 and vanish under C5; deeper L sites (7..9, e >= 1130) should also fire. Kill: C5 or C6
   row-identical to C4 on all 200 positions of O.
4. The plant (C0, Base 0): every pruned[L] = 0 on both sets. Kill: any pruned entry > 0.
5. Known answer 2 (gate arithmetic): both mismatch counts are 0 in every counted run.
   Kill: any nonzero mismatch count.
