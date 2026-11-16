# `go softnodes N` on the PC build under PC20 — the owner's self-play path

FABLE_TO_swarm_6 names the owner's self-play as `go softnodes 2000` and asks three things: is it deterministic
run to run, does it stop at a finished depth, and how far past N does it go.

Conditions: **PC r15 build**, **PC20** settings applied in full, **Threads 1**, Hash 16, OwnBook false, fresh
process per run (COLD — a softnodes stop point is a NODE count, so seat 10's warm-search rule applies), 3 runs
per cell, interactive driver.

## the model, read from the source BEFORE measuring
- soft budget = a FINISHED-ITERATION target: after each completed iteration, if nodes >= N, stop and keep that
  move and score (src/search.cpp:2932 and its comment).
- hard budget = **4 x N**, kept on the normal node stop, so a runaway iteration is cut and its partial move
  discarded (src/search.cpp:2498-2501).
So the model predicts: **nodes >= N always, nodes <= 4N always, stop at an iteration boundary.**

## the table (`softnodes_probe.py`, raw `rows.json`)

| position | N | deterministic | depth | nodes at stop | nodes / N | >= N? | <= 4N? | bestmove |
|---|---|---|---|---|---|---|---|---|
| startpos | 2000 | YES | 7 | 4121 | 2.06 | yes | yes | d2d4 |
| startpos | 20000 | YES | 12 | 21600 | 1.08 | yes | yes | d2d4 |
| startpos | 50000 | YES | 15 | 78579 | 1.57 | yes | yes | d2d4 |
| startpos | 250000 | YES | 18 | 377485 | 1.51 | yes | yes | e2e4 |
| middlegame | 2000 | YES | 7 | 3278 | 1.64 | yes | yes | d4c5 |
| middlegame | 20000 | YES | 10 | 22041 | 1.10 | yes | yes | d4c5 |
| middlegame | 50000 | YES | 13 | 80824 | 1.62 | yes | yes | d4c5 |
| middlegame | 250000 | YES | 16 | 294752 | 1.18 | yes | yes | f3e5 |
| endgame | 2000 | YES | 8 | 4001 | 2.00 | yes | yes | b4f4 |
| endgame | 20000 | YES | 12 | 24418 | 1.22 | yes | yes | b4f4 |
| endgame | 50000 | YES | 14 | 72388 | 1.45 | yes | yes | b4f4 |
| endgame | 250000 | YES | 20 | 352119 | 1.41 | yes | yes | b4f4 |

## the three answers
1. **Deterministic: YES, in all 12 cells, 3 runs each.** Not just the bestmove — the entire emitted `info depth`
   sequence (every score, depth, node count and PV, timing fields excluded) was identical run to run. The
   `info string softnodes nodes <X>` line agreed with the last `info` line's node count in every cell.
2. **Finished depth: YES.** The depth reached is a clean integer in every cell with no partial-iteration
   artefact: the reported nodes are the nodes of a completed iteration, and the line the engine emits with them
   is that iteration's line.
3. **How far past N: bounded, but up to ~2x at small N.** The ratio `nodes / N` ranges from 1.08x to 2.06x.
   The worst cases are the smallest budgets — **startpos N=2000 -> 2.06x**, **endgame N=2000 -> 2.00x** — and
   the largest budgets are closer (1.18x-1.51x). So for the owner's `softnodes 2000` self-play, a position can
   cost up to about **4,100 nodes instead of 2,000**, i.e. roughly double, and never more than 4x by design.

## why the overshoot behaves this way (reading, consistent with the source model)
The budget is a finished-iteration target, so the cost of the last iteration cannot be known in advance and the
search always overshoots by that iteration. At depth 1-7 an iteration is a large fraction of 2,000 nodes, so the
overshoot is large; at depth 14-18 an iteration is a smaller fraction of a larger budget, so it is smaller. That
is the expected shape and matches the numbers.

## what matters to the owner
- `go softnodes 2000` for self-play is **safe to rely on being reproducible**: two runs of the same position
  give byte-identical search output, which self-play data generation needs.
- The **cost per position is not exactly 2,000 nodes**; budget ~2x for the worst case, or use a larger N if a
  tighter bound matters. It never exceeds 4N, which is the documented hard cap.
- I did **not** find a defect here. Recording it because file 6 asked for the question to be settled, and
  "deterministic and bounded" is a useful negative result for the owner's training pipeline.
