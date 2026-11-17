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
   **Re-tested under clang (S-F115), since the environment table below predicts behaviour can differ:
   ratio 0.9888 (-1.12 %), CI upper bound 0.9942 — STILL SLOWER, and 2.4x more so.** Same sign on both
   compilers, so this candidate can be dismissed on evidence rather than on one build's noise.
3. **Exploit the refresh cache harder** (S-F112) — turned out to be unnecessary: `replay_ply` already
   passes `state.cache` and `refresh_from_pieces` diffs incrementally, avoiding 99.5 % of rebuild work.

Both patches are committed as `job_v3/*.CANDIDATE.txt` so nobody repeats them. Neither is offered as
a ship.

## THE NEXT JOB, SCOPED (S-F116) — evasion generation
If you have a session to spend, this is where I would spend it, and it is self-contained:

- **The evidence.** `MovePicker::generate_evasions` ranks **3rd** in the gprof ordering on only
  **443,053 calls** — so the cost is per call, not per node. (Use the ordering, not the share; `-pg`
  inflates the many-call symbols.)
- **The code shape.** `src/search.cpp:1051-1090`. It calls `board_.generate_pseudo_legal(buffer_, false)`
  — i.e. it generates **every** pseudo-legal move in a check position, then filters and scores them all.
- **The gap.** There is **no evasion-specific generator**: `Board::GenMode` is only
  `{All, Captures, Quiets}` (`include/forge/board.hpp:186`). A fourth mode that emits only
  check-resolving moves would cut the generation, the scoring loop and the sort together.
- **Why I did not write it here.** It is a move-generation rewrite with a high probability of moving a
  node count. File 7 says a patch that moves one node is not a speed patch, and the identity harness
  (`job_v3/identity.sh`) would almost certainly reject it. That is a session's work with the harness in
  the loop, not an end-of-window patch.
- **Also checked and closed:** `init_check_squares()` does two slider-ray computations per evasion
  generation, but the `FORGE_SEARCH_SPEED2` scorer genuinely needs those squares, so there is no cheap
  win there (S-F116).

Success test for that job, in order: identity first (all three benches + all three evals byte-equal),
then two builds per side, then the timing harness with its three-way verdict. If identity moves, the
patch is not a speed patch regardless of how fast it looks.

## What this means for further work
**Spend the next hour somewhere other than the evaluation update path.** Concretely, the measurement
says the remaining 79 % of bench time is search-side — `Worker::search`, `MovePicker::next`,
`pick_best`, `generate_evasions`, `Board::see_ge` were the top symbols in the gprof profile (S-F104),
and that profile's *shares* are distorted by `-pg` but its *ordering* is not. So move ordering, SEE,
and move generation are where unclaimed time is; the v3 kernels have been tuned already.

## THE MOST IMPORTANT PART FOR TRANSFER: this machine is not the PC
**No result in this folder transfers to the PC without being re-timed there.** Not a caution — a
consequence of four concrete differences, each of which changes which code is fast:

| | here | the PC | why it changes the answer |
|---|---|---|---|
| compiler | **g++ 13.3.0** | **clang** | different inliner, different loop-unroll and auto-vectorisation heuristics; a hand-written specialisation often duplicates what clang's optimiser already emits, or defeats it |
| `-march` | **x86-64-v4** | **znver5** | znver5 tunes scheduling and latency for Zen 5 specifically; the same AVX-512 kernel can have a different critical path on Xeon vs Zen 5 |
| LTO | **none** | **thin LTO** | without LTO the v3 kernels are not inlined across translation units, so per-call overhead looks bigger here than it will on the PC — which is exactly why my "hoist `prepare()`" patch (S-F108) could not show a win |
| PGO | **none** | **yes, profiled with the net loaded** | PGO moves branch layout toward the profiled workload, so branch-shaped micro-optimisations (my count-2 kernel, S-F109) may be irrelevant on a PGO build |

That is the concrete reason file 7 insists every patch is re-timed on the PC before anything is
believed, and it is why I offered both candidates as CANDIDATES rather than as ships. Note in
particular the LTO and PGO rows: **two of my three negative results have a plausible mechanical
explanation in this table**, which is a reason to expect the same patches to behave differently there
rather than a reason to think they would win.

## Instrument notes (so the next person does not repeat my detours)
- **clang 18.1.3 IS available**, contrary to what my first failed build suggested. It needs
  `-isystem /usr/include/c++/13 -isystem /usr/include/x86_64-linux-gnu/c++/13` to find the C++
  headers and `-L/usr/lib/gcc/x86_64-linux-gnu/13 -lstdc++` to link. With those it builds the PC
  tree cleanly, which is how S-F115's clang retest was possible.
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
