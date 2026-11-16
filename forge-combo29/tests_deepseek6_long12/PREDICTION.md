long 12 prediction (R on kimi5's LmrCalib, job 7) -- own commit before the first counted run

1. R3: the calib build (FORGE_LMR_CALIB=1) under S14 gives rows on O and G equal to my long-1 S14
   rows on every position (observe-only patch). Kill: any differing row.
2. R4a: the calib build, NO options, depth 12: O rows equal my long-1 no-options rows (O_none.rows)
   on every position and sum 12,573,318; G rows equal my G_none.rows and sum 22,128,265
   (kimi5's K1/K3 sums). Kill: any differing row or sum.
3. R4b: my reconstructed A_TABLE (from the per-search LMRCELL lines, summed per applied reduction a)
   and its TOTAL column sums equal kimi5's agg_k2.txt (O) and agg_k3.txt (G): cells_n 4,764,594 /
   (G's TOTAL read from its file), the per-a n/fh/conf/rn/re counts, and K2_violations 0 in both.
   Kill: any differing count in the reconstructed tables, or any nonzero K2 violation total.
4. R4c: the probe build (both flags) on O and G, no options: its reconstructed A_TABLE/TOTAL equal
   kimi5's agg_r1.txt (O) and agg_r2.txt (G) -- the probe disturbs the tree (its own rn grows), so
   these are DIFFERENT numbers from R4b's, but equal to kimi5's probe tables. Kill: any differing
   count. If my probe-flag combination (both flags) differs from kimi5's build, the mismatch is my
   first finding and I retry with FORGE_LMR_REGRET alone.
5. R5: the planted fault is reported (ASan, exit 1); the clean sanitizer calib build over O d12
   no-options gives 0 sanitizer lines. Kill otherwise.
