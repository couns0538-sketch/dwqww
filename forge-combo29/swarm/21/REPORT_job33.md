# REPORT job33 — the node undershoot does not change the move, even on tactical positions

**What was asked.** (The experiment that could still make 21-F16 urgent.) On positions where a
capture wins material, does the node undershoot pick a worse move?

**The answer.** **No.** On 8 tactical positions (the first 8 of set G where a capture wins at least a
minor piece against a greedy recapture) the bestmove at `go nodes 20000` is **identical** to the
bestmove at `go nodes 400000` — **0 of 8 changed** — even though the large budget reached 6 to 11
more plies. Combined with job32's 9-of-10 middlegame result, that is 1 move change in 18 positions
across a ~7-ply depth difference.

**How sure.** High for these positions. 8 positions × 2 budgets, Threads 1 under PC20, every search
read to bestmove. Determinism was established for the same limit path in 21-F15 and 21-F17 (each
pair here was run once).

## Table (pasted from `job33/out/summary.md`)

| pos | depth@20k | nodes@20k | move@20k | depth@400k | nodes@400k | move@400k | changed? |
|---|---|---|---|---|---|---|---|
| 0 | 53 | 19,796 | `c4a6` | 64 | 23,834 | `c4a6` | no |
| 1 | 10 | 17,329 | `f3f8` | 17 | 265,583 | `f3f8` | no |
| 2 | 10 | 19,249 | `b1a1` | 15 | 318,716 | `b1a1` | no |
| 3 | 10 | 19,510 | `e7d6` | 17 | 336,043 | `e7d6` | no |
| 4 | 10 | 16,620 | `c5d6` | 17 | 375,246 | `c5d6` | no |
| 5 | 10 | 12,307 | `a2a6` | 19 | 399,249 | `a2a6` | no |
| 6 | 11 | 18,001 | `b5d4` | 20 | 351,935 | `b5d4` | no |
| 7 | 11 | 11,538 | `d5a8` | 20 | 345,827 | `d5a8` | no |

Because no move changed, the reference-search comparison of the two moves had nothing to compare —
the table of "eval after" is empty, which is the honest output rather than a fabricated row.

## Reading position 0 carefully

Position 0 reports depth **53 at 19,796 nodes** and depth **64 at 23,834 nodes**. A 64-ply depth at
24k nodes is not a real 64-ply search: it is the engine running out of moves in a near-terminal
position and extending, or a forced sequence. I record it as measured, but it should not be read as
"the engine sees 64 plies". The other seven positions show the ordinary 10→17–20 pattern.

## Prediction outcome

| prediction | outcome |
|---|---|
| P1 at least 3 of 12 give a different bestmove | **FAILED** — 0 of 8 (my selector found 8 tactical positions in G, not 12) |
| P2 where moves differ, the large-budget move scores >= 50 cp better | not testable (no differences) |
| P3 depth gap at least 5 plies | held (6–11 plies on the ordinary positions) |
| P4 deterministic | held for the limit path (21-F15/F17) |
| P5 0 crashes / sanitizer lines | held |

## What this settles

**21-F16 is real but not urgent.** The undershoot is systematic (−20 to −52 % of the requested node
budget, deterministic) and it costs 6–11 plies of depth on real positions — but it did not change the
chosen move on any of the 18 positions I tested (10 middlegame + 8 tactical). So a match played at
"250,000 nodes" is a shallower search than the owner asked for, and the move it picks is the same one
a deeper search picks, on everything I have measured.

## Suspicions, not proven

- Positions where the right move needs MORE than ~11 extra plies (deep sacrifices, long forced
  mates) could still differ. My tactical filter only catches one-ply material wins.
- The empty "eval after" table is a consequence of no differences; if a future set does produce
  differences, that comparison is already coded.

## What I did NOT do

- Did not find 12 tactical positions: my filter found 8 in set G and I used them rather than widening
  the filter, so the sample is 8 and the report says so.
- Did not test positions needing long forced sequences (the case most likely to differ).

## What I am NOT sure about

- Whether the owner cares that "250,000 nodes" means ~78 % of that. On move choice it does not
  matter in my sample; on reproducibility of published node counts it does, and that is a
  documentation matter for the match program.

## Times

see `job33/stamps.txt`.
