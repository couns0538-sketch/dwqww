long 39 prediction (the dead settings swept across their ranges) -- own commit before the first counted run

1. QsSeeMargin 0, 20, 60, 80 on O are EXACT identities (9,500,069; 200/200 rows) -- the whole
   0..99 band is one search (SeeValue are multiples of 100). Kill: any changed row.
2. QsSeeMargin 100 on O = 9,768,507 EXACTLY (the known). Kill: otherwise.
3. QsSeeMargin 500 (the option's maximum) on O differs from S14. Kill: equality.
4. CaptureFutilityMultiplier (0, 125, 375, 500, 1000) and CaptureFutilityDepth (0, 3, 9, 12, 15)
   are EXACT identities on O at every value -- the capture-futility block is gated off by
   CaptureFutilityBase = 0, so nothing in their ranges can act. Kill: any changed row in any of
   the ten runs.
5. The bisection on QsSeeMargin: every value in 41..99 is dead; the dead/alive boundary sits
   between 99 and 100, so the smallest change from the default 40 that moves the O sum is +60
   (to exactly 100). Kill: any alive value below 100, or a dead value at or above 100.
6. QsSeeMargin 100 on G differs from the S14 G sum (it moved O). Kill: equality.
7. The answer: of the three, ONLY QsSeeMargin is alive anywhere in its tuner range, and only at
   values >= 100; the two capture-futility settings are dead across their entire ranges under
   S14. Kill: contradicted by any run.
