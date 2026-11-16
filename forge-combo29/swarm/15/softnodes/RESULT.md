# `go softnodes N` on the PC build under PC20 — determinism, finished depth, overshoot

**Short answer:** `softnodes` is **fully deterministic** (5 runs, identical score, nodes and bestmove,
15 of 15 rows) and its reported depth is **always a completed iteration** (no gaps in the depth
sequence, 15 of 15). But it **overshoots N by far more than "one depth's worth"** — up to **+233 %** at
N=500 and **+106 %** at the PC's own self-play setting of N=2000 — and one row finished *under* N.

PC build (r15), **PC20**, **Threads 1**, Hash 16. Script `softnodes.py`, 5 boards × N ∈ {500, 2000,
20000} × 5 repeats. Prediction was committed and pushed before any measurement. Raw:
`softnodes_out.txt`, per-row data `softnodes.jsonl`.

## The table

| board | N | depth reached | nodes | vs N | deterministic |
|---|---|---|---|---|---|
| startpos | 500 | 5 | 971 | **+94.2 %** | yes |
| startpos | 2000 | 7 | 4,121 | **+106.1 %** | yes |
| startpos | 20000 | 12 | 21,600 | +8.0 % | yes |
| G-mid-1 | 500 | 4 | 626 | +25.2 % | yes |
| G-mid-1 | 2000 | 7 | 2,671 | +33.5 % | yes |
| G-mid-1 | 20000 | 12 | 31,779 | **+58.9 %** | yes |
| G-mid-2 | 500 | 5 | 532 | +6.4 % | yes |
| G-mid-2 | 2000 | 8 | 3,312 | **+65.6 %** | yes |
| G-mid-2 | 20000 | 11 | 21,089 | +5.4 % | yes |
| G-end-1 | 500 | 4 | 1,667 | **+233.4 %** | yes |
| G-end-1 | 2000 | 5 | 3,496 | **+74.8 %** | yes |
| G-end-1 | 20000 | 8 | 27,098 | +35.5 % | yes |
| G-end-2 | 500 | 6 | 442 | **−11.6 %** | yes |
| G-end-2 | 2000 | 7 | 2,025 | +1.2 % | yes |
| G-end-2 | 20000 | 12 | 24,501 | +22.5 % | yes |

## Answers to the three questions file 6 asked

**1. Is it deterministic run to run?** **YES.** Every one of 15 (board, N) cells gave an identical
`(score, nodes, bestmove)` across 5 repeats. This is the property self-play depends on, and it holds.

**2. Does it stop at a finished depth?** **YES.** In every row the depths printed are exactly
`{1, 2, …, D}` with no gaps and D is the maximum printed — so the stop happens at an iteration
boundary, not in the middle of one. That is what "stops at the end of the first depth after N nodes"
should mean, and it is what happens.

**3. How far past N does it go?** **Much further than the description suggests.** The overshoot is the
size of the *whole next depth*, which is not a small correction:

- at N=2000 (the PC's own self-play value) it ranges **+1.2 % to +106.1 %**;
- at N=500 it reaches **+233.4 %** (G-end-1: 1,667 nodes for a 500 budget);
- at N=20000 it is smaller (+5.4 % to +58.9 %) because one depth is a smaller fraction of a large budget.

The mechanism is visible: the engine checks the node budget between iterations, so the final depth
completes however many nodes it needs. When a depth's cost is 1,167 nodes on a 500 budget, you get
1,667. **The overshoot is therefore not a constant or a small margin — it is "whatever the next depth
costs", which can be more than double the budget.**

**4. One row finished UNDER N.** G-end-2 at N=500 reports **442 nodes (−11.6 %)**. That is below the
budget, so the stop was triggered by something other than reaching 500 nodes — most plausibly the
position being resolved (a forced mate found) or the depth limit being reached. I did not instrument
this, so I state the observation and not a cause.

## My prediction, honestly

| # | prediction | verdict |
|---|---|---|
| P1 | deterministic across 5 reps | **HELD** |
| P2 | finished depth, no gaps | **HELD** |
| P3 | overshoot ≤ 20 % (kill at > 50 %) | **REFUTED — KILL TRIGGERED**: 6 of 15 rows exceed 50 %, max +233.4 % |
| P4 | softnodes 2000 stops at depth 4–12 | **HELD** (depths 5, 7, 7, 7, 8) |
| P5 | legal bestmove everywhere | **HELD** |

P3 was my mistake, and it is worth naming what I got wrong: I assumed "one depth past N" would be a
modest fraction of N. For small N it is not — a depth can cost more than the whole budget. My 20 % band
was a guess about magnitude that I did not derive from anything.

## Why this matters for the owner

The PC's self-play budget is `softnodes 2000`, and the honest description of what that buys is
**"2,000 nodes plus the remainder of the next depth"**, which in these five positions meant
**2,025 to 4,121 nodes — up to twice the intended workload.** If the self-play's node budget is being
used to control compute per game, the real cost can be roughly double on some positions. If it is only
used to make the search cheap and deterministic, it is doing that job perfectly.

## Scope

- 5 boards (startpos, 2 middlegames, 2 endgames), one build, one regime (PC20), Threads 1, and N of
  500 / 2000 / 20000. Not a survey.
- I did **not** test `go nodes N` for comparison in this job, nor the clock path.
- I did not instrument *why* G-end-2 finished under N; that is stated as an open observation.
