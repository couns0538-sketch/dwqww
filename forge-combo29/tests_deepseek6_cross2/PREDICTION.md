cross 2 prediction (kimi5's job-10 REGRET probe runs reproduced) -- own commit before the counted runs

Scope: the four probe runs (defaults-O, S14-O, S14-G, defaults-G -- its agg_r5/r6/r7/r8) and the
four controls on O (QsFutilityMargin 0/400, QsSeeMargin 0/200 -- its agg_c_fut0/fut400/see0/see200),
all with FORGE_QS_STEPS=1 + FORGE_QS_REGRET=1 at the patch's default probe cadence (48/256/700).

1. Pins on my probe build: 312866 / 862329 / 4865609. Kill: otherwise.
2. The eight runs' rows differ from the plain rows for the same settings (the probe DISTURBS the
   search -- kimi5's stated +51.5/+48.4 percent at the defaults... my disturbance will be
   different in size but present): every probe run's node sum differs from its undisturbed
   counterpart (r5 vs 12,573,318 etc.). Kill: any probe run with EXACTLY its undisturbed sum.
3. My aggregated tables equal kimi5's eight agg files on every labeled line but the SUMMED source
   line, including the PART 3 PROBES section: the seen counts (777,675 / 1,880,428 / 2,131,480 on
   r5), the probe nodes (43,743 on r5), the per-class probe/missed/cut/bound tables, the by-q
   tables and their identities. Kill: ANY differing number.
4. The probes' cadence identities hold (the seen counts == the class-cell sums, e.g. r5's fut
   probes 16,106 = the sum of its six margin cells). Kill: any mismatch.
