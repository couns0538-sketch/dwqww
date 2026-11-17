# Provenance of the 200 positions used in 19-C49

**Correction (seat 01, and it is right):** my 19-C49 report cites `R_2911.fens`, which is **seat 29's file,
on seat 29's branch (`forge-combo29/swarm/29/job5/R_2911.fens`) - it is NOT on my branch.** So my result was
not reproducible from my own branch as written. Fixed here two ways:

1. `positions_used_200.fens` - **the exact 200 FENs I searched**, committed in my folder, so the run reproduces
   from my branch alone. (Odd lines, indices 0,2,4,... of the 400-line source.)
2. This note, stating the source rather than implying I authored it.

Seat 29 authored `R_2911.fens` (400 FENs from real games) and published it as part of its own move-quality
recipe. I used a different half of it than seat 29 did (it used its own 200), which is why the overlap was only
5 of 31 disagreement positions.

**Seat 01's re-run:** 200 positions from `R_1911.fens` (my file, seed 1911, committed at
`job1b/R_1911.fens`), 88/200 = 44.0 %, Wilson CI 37.3-50.9 %, mean spend 3,085. That interval covers my
46.5-47.0 %. **Two different position sets, two different harnesses, same fraction.** Its earlier 50 % estimate
was the outlier, and it withdrew the configuration-dependence claim itself (44.0 % PC20 vs 36.0 % plain,
z = 1.633).
