long 16 prediction (R on kimi5's FailHighBlendCheck, its job 12 companion) -- own commit before the first counted run

1. R3: the check build (FORGE_FHB_CHECK=1) under S14 with FailHighBlend 0 gives rows on O and G
   equal to my long-1 S14 rows on every position (observe-only counters). Kill: any differing row.
2. R4: my five runs (S14, O, depth 12, FHB 0/1/2/4/7) give
   (a) rows equal to kimi5's c_fhbN_s14_O_d12.json on 200 of 200 positions (nodes AND bestmove) --
   the same trees its counters were taken on;
   (b) aggregated FHB counters equal to its counter_sums.txt exactly: rfp A 1,965,016 (FHB 1);
   standpat A 1,815,929 and qend A 734,301 (FHB 2); mainend A 1,444,832 (FHB 4); FHB 7 all four
   places 1,959,912 / 1,777,673 / 711,666 / 1,529,966; L = R = M = 0 in every run of mine as in
   kimi5's; FHB 0 all zeros. Kill: any differing count or row.
3. R5: the planted fault is reported (ASan, exit 1); the clean sanitizer check build over O under
   S14 d12 (FHB 0) gives 0 sanitizer lines. Kill otherwise.
