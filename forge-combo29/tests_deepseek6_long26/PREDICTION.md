long 26 prediction (long 17's counters on B_FINE under T1 and T2) -- own commit before the first counted run

1. The counter build's rows equal the plain B_FINE rows for the same settings on every position:
   T1 against job 4's runs/D2_O.rows (O) and the long-19 a_T1_G rows (G); T2 against job 4's
   runs/D3_O.rows (O) and long 5c's T2-sum rows only by SUM on G (no row file of mine holds
   B_FINE-T2-G; the sum 22,952,032 is the check). Knowns: T1 O 10,170,054, T2 O 11,915,365 --
   both must come out EXACT. Kill: any differing row or sum.
2. The gate ratio against long 17's S14 run (4,049,383): T1 in [1.03, 1.12] (the +7.05 percent
   tree), T2 in [1.15, 1.35] (the +25.4 percent tree). Kill: outside either interval.
3. iir ratio against long 17's 353,529: T1 in [0.8, 1.25], T2 in [0.7, 1.4] (the fine path's
   shifted reductions move the missing-hash-move events, direction unknown). Kill: outside.
4. The razor pair under T2 stays within [0.8, 1.3] of S14's values (razor lives at depth <= 2
   where the fine path's history term barely acts). Kill: outside.
5. The carrier question is answered by the largest |ratio - 1| among the big counters (gate,
   rfp_ret, null_try, probcut_enter, iir); job 4's d-count prediction says the fine history
   term's -1 sites (good history, reduced less) drive the growth, so I expect rfp_ret and the
   gate to move TOGETHER and null/probcut to stay nearest 1. Kill: probcut_enter's |ratio - 1|
   the largest of the four.
