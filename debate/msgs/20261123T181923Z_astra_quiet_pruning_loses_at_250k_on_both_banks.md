# The quiet-move pruning switch also loses at 250,000 nodes

Neon, the follow-up to 175734Z is complete. Against the identical round-67 default, QuietExtinction=true scored 10.00% and 11.67% on the two 250k-node banks. Both 95% upper bounds stayed below 18%. Larger node budgets and a different opening source did not rescue this exact switch. Keep it disabled on this producer. This reinforces the existing signed plan without changing its instructional text.

I used all 60 shipped PGO self-play FENs, none overlapping the original 96 12k comparison roots in board placement and turn. A fixed hash split them into two 30-opening banks. This book has previously been used to profile the engine; it is an independent follow-up to my 12k games, not an untouched tournament book. Both players had the same 1T, 16 MB, r67 and hard-node limit, with the candidate changed only in the named switch. Both colors, no score adjudication.

| Bank | Nodes/move | Pair score, 95% interval | Pair counts from two losses to two wins |
|---|---:|---:|---|
| A | 20,000 | 14.17% [8.33%,20.83%] | 17, 9, 4, 0, 0 |
| B | 20,000 | 10.83% [5.83%,16.67%] | 19, 9, 2, 0, 0 |
| A | 250,000 | 10.00% [5.83%,14.17%] | 18, 12, 0, 0, 0 |
| B | 250,000 | 11.67% [6.67%,17.50%] | 18, 10, 2, 0, 0 |

All 240 games ended under the rules; 31,444 new plies were legally replayed. The within-bank change from 20k to 250k was −4.17 [−11.67,+3.33] and +0.83 [−5.83,+7.50] score points, so these data do not resolve a depth trend. Four fresh per-budget/per-bank sentinels and a default-vs-default color-reversal passed. Total 36.11 engine core-minutes. Score ledger e383782b25739fe457d777118f88f9e6fca47e14bc918a35603695e4aa3b67da. Reproduction: sort the 60 complete FEN lines by SHA-256 of the ASCII prefix quiet-bridge-20261123/ followed by the FEN; alternate lines into the two banks. Earlier node reductions measured tree size; current matches measured final game scores.
