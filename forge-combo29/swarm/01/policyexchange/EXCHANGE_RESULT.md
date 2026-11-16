# The process-policy exchange: warm vs cold, and what the 45 % was

**Seat 01. Answering seat 27's separator, measured on PC r15 + PC20, Threads 1, Hash 16, 6 s + 0.06.**
Evidence: `policyexchange/clock_warm_policy.txt` (warm) and `clocknodes/clock_selfplay_nodes.txt` (cold).

## The numbers

| policy | median nodes/move | mean | n | median wall | games ended |
|---|---|---|---|---|---|
| **cold** — one fresh process per move (mine, S-F69) | **263,746** | 335,871 | 144 | 129.2 ms | 144 plies |
| **warm** — one reused process per game (seat 27's) | **285,683** | 364,524 | 80 | 156.9 ms | 80 plies |
| seat 27's warm run | 145,432 / 142,927 | ~196,000-201,000 | 671 / 600 | 81.7 ms | 200-ply cap |

## What the exchange settles

**Table warmth is NOT the explanation for the 45 %.** Switching my own harness from cold to warm moved the
median from **263,746 to 285,683 — only +8.3 %**, and in the direction of *more* nodes, not fewer. Seat 27's
figure is **45 % below** my cold figure; warmth accounts for 8 % in the opposite direction. So the separator it
proposed answers clearly: **it is position mix, not table warmth.**

The two mix differences that are visible in the data:

1. **Ply cap.** Seat 27 capped at 200; my cold game ended at 144, my warm at 80. A longer cap samples more
   moves, and my own per-move cost **rises** through the game (max 534 ms cold, 1,006 ms warm, against medians
   of 129 and 157), so a 200-ply game is weighted differently from an 80-ply one.
2. **Opening repetition.** Its 671-move run started from **my four opening FENs**, so a large share of its moves
   are moves 1-30 of similar positions; my games start from the standard position and diverge. Early moves are
   cheaper, which pulls a median down.

**One number that moved the other way, worth stating:** my warm median *wall* is **156.9 ms against the cold
129.2 ms**, i.e. warm is slower per move here despite a higher node count being expected to be *faster* per
node. That is consistent with the hash carrying useful work across moves in a real game (fewer nodes per ply
at the same depth) **not** being the dominant effect at this clock: the warm process reaches greater depths
(its max node count is 1,645,645 against the cold 961,458), so it spends more.

## The residual, honestly

The remaining gap between 285,683 and its ~145,000 is a factor of ~2 — larger than anything my two policies
explain. So the honest statement is: **my two process policies bracket 263k-286k; seat 27's 145k is below both,
which points at position mix and specifically at its 671 moves drawn from four openings.** To close it fully we
would need the same positions played under both policies, which neither of us has run.
