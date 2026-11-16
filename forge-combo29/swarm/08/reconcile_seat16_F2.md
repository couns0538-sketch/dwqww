---
cursor:
  subagentId: "bc-e6721c8c-6d0e-5240-aa74-0ea3933103b9"
---

# Seat 16's REFUTES of "stops at M-10 ms" — reconciled against seat 08's 08-F2

**Conclusion: neither finding is wrong; they measure different quantities, and seat 16's mechanism claim is
half right. The rule "`go movetime M` stops at M - Move Overhead" is CORRECT for the WALL clock (the time from
`go` to `bestmove`). It is WRONG as a statement about which iteration the engine gets to keep: the iteration
that crosses the deadline is discarded, so the answer the engine plays is usually the one from an iteration that
finished 1-69 ms EARLY.** Seat 16 read the last completed iteration's time and called that "the stop".

One hour of my work went into this; the numbers are below and everything is on my branch.

## The measurement that separates them

`job4/reconcile.py` records, for the SAME search: the wall time, the last completed depth, and the engine's own
`time` field on that last info line.

| position | movetime | overhead | plan | **wall** | **wall - plan** | last depth | engine `time` field | engine time - plan |
|---|---|---|---|---|---|---|---|---|
| coarse ladder | 50 | 0 | 50 | 52.30 | **+2.30** | 15 | 46 | -4 |
| coarse ladder | 50 | 10 | 40 | 42.26 | **+2.26** | 14 | 31 | -9 |
| coarse ladder | 50 | 45 | 5 | 6.40 | **+1.40** | 10 | 4 | -1 |
| coarse ladder | 200 | 10 | 190 | 192.10 | **+2.10** | 17 | 126 | -64 |
| G open | 50 | 0 | 50 | 51.72 | **+1.72** | 12 | 41 | -9 |
| G open | 50 | 10 | 40 | 41.74 | **+1.74** | 12 | 37 | -3 |
| G open | 50 | 45 | 5 | 6.88 | **+1.88** | 8 | 4 | -1 |
| G open | 200 | 10 | 190 | 191.50 | **+1.50** | 15 | 182 | -8 |
| smooth endgame | 50 | 0 | 50 | 51.55 | **+1.55** | 17 | 32 | -18 |
| smooth endgame | 50 | 10 | 40 | 41.51 | **+1.51** | 17 | 31 | -9 |
| smooth endgame | 50 | 45 | 5 | 6.70 | **+1.70** | 12 | 3 | -2 |
| smooth endgame | 200 | 10 | 190 | 191.39 | **+1.39** | 19 | 121 | -69 |

Wall - plan is +1.4 to +2.3 ms in all 12 rows, at every overhead, every position, every movetime. The `time`
field on the last finished iteration is 1-69 ms BELOW the plan and moves with the position.

So my 08-F2 stands as written ("movetime 50 gives 40 ms of search") — it is about wall clock, which is what a
GUI's flag falls on. Seat 16's numbers are also real, but they are the achieved (kept) iteration, not the stop.

## Why seat 16 saw the same number at overhead 0 and overhead 10

Because for `movetime 50` both plans fit the same whole iteration on their positions (depth 12 ends at 28 ms,
depth 13 at 94 ms, so both 50 and 40 pick depth 12). That is a real property of the engine, and it is the useful
part of their finding — but it is a statement about the ITERATION LADDER being coarse relative to the budget,
not about the overhead subtraction failing. Their own note "depth 13 at 94 ms" already shows the 50 ms and 40 ms
budgets cannot be told apart on that position: both stop inside the same iteration.

## The generalisation: the undershoot is set by the iteration that gets thrown away

12 G positions, `movetime` 50/200, overhead 0/10/45 (`job4/undershoot.tsv`):

| movetime | overhead | plan | median wall | median LAST COMPLETED depth time | median wall - last depth |
|---|---|---|---|---|---|
| 50 | 0 | 50 | 51.8 | 43.8 | 8.1 |
| 50 | 10 | 40 | 41.9 | 32.2 | 9.7 |
| 50 | 45 | 5 | 6.6 | 5.1 | 1.5 |
| 200 | 0 | 200 | 201.9 | 143.6 | 58.3 |
| 200 | 10 | 190 | 192.0 | 142.3 | 49.7 |
| 200 | 45 | 155 | 156.7 | 121.7 | 35.0 |

The achieved time is the plan MINUS the part of the running iteration that was discarded. It grows with the
budget because the last iteration is a bigger share of a bigger budget.

## The two stop paths have OPPOSITE error modes (this is the correction worth having)

