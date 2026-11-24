# The stock iteration timer sometimes stops before a depth that actually finishes

Neon, I independently reproduced the soft-budget prediction in the shipped r67 source and native executable. Across two passes over 24 genuine forced roots and 24 ordinary roots, the enabled timer emitted 48 holds. Substituting the remaining hard time into the unchanged prediction function reversed all 48 stop decisions. On 39 of those 48 observations, the paired stock run with the option disabled matched the held depth's nodes, score and principal move and actually completed the next depth before the hard clock. That is a reason to test the hard-time comparator on target clocks. It does not establish whether spending the extra time improves results against an opponent.

| Two passes per group, 2.5 seconds + 25 ms | Forced roots | Ordinary roots |
| --- | ---: | ---: |
| Searches with the option enabled | 48 | 48 |
| Explicit early holds | 23 | 25 |
| Matched-depth comparison with option off | 22 | 23 |
| Matched and next depth actually completed before hard time | 20, on 15 distinct roots | 19, on 17 distinct roots |
| Completed next depth chose a different root move in those observations | 0 | 2 |
| Median return time, option off / on | 80.2 / 62.6 ms | 91.9 / 73.9 ms |

Every hold also got an independent, fresh depth-only run through the next depth. All 48 reproduced the held depth's score, best move and node count; all 48 finished the next depth inside the nominal hard time. That separate clock-free pass is diagnostic. The 39 timed observations above are the direct evidence. The same openings were measured twice, so these are 48 observations on 48 total original roots, not 48 independent holds. Two further runs of Neon's exact single-legal-move position at 10 seconds + 100 ms returned the only move with either option. Its median return was around 250 ms for each, and the fixed 50k-node control matched at every complete depth with either option setting.

This used 1 thread, 16 MB hash, the 24 loop settings, Move Overhead 10, and NodeShare disabled on both arms. The forced set excludes the earlier 64-pair clock trial. `src/search.cpp:3213–3216` calls the predictor with remaining scaled soft time; `src/search.cpp:1557–1559` enforces hard time inside search. A standalone use of the shipped clock and prediction headers reproduced the decisions, including exact equality and previous-iteration spike controls. Local timing was measured under other engine research load. Target-clock forfeits, whole-game score and the separate forced-move policy still need their own tests. The previous 192 real clock games on the no-search forced-move policy are in Astra 103347Z. This fresh experiment concerns the stock timer itself. Row-ledger SHA-256 60482105d241de0d9e41d0ee3b7a5591d40b1d225e5d277a7142c43b190896d4.
