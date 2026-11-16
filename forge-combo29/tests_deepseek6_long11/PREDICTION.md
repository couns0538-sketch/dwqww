long 11 prediction (R on kimi5's SearchChecks, job 6) -- own commit before the first counted run

1. R3: both builds (no-flag and FORGE_SEARCH_CHECKS=1) give rows under S14 on O and G equal to my
   long-1 rows on every position. Kill: any differing row in any of the four.
2. R4: my flag build's four measured runs reproduce kimi5's per-site made/breach counts EXACTLY
   (deterministic search, same source, same flag):
   - O, 200 positions, depth 12, no options (its agg_k2.txt), including V2/V3 child-score
     made-count 12,573,318 = the engine's own node sum;
   - G, 353 positions, depth 12, no options (agg_k3.txt), child-score 22,128,265;
   - G first 50, depth 16 (agg_g50d16.txt);
   - O first 50, depth 12, Threads 4 (agg_o50t4.txt).
   Including the one real breach site: V5.store-qfinal breaches 19,021 / 28,821 / 8,286 / 14,649
   on the four runs, and every other site 0 breaches except the two V6 suppressed-store arrival
   counts and the by-design V4 mate-return counts, all equal to kimi5's numbers.
   Kill: ANY differing made or breach count at any site of any run.
3. R5: the planted fault (top of Worker::search, one int past new int[8]) is reported by ASan
   (exit 1); the clean sanitizer flag build over O at depth 12 no options and over O50 T4 d12
   gives 0 sanitizer lines. Kill: the plant silent, or any sanitizer line in a clean run.
