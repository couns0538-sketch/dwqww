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


---

# the clamp trap is NOT a risk on the owner's real clock path — measured

The S-C18 warning ("a movetime far below its slice may be the depth clamp, not the clock") is only a practical
worry if real game positions can hit the clamp. I tested eight of them on the owner's exact clock,
`go wtime 6000 btime 6000 winc 60 binc 60`, PC r15 + PC20, Threads 1:

| board | wall ms | depth reached | nodes | clamp hit |
|---|---|---|---|---|
| g1 middlegame | 381 | 19 | 683,500 | no |
| g2 middlegame | 163 | 18 | 314,239 | no |
| g3 endgame | 205 | 21 | 479,853 | no |
| g4 middlegame | 302 | 17 | 501,519 | no |
| g5 tactical | 201 | 17 | 347,819 | no |
| g6 kiwipete | 275 | 16 | 428,663 | no |
| g7 sparse endgame | **1585** | 16 | 1,784,852 | no |
| g8 middlegame | 595 | 18 | 998,994 | no |

**0 of 8 hit the depth-64 clamp.** Depths reached were 16-21, nowhere near 64. So:

- **On the owner's clock, the clamp trap does not bite on real positions.** The early-stop phenomenon I confirmed in
  S-C18 is real but confined to boards that are trivially finished (a lone-king or K+R-v-K ending), which a real
  game reaches rarely and never at depth 64 in the time available.
- **It still matters for a HARNESS**, which is where the warning belongs: a latency study that mixes in solved
  positions will average in ~0 % cells and misreport the clock. That is the case to guard against, not the owner's
  play.
- g7 is the same sparse endgame that hits the **hard limit** at 1585 ms (my S-F13), which is a different mechanism
  again — the clock cut, not the depth clamp. Both are in this file now, clearly separated: one is "finished, so
  stopped early", the other is "unfinished, so cut at the hard limit".
