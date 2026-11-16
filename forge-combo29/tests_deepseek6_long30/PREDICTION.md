long 30 prediction (recipe R on LmrCutNode 5859a66f, LmrGiveCheck 0e5b0375, LmrTtPv 05e49972)
-- own commit before the first counted run; the three are done one at a time in this order.

For EACH of the three patches (built alone on a clean 6b98f217, release, no calib flag):
1. R2 pins: bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609; the uci list shows the
   option with kimi5's default and range (LmrCutNode 0..4 default 2; LmrGiveCheck 0..4 default 1;
   LmrTtPv 0..4 default 1). Kill: any pin or uci line differing.
2. R3 identity: rows under S14 on O and G equal my long-1 rows on every position (the option at
   its default is today's code). Kill: any differing row.
3. R4 (the setting kimi5's job-7 report tested, on ITS rows files o1_v1/o2_v0/o3_v0):
   LmrCutNode=1 rows on O and G equal kimi5's o1_v1 jsons position by position (nodes AND
   bestmove), sums 12,310,830 / 22,228,946; LmrTtPv=0 rows equal o2_v0, sums 8,572,032 /
   16,869,889; LmrGiveCheck=0 rows equal o3_v0, sums 11,811,886 / 21,239,639.
   Kill: any differing row or sum in any of the six runs.
Note: kimi5's proof build carried the LmrCalib flag; the counters are observe-only, so my
no-flag rows must equal its flag-build rows -- if they do not, THAT is the finding.
