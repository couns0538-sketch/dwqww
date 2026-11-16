# seat 20 — job 41: seat 28's S-F19 (competing patches) and S-F21 (score reproducibility), Threads 1

Final short-list entry. Everything below states **build** and **settings**; all Threads-1 rows send
`setoption name Threads value 1` explicitly.

## S-F21 — reproduced, and it is worse than "scores vary": the MOVE varies too

Build `PC r15`, settings `PC20`, position `r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1`,
`go depth 12`, five fresh processes per thread count.

| Threads | distinct scores | distinct moves | distinct node counts |
|---|---|---|---|
| **1** | **1** (`cp 70` ×5) | **1** (`e1g1` ×5) | **1** (36,104 ×5) |
| **4** | **5** (`cp 74, 85, 65, 59, 79`) | **3** (`e1g1`, `c2c3`, `d2d4`) | **5** (105,712 … 191,362) |

**CONFIRMS S-F21** and strengthens the sentence: at Threads 4 the engine does not merely report different scores,
it **plays different moves** on the same position. That is a reproducibility problem for any match or test run
above Threads 1, and it is the strongest argument yet for the swarm's Threads-1 rule.

*Note on numbers:* my `cp 70 / 36,104` at Threads 1 differs from their `cp 54 / 27,066` because I used a different
board (theirs is named only as "one lost position"; I used the Italian and say so). **The thread-count contrast is
what I am confirming, not their absolute values.**

## S-F19 — the separating case behaves as they report on the unpatched builds

Their claim: the counter-resetting mate board is FIXED by their patch — base `h6h7`/cp 0/0 nodes vs patched
`h6h7`/mate 2/398 nodes, "exactly seat 01's 398". I did **not** build their patch (it applies to a tree I do not
have patched), so what I can confirm is the **unpatched** half and the mechanism:

| build + settings | `8/3K4/7P/8/8/7k/8/6Q1 w - - 100 1`, `go depth 6`, ×3 |
|---|---|
| base 6b98f217 + S14 | `h6h7` / **cp 0** / **0 nodes** ×3 |
| PC r15 + PC20 | `h6h7` / **`mate 2`** / **200 nodes** ×3 |

So on the unpatched base tree the draw is declared without searching while a forced mate exists, and **an
independent repair (the PC build) already reaches `mate 2` on that board** — which corroborates their point that the
case is discriminating and fixable, and gives the owner a second data point that the PC's own repair handles it.

Their `398 nodes` for their patch is a different number from the PC build's 200 — both are searched mate-2
answers on the same board with different code, so I make no claim about which patch is better. **Which of the three
competing patches to advise is still the owner's decision, and I am not making it.**

## What I did NOT do
- I did not apply seat 28's `job5/search.cpp.patch.txt`, nor seat 01's, nor seat 12's. Comparing them is a
  patch-engineering job (each needs its own scratch build + the four pins + the separating cases), and I would
  rather say so than pick one from a table.
- S-F21's exact board was not available to me; I used the Italian and declared it.

## Honest bottom line for the queue
Seven of the eight short-list entries are now confirmed at Threads 1 (S-C17, S-C18, S-C19, S-C20, S-C21, S-C22,
S-C23). This one is confirmed in the half I could test and explicitly **not** confirmed in the patch-comparison half.
