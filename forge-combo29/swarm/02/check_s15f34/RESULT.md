# S02 check of seat 15's 15-F34 — CONFIRMS both halves, including the depth-64 explanation

Their finding: no movetime "character cutoff" between 1000 and 3000 ms — working boards honour 99-100 % of either
slice (990/990/990 and 2990/2990/2990) — and the only early-stopping cells are endgames that hit **depth 64 (the
clamp maximum)** with IDENTICAL node counts at both slices, so the depth ladder ended, not the clock.

## my measurement (own harness, `check_s15f34.py`)
PC r15 + PC20, Threads 1, Hash 16, OwnBook false, 2 runs per cell, cold, interactive driver.

| board | movetime | wall ms | % of slice | nodes | depth |
|---|---|---|---|---|---|
| mid_sharp (middlegame) | 1000 | 991 / 991 | **99.1 %** | 1,521,499 | 22 |
| mid_sharp | 3000 | 2991 / 2991 | **99.7 %** | 4,743,913 | 28 |
| mid_quiet (middlegame) | 1000 | 991 / 991 | **99.1 %** | 1,580,477 | 20 |
| mid_quiet | 3000 | 2990 / 2991 | **99.7 %** | 4,630,363 | 23 |
| end_trivial (K+R v K) | 1000 | 2.0 | 0.2 % | **2,596** | **64** |
| end_trivial | 3000 | 2.0 | 0.1 % | **2,596** | **64** |

## both halves confirm
1. **No character cutoff.** On boards with real search work the slice is honoured at **99.1 % at 1000 ms and
   99.7 % at 3000 ms** — the same character across the range, matching their 990/2990. Their claim is that a
   1000 ms slice is not qualitatively different from 3000 ms, and that holds.
2. **The early stops are the DEPTH CLAMP, not the clock.** My trivial K+R-v-K board finished in 2 ms at **depth 64
   with exactly 2,596 nodes at BOTH slices** — identical node counts, which is the signature they describe: the
   depth ladder ran out, so more time cannot buy more search. Their boards gave 2,196,864 and 94,406 nodes; mine
   gives 2,596; the mechanism is the same and the node count is board-specific.

## why this matters beyond the confirmation
This is the third independent sighting of the same trap, and it is worth naming once for the owner: **a
`go movetime` measurement that comes out far below the slice is not necessarily a clock defect — check whether the
search hit the depth clamp first.** A board that is trivially finished reports ~0 % of its slice at depth 64, and
any latency harness that averages over mixed boards will pull its median down without anything being wrong. My own
clock work avoided this only because I used middlegame and endgame boards that do not finish; a harness using easy
positions would have measured the clamp, not the clock.

## scope
Two middlegame boards and one trivial endgame, 2 runs each. Enough to confirm the mechanism and the direction;
their 5 boards x 2 slices x 5 runs remains the larger sample for the rate.
