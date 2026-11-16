long 14 prediction (R on kimi5's tunable_AspReopenMargin, its job 3.2) -- own commit before the first counted run

1. R3: the tunable build (option at its default 13) under S14 gives rows on O and G equal to my
   long-1 S14 rows on every position. Kill: any differing row.
2. R4a (the wiring control remade): counters.patch + tunable patch, AspCappedReopen true, on
   kimi5's wire8.fens at depth 12: AspReopenMargin 0 / 13 / 100 give EXACTLY 279,937 / 407,550 /
   469,476 nodes. Kill: any differing sum.
3. R4b (the margins on the full sets, tunable build alone, under S14): on BOTH sets the node sums
   order margin0 < S14 < margin100 (0 breaks the reopen loop early via the iteration_score <=
   alpha break; 100 widens the reopen so more iterations succeed-and-continue).
   O: margin0 < 9,500,069 < margin100. G: margin0 < 18,466,239 < margin100.
   Kill: any wrong direction, or equality with the S14 sum at either end.
4. R5: the planted fault is reported (ASan, exit 1); the clean sanitizer tunable build over O under
   S14 d12 gives 0 sanitizer lines. Kill otherwise.
