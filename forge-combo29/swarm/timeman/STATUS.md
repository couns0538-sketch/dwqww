# STATUS

Seat: owner-audit, time-manager accounting, topic `swarm/timeman`.
Audit base: `6b98f217` (a divergent commit, NOT an ancestor of `main`).

## Where this stands

| # | Item | State |
|---|------|-------|
| 0 | Build + four honesty pins | **DONE** — 312,866 / 862,329 / 3,024,920 / perft 5 4,865,609 |
| 1 | Increment accumulation over real games, 4 controls | **DONE** — 200 games |
| 2 | `movestogo` + fallback clock (the recorded gap) | **DONE** — base and patched |
| 3 | `movetime` accuracy as floor/ceiling | **DONE** |
| 4 | Sudden death vs increment; clock below the floor | **DONE** |
| 5 | Threads 1 vs 4 | **DONE (cheap arm only)** — one position, both thread counts |

## Two inherited claims I had to withdraw or correct

1. **"`movestogo 0` means SUDDEN DEATH" is wrong for this source tree.** `src/uci.cpp:117`
   is `limits.moves_to_go = std::max(1, read_int())`, so `0` and `-1` are rewritten to `1`
   *before* `clock_plan.hpp:37` ever sees them. At a 2000 ms clock the plan for `movestogo 0`
   is **995/1592**, exactly the `movestogo 1` plan — not the sudden-death plan (90/450), and the
   measurement follows the plan. The earlier reading described the **pre-clamp** value. The
   `>50 → 50` clamp *does* hold, and it is real.

2. **"Hard limit is 60% of soft" is the wrong description of this planner.** The hard limit is
   `min(available × 60/100, soft × 5)`. In sudden death `soft = available/22`, so `5 × soft`
   ≈ `0.227 × available`, which is *below* `0.6 × available` at every clock I tested (2000 down
   to 60 ms) — so **the `5×soft` term binds and hard is 5× the soft plan**, not 0.6× of it.
   The 60% figure does bind where `available` is large relative to soft, which is not sudden
   death.

## One finding of my own, withdrawn

A 3000+200 game appeared to flag. Two separate harness faults produced it, and both are now
fixed with a self-check that fails loudly:
- the clock was charged **wall** time rather than the engine's own `time` field (one move's tail
  was 452 ms over a 185 ms search);
- **Black's clock was sent in `wtime`**, so a Black move was planned off White's clock. Fixing
  the field, 42 isolated replays of the "overrun" position at that exact clock produced
  **0 of 42** moves over the hard plan.
With both fixed: **0 forfeits**. Recorded as withdrawn, not as a defect.

## Not started

Nothing assigned is unstarted.
