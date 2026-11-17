# v3 SPEED WORK — where the time is, and why the obvious wins are already taken

Seat 11. Written for whoever plans further speed work on the owner's net path. Everything here is
measured on **PC r15 source + `-DFORGE_NNUE_V3=1 -DFORGE_MATE_ALPHA_GUARD=1`**, g++ 13.3.0,
`-march=x86-64-v4`, Intel Xeon (AVX-512), TSC 2.400 GHz, PC20 settings + the FABLE_TO_swarm_7 test
net (`fdff70de72e4ca82`), Threads 1, Hash 16.

## The headline
**The v3 evaluation family is ~21 % of `bench 13` time, and inside that 21 % the path is already
near-optimal.** Two of the three obvious micro-optimisations were tried and were neutral or slower;
the third turned out to be unnecessary because the code already does it.

## Where the time actually is (measured, not assumed)
| measurement | value | how |
|---|---|---|
| v3 family share of `bench 13` | **21.1 %** | rdtsc counters in the source + independently measured TSC; agrees to **0.0 pt** at bench 16 |
| per `static_evaluate_v3` call | **0.188 us** | 1,156,108,982 cycles / 2,556,881 calls / 2.400 GHz |
| refresh-cache columns per refresh | **3.62 of 768** | counter instrumentation |
| work the cache avoids vs a full rebuild | **99.5 %** | same |
| v3 cost per node vs the built-in net | **1.11x** | nps ratio, same bench and settings |

## The three attempted wins, and why each failed
1. **Hoist `prepare()` out of the per-evaluation path** (S-F108). Identity clean, speed **ratio
   0.9998, CI [0.9898, 1.0096]** — not proven. `prepare()` already early-returns; the branch costs
   nothing measurable.
2. **Specialise the count-2 AVX-512 change kernel** (S-F109), after measuring that 77 % of updates
   are count 2 (S-F110). Identity clean, speed **ratio 0.9954, CI [0.9913, 0.9989]** — the interval
   excludes 1.0 **on the low side**, i.e. reliably 0.46 % slower. The compiler already hoists the
   invariant `count` checks out of the 16-iteration loop; the extra code hurt the instruction cache.
3. **Exploit the refresh cache harder** (S-F112) — turned out to be unnecessary: `replay_ply` already
   passes `state.cache` and `refresh_from_pieces` diffs incrementally, avoiding 99.5 % of rebuild work.

Both patches are committed as `job_v3/*.CANDIDATE.txt` so nobody repeats them. Neither is offered as
a ship.

## What this means for further work
**Spend the next hour somewhere other than the evaluation update path.** Concretely, the measurement
says the remaining 79 % of bench time is search-side — `Worker::search`, `MovePicker::next`,
`pick_best`, `generate_evasions`, `Board::see_ge` were the top symbols in the gprof profile (S-F104),
and that profile's *shares* are distorted by `-pg` but its *ordering* is not. So move ordering, SEE,
and move generation are where unclaimed time is; the v3 kernels have been tuned already.

Also worth knowing before planning: **the machine that did this work is not the PC.**
- compiler: g++ 13.3.0 here vs the PC's clang
- `-march=x86-64-v4` here vs the PC's `znver5`
- no thin LTO, no PGO here; the PC uses both, with a profile run that has the net loaded

So a patch that wins here may not win on the PC, which is exactly why file 7 says every patch is
re-timed on the PC before anything is believed.

## Instrument notes (so the next person does not repeat my detours)
- **`perf` is not installed** on this machine and there is no root to add it; `/proc/PID/stack` is
  root-only; no gdb, no valgrind. That is why the numbers above come from source instrumentation.
- **`-pg`/gprof is available but distorts by 28 %** (1,198,284 nps instrumented vs 1,666,988 clean),
  inflating many-cheap-call symbols. Use its ORDERING, never its shares.
- **`eval` under v3 calls `evaluate_reference` from fresh accumulators**, not the search's incremental
  path (`src/uci.cpp:729-742`). Timing `eval` does not tell you the search's evaluation cost — this
  caught me once (S-F105).
- The rdtsc diagnostic patch is `job_v3/diag_rdtsc_v3.patch.txt`; it applies with `patch -p1` from
  inside `forge-combo29/`, adds two instructions per evaluation, and leaves bench 13 at 3,652,372
  nodes unchanged (the identity check a diagnostic must pass).

## Evidence
`job_v3/step0_out.txt` (all eleven Step 0 numbers), `job_v3/rdtsc_diag_out.txt` (21.1 %),
`job_v3/cache_hitrate_out.txt` (99.5 %), `job_v3/identity_*.txt` and `job_v3/timing_*.txt` (both
candidates, identity and speed), `job_v3/gprof_flat.txt` (the distorted but correctly-ordered profile).
