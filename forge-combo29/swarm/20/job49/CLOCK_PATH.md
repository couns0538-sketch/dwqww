# seat 20 — job 49: the PC's clock path (6 s + 0.06) at Threads 1 — TIME decides the depth, so it is not reproducible

FABLE_TO_swarm_6 says the owner's strength matches use the clock 6 s + 0.06 per move. Seat 08's 08-F25 recorded that
a high-counter endgame does not fit that clock. Nobody had published the basic numbers, so this measures them.

Method: `go wtime 6000 btime 6000 winc 60 binc 60`, PC r15 + PC20, **Threads 1**, Hash 16, fresh process per move,
3 independent runs of 6 consecutive moves with the remaining time passed back in as a GUI would. Positions from real
games (G1, G2).

## How long a move takes, and how deep it gets

| position | typical depth | nodes | wall time |
|---|---|---|---|
| G1 | **17–18** | 170,070 – 314,239 | **140–165 ms** |
| G2 | **17–18** | 237,233 – 514,093 | **129–301 ms** |

A 6 s clock is nowhere near binding: the engine uses **130–300 ms** per move, i.e. **2–5 % of the 6.06 s** available.
Depth reached is 17–18 on both positions.

## The finding: the clock path is NOT reproducible even at Threads 1

Same position, same move index, three independent runs:

| position | move | result |
|---|---|---|
| G1 | 1 | SAME move+depth, nodes 314,239 (×3) |
| **G1** | **2, 3, 4** | **VARIES — depth 17 or 18, nodes 288,912 or 314,239** |
| G1 | 5, 6 | SAME, nodes 288,912 (×3) |
| G2 | 1, 2 | SAME, nodes 514,093 (×3) |
| **G2** | **3, 4** | **VARIES — depth 17 or 18, nodes 514,093 or 237,233** |
| G2 | 5, 6 | SAME, nodes 237,233 (×3) |

**The move never changed** (`g7g6` on G1, `b6b5` on G2, in every run) — but the **depth and node count did**, because
the search stops when the wall clock says so, and the clock is a wall clock. Run-to-run wall variation of ~5 ms
(157–165 ms) is enough to decide whether the 18th iteration finishes.

This is **not** the multi-thread nondeterminism I recorded in S-C24 (that was the same fixed budget giving different
scores). Here Threads is 1 and the *budget itself* is time-based, so irreproducibility is inherent to the clock
path. It is not a defect either — a GUI plays on a clock, and time-based stopping is the design.

## What it means for the owner
1. **Match results on a clock are not exactly reproducible**, even single-threaded, because depth 17 vs 18 can flip
   a score. A re-run of a 6 s+0.06 match will not replay game-for-game. Node-limited matches (`go nodes N`) are
   exactly reproducible and the clock ones are not — that is the practical difference between the two paths.
2. **The clock is not the constraint at these depths.** 2–5 % of the budget is used, so increasing the clock a little
   buys very little, and *reducing* the per-move target (as `go softnodes 2000` does for self-play) is a much bigger
   lever than changing the clock.
3. The **move** is stable across runs at this budget on these positions, so match *strength* conclusions are not
   undermined — only exact replay is.

## Honest limits
- Two positions, six moves, three runs each — enough to show the flip, not to bound its rate.
- Clock path only; the PC's own net would change the node counts (not the mechanism).
- `Threads 1` throughout, as required.
- I did not test the clock at the low end (seat 08's `go wtime 10` case) — that is their finding, not mine.
