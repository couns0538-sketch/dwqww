RE F4 / W5(f) — MEASURE for larger future stores. Under ONE unchanged deterministic producer and no registry, the fraction of surplus eight-random-ply requests grows materially across simulated runs of 16.37M, 32.74M, 65.48M and 130.96M requests. Two independent opening streams and independent stable sampling salts respectively returned 1.858/1.857%, 3.607/3.571%, 6.642/6.574%, and 11.660/11.582%. With two extra random plies from the same prefix streams, the last figures become 0.382/0.398%. The smaller fractions describe key collisions; deeper random starts change the distribution and training games. Do not switch the live opening policy from this evidence.

Known positive control: the first 16.37M stream's exact earlier surplus is 304347 (053938Z); the 1/64 stable whole-key sample estimated 304128 with estimated SE 4587, within the predeclared three SE. At the largest size the first stream estimates 15270144 ± 40425 surplus requests (one SE) vs 15167424 ± 40169 in stream two. Sampling variation conditional on a stream and variation in future producer settings are different. Surplus is occurrences beyond the first per full A7 key, never the number of equal unordered pairs. Actual saved CPU time also requires a measured duplicate-vs-unconditional cost ratio on the live producer. No change to current F4 priority: its original one-day, 1.86% fixture and fail-open rule stand. Changing network or deterministic settings changes the manifest and starts a different count.

Reproduction using the unmodified Board and legal move ordering of 053938Z: start at standard chess, use std::mt19937_64; for a legal move count n draw a 64-bit unsigned x, discard x < ((0-n) modulo 2^64) modulo n, use x modulo n. Seed initial eight plies 202611230527/202611230710, extra two from separate engines seeded 202611230722/202611230711. Reject when no legal moves before a requested random ply. The PC's pre-ply third-occurrence check is also applied before the ninth and tenth moves (one/two rejections across the full two runs respectively); there cannot be a threefold before the eighth move, nor material/rule50 draws at these depths. Count the eight-ply request after the eighth move; the ten-ply control can have fewer accepted requests. For every class compare full A7 keys (current board with relevant geometrical ep and ordered history with legal ep); sampled fingerprint collisions were materialized and checked. The 64-bit mix is the SplitMix finalizer: XOR right-shift 30, multiply bf58476d1ce4e5b9, XOR right-shift 27, multiply 94d049bb133111eb, XOR right-shift 31, all modulo 2^64. Let h=halfmove clock, ep be the current retained target index or -1; start with mix(16*(1+ep)+h) and fold each Board key from h plies ago through the current key using mix(value XOR key). Retain entire classes for which mix(fingerprint XOR salt) mod 64 = 0. Salts 530b6e4278a85d19 and a8237811dce49b63 are fixed hexadecimal. If a retained class occurs c times, estimate surplus by 64*sum(c-1) and Bernoulli whole-class sampling SE by sqrt(63*64*sum((c-1)^2)); this interprets the scrambled hash as a uniform sample. Exact repeated-position comparisons protect against a fingerprint conflating different openings. No engine matches, strength changes or rental-rate estimates in these two runs.

Raw CSV, seed pair one:

```csv
plies,accepted_draws,sampled_occurrences,sampled_classes,sampled_surplus,estimated_surplus,est_se,est_surplus_pct
8,16370000,255316,250564,4752,304128,4586.82635381,1.85783750764
10,16365893,255695,255588,107,6848,656.828744803,0.0418431184904
8,32740000,511428,492974,18454,1181056,9427.26598755,3.60737935247
10,32731750,511231,510763,468,29952,1382.4499991,0.0915074812682
8,65480000,1023249,955292,67957,4349248,19404.9610152,6.64210140501
10,65463639,1022600,1020672,1928,123392,2821.19974479,0.188489368885
8,130960000,2047232,1808636,238596,15270144,40425.0631168,11.6601588271
10,130927237,2044226,2036411,7815,500160,5739.81463115,0.382013713464
```

Seed pair two:

```csv
plies,accepted_draws,sampled_occurrences,sampled_classes,sampled_surplus,estimated_surplus,est_se,est_surplus_pct
8,16370000,255091,250340,4751,304064,4604.81139679,1.85744654856
10,16365870,255348,255223,125,8000,709.929573972,0.0488822164663
8,32740000,509910,491643,18267,1169088,9362.67654039,3.57082467929
10,32731817,510923,510405,518,33152,1447.97790038,0.101283714253
8,65480000,1020358,953094,67264,4304896,19234.558898,6.57436774588
10,65463641,1022470,1020414,2056,131584,2902.90888593,0.201003179765
8,130960000,2043191,1806200,236991,15167424,40169.3686283,11.5817226634
10,130927367,2043424,2035287,8137,520768,5844.9239516,0.397753358929
```
