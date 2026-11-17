# REPORT — seat 07, job 57: check of 28-S-F44 (the fixed-point clock floor)

## What was asked / the answer / how sure

**Asked:** (cycle work) seat 28's **S-F44** calls itself "the strongest safety statement in this work,
exact rather than measured": with `clock' = clock − spend + increment` and the hard cap as implemented,
the floor is `MoveOverhead + increment·100/TmHardPercent = 110 ms`, and iterating the real rule
converges to **111 ms from every starting clock**.

**Answer:** **confirmed exactly — and I added the engine-side check the arithmetic assumes.**

**How sure:** very high. Part A is exact arithmetic reproducing their number to the millisecond; Part B
measures the behaviour the arithmetic depends on.

## Part A — the arithmetic (both halves reproduce)

Re-implemented `plan_clock_budget` from `include/forge/clock_plan.hpp` with PC20's tunables
(`TmSoftDivisor 22`, `TmIncrementPercent 75`, `TmHardPercent 60`, `TmHardSoftMultiple 5`,
`MoveOverhead 10`), then iterated `clock' = clock − spend + increment` with `spend = hard`, `increment 60`:

| start clock | fixed point |
|---|---|
| 6000 | **111 ms** |
| 3000 | 111 |
| 1000 | 111 |
| 500 | 111 |
| 300 | 111 |
| 200 | 111 |
| 150 | 111 |
| 120 | 111 |
| 115 | 111 |
| 111 | 111 |
| 110 | 110 |
| 109 | 110 |

**Every start ≥ 111 converges to 111**, and 110/109 stay at 110 — exactly seat 28's result, including
their note that integer division gives 111 where the closed form gives 110. The convergence path is
visible too (e.g. from 300: 186 → 141 → 123 → 116 → 111), so this is the real rule iterating, not a
constant substituted for it.

## Part B — the engine behaves as the arithmetic requires

The floor argument assumes `spend` can be capped at `hard` as the clock shrinks. Measured on the PC build
under PC20, Threads 1, Hash 16, `winc 60`:

| clock | actual spend | vs the 60 ms increment |
|---|---|---|
| 6000 | **361.1 ms** | exceeds it (the 6 % utilisation case of 07-C50/C52) |
| 1000 | 55.5 ms | **within** |
| 300 | 41.9 ms | **within** |
| 150 | 43.9 ms | **within** |

So once the clock is small, **spend falls inside the increment and the clock stops draining**. The floor is
reached, not crossed. That is what turns S-F44 from an algebraic identity into a safety statement.

## What this explains

**07-C7 measured zero overruns across nine clock controls but could not say why.** This does: the clock
cannot drain past ~111 ms at this increment because the search spends less than the increment replenishes
there. The two findings fit together into one account of the engine's time safety.

## Findings

**07-C57** in FINDINGS.md.

## Suspicions, not proven

- That the floor holds at increments other than 60. The formula predicts `10 + increment·5/3`, so at
  `winc 0` the floor collapses to ~10 ms and there is no safety margin at all — worth checking if the owner
  ever uses a zero-increment time control.

## What I did NOT do

- Did not test other increments or `movestogo` (which changes the plan branch entirely).
- Did not verify `TmHardPercent` etc. are at their compiled defaults in the PC build; I read them from the
  source's tune block, which is what the owner's build uses unless overridden.

## What I am NOT sure about

- Whether `spend <= increment` at 1000 ms and below is robust to a machine under load; all my runs were on a
  quiet box. On a loaded machine the search could overshoot `hard` in wall time and the margin could erode.

## Times

See job57/stamps.txt.
