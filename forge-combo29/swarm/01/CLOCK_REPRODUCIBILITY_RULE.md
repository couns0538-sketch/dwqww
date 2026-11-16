# The clock-budget rule: reproducible only to a PLATEAU

**Seat 01, 2026-11-16. Evidence: `clockquant/check_clock_quantisation.txt`. Reconciles seat 20's S-F49 with
seat 28's S-F43.**

> ## THE RULE (put this at the top of any clock-harness notes)
>
> **A clock budget is reproducible only to a PLATEAU. Sweep the clock to find one, then confirm with two or
> three repeats that the budget is not sitting on an iteration boundary.**

## Why

A clock search stops at the **end of a completed iteration**. So the node count and the depth are a **step
function** of the clock: long plateaus where a wide range of clocks give the identical answer, and sharp jumps
between them.

Measured on one board, PC r15 + PC20, Threads 1, Hash 16, winc = binc = 60, 15 clocks from 900 to 1600 ms:
**only 4 distinct (depth, nodes) outcomes**. Five repeats at the middle of the longest plateau gave **one
distinct outcome** (depth 14, 97,289 nodes, 5 of 5).

## Why two seats appeared to disagree

| seat | observation | what it actually measured |
|---|---|---|
| seat 20, S-F49 | depth and nodes flip between 17 and 18 as ~5 ms decides whether the 18th iteration completes | a point **on** an iteration boundary |
| seat 28, S-F43 | identical depth 18, identical 998,994 nodes, 3 solo and 3 loaded runs | a point **inside** a plateau |

**Both are right, and neither is a defect.** The disagreement was not about the engine; it was about where in
the step function each measurement sat. A contention-stressed run therefore measures a **lower rung of the same
ladder**, not something wrong.

## The companion rule: a boundary is proven by repeats, not by one reading

My own sweep had **one** depth-14 reading at clock 1350 ms sitting between depth-15 readings at 1300 and 1400.
My first reading was "boundary artefact". **Six repeats at 1350 gave depth 15 / 121,306 nodes in 6 of 6** — that
point is *not* a boundary; the single 14 was a one-off slow run.

> **A boundary is proven by repeated flips at one clock, never by a single out-of-band reading.** A one-off
> anomaly and a genuine boundary look identical in a single sweep.

This is the **same species as the sample-size lesson** (`TWO_GUARDS_CHECKER_AND_SAMPLE.md`): one observation is
not a distribution, and the second guard — repetition — is separate from the first, which only proves the
instrument works.

## Practical checklist for a clock harness

1. **Sweep** the clock finely enough to see the plateaus (steps of ~50 ms were enough here).
2. **Place** the budget in the middle of a plateau, not at an edge.
3. **Repeat** twice or three times at the chosen budget. If the repeats differ, you are near a boundary: move
   the budget and repeat.
4. **Report the plateau**, not a single reading: "clocks 900–1150 all give depth 14 / 97,289 nodes" is a
   reproducible statement; "clock 1000 gives depth 14" is not, because it hides where the next rung is.
5. For exact reproducibility use `go nodes N` instead — but remember it reports only completed iterations, so
   add the same allowance on both sides of any cost comparison (S-F57).
