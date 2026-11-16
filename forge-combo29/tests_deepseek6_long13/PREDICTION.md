long 13 prediction (R on kimi5's NodeSteps, job 8) -- own commit before the first counted run

1. R3: the counting build (FORGE_NODE_STEPS=1) under S14 gives rows on O and G equal to my long-1
   S14 rows on every position, and with no options equal to my long-1 no-options rows on every
   position. Kill: any differing row.
2. R4 counting: my four runs (defaults O, S14 O, S14 G, defaults G) aggregate EXACTLY to kimi5's
   agg_k1_* tables: lines_summed, the K4/k4t/k4c line, and every labeled array (gate, rzt, rzr, rzn,
   rfp 42, nlt, nlr, nlv, nleb 42, nlnd 21, nlnr, nlnm, pce, pcc, pcr, pcn, splitviol) -- including
   GATE 5,762,433 on defaults-O and rfp's first cell 179,244. Kill: any differing number.
3. R4 probe: my four probe runs (defaults O, S14 O, S14 G, defaults G) aggregate EXACTLY to kimi5's
   agg_r1..r4 tables including the reg section (seen, ended1 0, wide 0, pnodes, rz 14, rfpg 84,
   nl 14, nlebg 84, nlndg 42, pcg 14); the three controls (defaults O + RfpMargin 10 / 300 /
   300 with N_RFP=100) equal its agg_r5/r6/r7. Kill: any differing number.
4. K4-style: k4t/k4c/splitviol viol counts are 0 in every line of every run. Kill: any nonzero.
5. R5: the planted fault is reported (ASan, exit 1); the clean sanitizer counting build over O
   under S14 d12 gives 0 sanitizer lines. Kill otherwise.
