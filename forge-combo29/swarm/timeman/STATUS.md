# STATUS

Seat: owner-audit, time-manager accounting, topic `swarm/timeman`.
Audit base: `6b98f217` (a divergent commit, NOT an ancestor of `main`).

## Where this stands

| # | Item | State |
|---|------|-------|
| 0 | Build + four honesty pins | **DONE** — 312,866 / 862,329 / 3,024,920 / perft 5 4,865,609; re-verified on the patched build |
| 1 | Increment accumulation over real games, 4 controls | **DONE at 3 of 4 controls** — 146 games / 19,084 plies. 10000+1000 still running at close: **absent, not zero** |
| 2 | `movestogo` + fallback clock (the recorded gap) | **DONE** — base and patched, incl. the clamp |
| 3 | `movetime` accuracy as floor/ceiling | **DONE** — 300 requests, 0 timeouts |
| 4 | Sudden death vs increment; clock below the floor | **DONE** — incl. the 111 ms floor derived as an equilibrium |
| 5 | Threads 1 vs 4 | **DONE (cheap arm only)** — one position, both thread counts |
| — | §1 placeholder in FINDINGS.md | **FIXED** — §1 written from the completed 3 controls |

## Two inherited claims I had to correct

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

## A third inherited claim, downgraded rather than withdrawn

**"The planner formula reproduced all 3,071 moves within +2.1 ms" does not reproduce** on this
seat's controls. At 200+0 it holds to ±2 ms on 84.5% of moves, but at **1000+100 only 2.2%** and at
**3000+200 only 1.1%**. The plan is a **bound**, not a prediction: no move exceeded its hard plan
except one at 1.0015×, and utilisation peaks at 59.6% — but the median move uses ~74% of its soft
plan, not ~100%. The original figure should be read as "the plan was never exceeded".

## One finding of my own, withdrawn

A 3000+200 game appeared to flag. Two separate harness faults produced it, and both are now
fixed with a self-check that fails loudly:
- the clock was charged **wall** time rather than the engine's own `time` field (one move's tail
  was 452 ms over a 185 ms search);
- **Black's clock was sent in `wtime`**, so a Black move was planned off White's clock. Fixing
  the field, 42 isolated replays of the "overrun" position at that exact clock produced
  **0 of 42** moves over the hard plan.
With both fixed: **0 forfeits**. Recorded as withdrawn, not as a defect.

## One row of my own table was noise, and is now marked as such

Own-clock `movestogo 2` read 379 ms (base) vs 751 ms (patched) — a 2× gap on a path the patch
should not touch. Re-measured with **12 interleaved ABBA runs per build**: ranges 367–1349 vs
204–1359 ms, sd 300–360 ms *within* each build. **Noise**, and a depth-12 identity control agrees
between builds exactly (`e1g1`, 113,145 nodes). FINDINGS.md §2 states this beside the table and §7
warns against quoting single-run milliseconds from it.

## Method rule added to FINDINGS.md

**A pin check on a build whose compile failed checks the previous binary.** `cmake --build`
returned rc=1 while `check_pins.sh` printed `PINS MATCH`; the binary was byte-identical to the
unpatched build (`cmp`). Now a stated RULE in §2 with three required practices (`rm -rf` the build
dir, assert the link happened, `cmp` when the patch should change behaviour).

## Not done, and why

- **10000+1000 control.** Still running at close (~2 min/game, 50 games). Its numbers are missing
  from §1 rather than reported as clean.
- **`movestogo` + fallback with a NON-ZERO increment.** §2 used increment 0 throughout. Named in
  §7 as the same class of gap one level down.
