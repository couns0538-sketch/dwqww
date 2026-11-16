long 40 prediction (long 18's carriers at depth 14) -- own commit before the counted runs

1. The S14 depth-14 counter run sums EXACTLY 21,812,100 and its rows equal the plain build's
   depth-14 rows (my long-29 s14_base.rows) on all 200 positions. Kill: otherwise.
2. V's depth-14 sum is BELOW S14's depth-14 sum (the variant still shrinks the tree deeper).
   Kill: equality or growth.
3. The gate's V/S14 ratio at depth 14 lands in [0.85, 0.95] and below the tree ratio (the gate
   led the tree at depth 12: 0.895 against 0.9016). Kill: outside, or at/above the tree ratio.
4. rfp_ret remains the step with the largest ABSOLUTE drop inside the gate (as at depth 12:
   -227,440). Kill: another step's absolute drop exceeds rfp's.
5. probcut_enter's ratio at depth 14 stays within [0.80, 1.05] (its depth-12 ratio 0.911; the
   depth-amplification of long 35 fights the variant's shrink here). Kill: outside.
