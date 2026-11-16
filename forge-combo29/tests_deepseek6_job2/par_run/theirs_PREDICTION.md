job 2 prediction (own commit, before the first run of Part A; never edited)
2026-11-16T16:59:55Z

Part A -- for each setting, the smallest of its four runs (2c, 4c) at which I expect 20 or more of 200
BEST MOVES on O to change:

- NullMoveEvalDivisor: NONE of the four (even 4c keeps every best move on O). Job 1 measured bm 200/200
  at both 1c ends while nodes moved by ~1-2 %: this setting changes tree size, not choices, at these steps.
  Kill: any of its four runs with fewer than 181 bm-equal on O.
- RfpDepth: NONE of the four (bm 200/200 at both 1c ends). Kill: any of its four runs with fewer than 181.
- FutilityDepth: at 2c fewer than 20 at both ends (5: expect 5-19 changed; 9: 1-10); at 4c the LOW end
  (value 3) reaches 20 or more, the high end (11) does not. Kill: neither 2c-low nor 4c-low reaches 20,
  or the 2c-low already reaching 20.
- SeeNoisyMultiplier: ALREADY at 2c BOTH ends have 20 or more changed (job 1 saw 22 changed at 1c-low).
  Kill: either 2c run with fewer than 20 changed.

Part B -- the gate opened with CaptureFutilityBase 230:
- B1..B4: I expect ALL FOUR to differ from B0 in nodes on BOTH sets (the block now actually runs, so its
  two knobs and both of their ±1c moves must move the tree). Kill: any of B1..B4 with 0 node differences
  on a set.
- B0's tree against S14: a node RATIO of about 0.93 on O (range that kills it: outside 0.85..1.00, or
  exactly 1.000 which would mean the gate is still not open) and about 0.93 on G (same kill range).
  The capture-futility block only prunes, so the ratio should be below 1, and 230 is deep enough to prune
  only clearly-lost captures, so it should be a few percent, not tens.
