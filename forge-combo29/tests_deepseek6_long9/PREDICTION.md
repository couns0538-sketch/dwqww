long 9 prediction (R on kimi5's LmrDS_tunables, job 4) -- own commit before the first counted run

R3 identities:
1. The tunable build at every default (switch off) equals my long-1 S14 rows on O and G on every
   position. Kill: any differing row.
2. The base build with LmrDeeperShallower true equals the tunable build with LmrDeeperShallower true
   (all four tunables at default) on every position of O and G (kimi5's K2, remade independently).
   Kill: any differing row.

R4 (nine non-default settings kimi5 tested, rows on O and G at depth 12):
3. On O, every one of the nine runs equals kimi5's d12 json for that setting position by position
   (nodes AND bestmove): k3 (100000/-100000), k4a (DeeperBase 20), k4b (DepthMul 4), k4c
   (ShallowerBase 50), k4d (ShallowerDepthMul 3), deep (ShallowerBase -100000), flat (8/0), half
   (20/1), dbl (80/4). Kill: any differing row in any of the nine.
4. On G (no kimi5 rows; direction predictions against S14's 18,466,239):
   k3 EXACTLY 18,466,239 (the switch-off proof is node-for-node on O; the same arithmetic must give
   the identical tree on G). Kill: any difference.
   k4a > S14, k4b > S14, deep > S14, half > S14, dbl > S14 (the deeper arm fires more -> larger
   tree). Kill: any of these five at or below 18,466,239.
   k4c < S14, k4d < S14, flat < S14 (the shallower arm fires more -> smaller tree).
   Kill: any of these three at or above 18,466,239.

R5: the planted sanitizer fault is reported (ASan line for the planted overread); the clean
sanitizer build gives 0 sanitizer lines over O at the nine settings. Kill: the plant silent, or any
sanitizer line in a clean run.
