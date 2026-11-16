long 19 prediction (the two bundle builds for glmflash5's file 28) -- own commit before the first counted run

1. Bundle (a) = ChecksLmr (d33b27ca) + LmrFine (f7bf3f43), applied in that order, zero fuzz:
   S14 rows on O and G equal 9,500,069 / 18,466,239 with the first-3 pattern (both extra patches
   inert at their defaults); V on O = 8,565,026 exactly; T1 on O = 10,170,054 and on G =
   19,269,858 exactly. Kill: any differing sum.
2. V + T1 on O: the two effects compose approximately multiplicatively:
   9,500,069 x 1.0705 (T1) x 0.9016 (V) = about 9,165,000. Kill: outside [8,700,000, 9,700,000].
   V + T1 on G: 18,466,239 x (19,269,858/18,466,239 = 1.0435) x (14,633,520/18,466,239 = 0.7925
   -- V's G ratio from long 18) = about 15,290,000. Kill: outside [14,300,000, 16,400,000].
3. Bundle (b) = ChecksLmr + SoundArms (57524c71) + SoundRegret (10208495) + SoundSteps
   (07713c3b) -- the working order (Regret must precede Steps: its uci hunks expect Arms's lines
   and Steps inserts before Regret's anchor; the plain job-5 order Arms,Steps,Regret FAILS its
   dry run, disclosed): S14 rows on O and G equal the known sums (three patches inert at their
   defaults); P (SoundPvArm 1 + SoundStepMask 1) on G at depth 12 about 17,500,000 (the d10
   sanitizer ratio 0.967 from my long-8 addendum carried to d12). Kill: outside
   [16,500,000, 18,400,000]. V + P on O about 8,565,026 x 0.967 = about 8,280,000; kill outside
   [7,700,000, 8,560,000]. V + P on G about 14,633,520 x 0.967 = about 14,150,000; kill outside
   [13,100,000, 14,630,000].
4. Both bundles' pins: bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609. Kill otherwise.
