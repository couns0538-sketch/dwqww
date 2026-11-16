long 20 prediction (CheckExtensionDepth 3,4,5,6,7,10,12 on the plain base) -- own commit before the first counted run

1. The hard known: my CED 5 rows on O equal the peer session's E2 rows (tests_deepseek6_job5,
   cex_E2_O.txt's per-position nodes; its run is the same setting on the same base) position by
   position. Kill: any differing row (or a missing/unreadable E2 table -- then the comparison is
   declared impossible and the item's own sums stand alone).
2. CED 10 and CED 12 on O are both below CED 8's 9,015,167, and CED 12 <= CED 10 (fewer
   extensions, smaller tree, mostly monotone at the top end). Kill: CED10 >= 9,015,167 or
   CED12 > CED10.
3. CED 3..7 on O all lie in [9,015,167, 9,500,069]. Kill: any outside.
4. On G: CED 10 and 12 below my long-18 CED-8 value 15,120,379; CED 3..7 within
   [15,120,379, 18,466,239]. Kill: any outside.
5. The G curve reproduces the O shape: every G sum for CED 3..12 sits strictly between its O
   counterpart x 1.85 and x 2.05 (the O/G node ratio at S14 is 1.944). Kill: any outside.