| path | where the deadline is checked | what is lost | measured |
|---|---|---|---|
| `go movetime M` | INSIDE the search (`should_stop`, hard limit) | the whole partial iteration | wall = plan + 1.7 ms; kept iteration 1-69 ms early |
| `go wtime` (soft limit) | at the END of an iteration (`search.cpp:2612`, `if (elapsed >= soft_basis*factor) break;`) | nothing — no iteration is thrown away | undershoot 0.0 ms in 40 of 40; the search OVERSHOOTS soft by up to a whole iteration |

`job4/mtg.tsv`: movestogo 1 plan soft 495 -> median wall 347.3 (70 %), spread -271..+299 ms; movestogo 2 plan
330 -> 283.0; movestogo 40 plan 24 -> 23.7; no movestogo plan 45 -> 39.3. **Undershoot is exactly 0.0 in every
clocked row** — the wall time equals the last completed depth's time, because a clock stop discards nothing.

This also EXPLAINS my 08-F9 rather than contradicting it: on a clock the engine stops at an iteration boundary,
so if iterations are long the search ends well short of soft (the 0.6-0.8 factor of 08-F9 is the same
granularity effect seen from the other side). 08-F9's own mechanism sentence ("`factor` multiplies the soft
deadline") is what I read in the source, and it is real (`TmEffortBase`, `TmMinFactorPercent`), but the
dominant term for long iterations is this boundary behaviour.

## The two tests the coordinator asked for

**Does `movestogo` change the undershoot pattern?** Yes, decisively, in the opposite direction: with `movetime`
the engine undershoots its plan by discarding a partial iteration; with `movestogo` it undershoots soft by
nothing at all (undershoot 0.0, 40/40) and instead overshoots soft by up to a whole iteration (+299 ms on a
495 ms plan). Table above.

**Does a coarse depth ladder undershoot by a whole iteration more than a smooth one?** Not as a clean rule, and
I will not claim one. `job4/ladder.tsv`, 6 positions x movetime 50/100/200:

| position class | median undershoot |
|---|---|
| smooth endgame | 40.1 ms |
| smooth pawns | 36.6 |
| coarse tactical | 20.3 |
| smooth K+R | 19.8 |
| coarse open | 16.0 |
| coarse mid | 14.5 |

The two SMOOTH positions undershoot the most and the coarse ones the least — the opposite of the hypothesis, on
6 positions. The honest reading: the undershoot is bounded by the cost of the abandoned iteration, which is
larger for smooth positions (many small iterations, so the abandoned one is a bigger absolute slice of the
budget) and can be either large or small for coarse ones depending on where the deadline falls. With 6
positions this is a direction, not a rule. `job4/correlation.txt` shows undershoot / last-iteration-cost ranging
0.20 to 12.91 — no single ratio, so no clean predictor.

## What this changes in my findings

- **08-F2: unchanged and strengthened.** The wall-clock statement is right at every overhead (plan + 1.4..2.3 ms).
  I am adding the missing half: the KEPT iteration is 1-69 ms below the plan, so "movetime 50" buys 40 ms of
  wall clock and typically a 32-44 ms iteration.
- **08-F9: restated.** "Engine spends 55-79 % of its planned soft limit" is a statement about the last COMPLETED
  iteration relative to soft, which is the iteration-boundary effect; on a clock nothing is discarded.
- **08-F8: unaffected** (it is about the hard limit being reached, which it is).
- Nothing I reported was derived from the engine's `time` field being mistaken for wall clock; my timing harness
  uses `time.monotonic()` around the `go`/`bestmove` exchange, and the `nlines >= 2` audit confirms every
  record was a real search.

## Files

- `/agent/repos/dwqww/forge-combo29/swarm/08/job4/reconcile.py`, `reconcile.tsv` — the wall vs engine-time split
- `/agent/repos/dwqww/forge-combo29/swarm/08/job4/movetime_undershoot.py`, `undershoot.tsv`, `summary.txt`
- `/agent/repos/dwqww/forge-combo29/swarm/08/job4/mtg_undershoot.py`, `mtg.tsv`, `mtg_summary.txt`
- `/agent/repos/dwqww/forge-combo29/swarm/08/job4/ladder_test.py`, `ladder.tsv`, `ladder_summary.txt`, `correlation.txt`
- `/agent/repos/dwqww/forge-combo29/swarm/08/job4/mechanism.txt`

Show it again: `cd forge-combo29/swarm/08/job4 && python3 reconcile.py ~/builds/release/forge /tmp/r.tsv`
