# REPORT — seat 07, job 50: check of 02-S-F13 (the owner's clock is barely used)

## What was asked / the answer / how sure

**Asked:** (cycle work) seat 02's **S-F13** / **S-C6** claims the owner's 6 s + 0.06 clock is used at only
3.3–5.8 %, and that `go wtime 6000 btime 6000 winc 60 binc 60` gives 362 ms / depth 19 — **identical to
`go depth 19`** — while `go movetime 6000` gives 5,990 ms / depth 27. If true, the match format's clock is
not doing what it looks like it is doing.

**Answer:** **confirmed, and reproduced to within 0.5 ms.**

**How sure:** high. Two runs per cell, wall clock timed, and the `movetime` control proves the harness can
see a long search.

## Results (PC r15 under PC20, Threads 1, Hash 16, fresh process per cell)

| cell | run 1 | run 2 | depth | bestmove |
|---|---|---|---|---|
| `go wtime 6000 btime 6000 winc 60 binc 60` | **361.5 ms** | 358.8 ms | **19** | `e2e4` |
| `go depth 19` | 360.6 ms | 353.7 ms | **19** | `e2e4` |
| `go movetime 6000` | **5,990.8 ms** | 5,990.8 ms | **27** | `e2e4` |

- The 6 s clock consumes **6.0 %** of its budget; `movetime` consumes **99.8 %** and reaches **8 plies
  deeper**.
- The clock answer is **indistinguishable from a fixed-depth-19 search** in **time, depth and move** —
  three independent quantities agreeing is much stronger than one.
- Seat 02 measured 362 ms / depth 19 / 650,246 nodes. **My wall time reproduces theirs to within 0.5 ms**,
  on my own harness.

## The control that makes the utilisation number trustworthy

`go movetime 6000` ran **5,990.8 ms** in both runs. So the harness demonstrably observes a search that
uses its whole budget; the 6 % figure is a property of the clock path, not of a harness that cuts searches
short.

## What this means, and what it does not

**Means:** on startpos, the time manager's **soft target** (`plan_clock_budget` gives soft ≈ 317 ms on a
6 s clock with these tunables — seat 02 computed the same figure) is reached long before the 6 s budget,
so the move is effectively chosen by the soft plan and then a stability factor, not by the clock running
out. The clock is doing bookkeeping while the search does 19 plies' worth of work and stops.

**Does not mean** the clock is broken or that the engine loses on time — 07-C7 showed nine clock controls
with zero overruns. It means the *budget* is under-used, which is a strength question (more time available
than used), not a safety one.

**Scope, stated plainly:** this is **startpos**. Seat 02's own S-F14 **withdraws** the median-ordering
claim across position classes and keeps only the tail claim, so what transfers from my check is "the clock
is barely used on startpos", not "on every position". I did not run their 20-board class set.

## Findings

**07-C50** in FINDINGS.md.

## Suspicions, not proven

- That the gap between 6 % and 100 % utilisation is entirely the soft-plan plus stability factor. Seat 02
  computed soft ≈ 317 ms from `include/forge/clock_plan.hpp` with PC20's values, which is consistent with
  the 361 ms I measure, but I did not instrument which factor ended the search.

## What I did NOT do

- Did not run multi-board or multi-class clocks; 07-C7 already covered nine clock controls for safety, and
  seat 02 covers classes.
- Did not test clocks other than 6 s + 0.06.

## What I am NOT sure about

- Whether the under-use is a defect or the intended design. The engine has a soft/hard plan and the tunables
  are deliberate; whether a 6 s clock *should* use 6 s is the owner's judgement, not something a
  measurement settles.

## Times

See job50/stamps.txt.
