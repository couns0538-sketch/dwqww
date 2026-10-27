# S24 [Sol leftover, OPTIONAL] int32 shelf cleanup — DONE (22-line follow-up patch)

`SOL_LEFTOVERS_FOR_CLAUDE.md` section 2 item 33 (inventory S24, optional, last). Branch `opus-sol-S24` = `d4f4312` +
`0d99f02` cherry-picked + this job. Deliverable: **`forge_sol_S24_int32guards_20261027.patch`**, a follow-up on top
of Sol's shelved exact-int32 patch `forge_sol_exactint32_h256e12_20261025.patch` (sha256 e661a145…, from Sol's
branch), not a resubmission. The branch carries the patch and evidence only; no engine source is changed on it
(`[skip ci]`).

## What the follow-up does (22 changed lines: 19 added, 3 removed; src/nnue.cpp + src/uci.cpp)
It puts every Job A default-build leak under `#if FORGE_NNUE_EXACT_INT32_AVX2`:
1. **The dead UCI option.** `option name NnueExactInt32 ...` and its `setoption` branch exist only in experiment
   builds; default builds ignore the name like the lock.
2. **The extra stats line after bench.** `info string NnueExactInt32 stats ...` is printed only in experiment
   builds.
3. **The unconditional thread_local counters.** `++current_stats.{refreshes,updates,evaluations}` in
   `refresh`/`update`/`evaluate` (every NNUE node) become `FORGE_NNUE_COUNT(...)`, which is `((void)0)` when OFF.
   The `thread_local` itself exists only in experiment builds; OFF builds return zero stats.

## Acceptance (Sol's pass line)
| line | result | evidence |
|---|---|---|
| <= 30 changed lines | **PASS**: 22 | the patch |
| default build's uci list byte-identical to the lock's | **PASS**. Lock and guarded-OFF exes give the same 12 `id`/`option` lines. Without the follow-up (shelf OFF) there are 13: the extra `option name NnueExactInt32 type check default false` | `logs/step2_uci_and_bench_vs_lock.log` |
| default build's bench output byte-identical to the lock's | **PASS**. `bench 13` output equal to the lock's with time/nps masked (the only run-dependent fields): one line, 862329 nodes. Without the follow-up there is an extra `info string NnueExactInt32 stats refreshes 8 updates 655136 evaluations 533258 ...` line | same |
| Std pass | **PASS**. Guarded OFF, box recipe: `uci_check.py --full` ALL OK (bench 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690); FMA 0; 0 warnings | `logs/step3_identity_guarded_off.log`, `logs/step1_builds.log` |
| reproducible from scratch | **PASS**. `verify_s24.sh` on a clean LF archive of d4f4312 + e661a145 + this patch: uci list IDENTICAL, bench 13 output IDENTICAL, ALL OK | `logs/step5_verify_from_scratch.log` |
| experiment still works when ON (sanity, not required) | **PASS**. `-DFORGE_NNUE_EXACT_INT32_AVX2=1`: the option is advertised; `setoption ... true` before bench prints `info string NnueExactInt32 active`; bench 13 = 862329 nodes (exact) with int32_refreshes 8 and int32_updates 655136 (every accumulator built on the int32 path) | `logs/step4_on_sanity.log` |

## How it was checked
- e661a145 applies cleanly (`git apply --check`, then apply) to the AL1 lock tree `d4f4312`, the current lock.
  The shelf was cut on h256_e12, but AL1 differs only in its net (S47 Part A), so the comparison is against the
  AL1 lock exe (sha256 5d4df7f1…).
- The follow-up applies to e661a145's result: `patch -p1` / `git apply -p1` with LF files, as stored in git.
- Builds: the PC box recipe (`build_pc.sh`, g++ 15.2, -O3 -DNDEBUG, znver5, static), nice 19, under
  `F:\opus_scratch\sol_S24`.

## Left / UNVERIFIED
- Not CMake/CTest- or CI-tested: the branch carries no engine change. The patch touches only preprocessor guards
  and one counting macro.
- OFF-build code is not byte-identical to the lock. e661a145's `evaluate()` refactor and its option-snapshot
  plumbing (`exact_int32_option`, the uci freeze flag, the announce helper) stay compiled. They produce no output
  and change no node count; the spec asks only for the UCI list and bench output. No speed measurement and no
  speed claim.
- Shelving and any future int32 path remain Sol's/CR's call (S21: an int16 path needs a different scale).
Machine exclusive: no.

## Files
`forge_sol_S24_int32guards_20261027.patch`, `verify_s24.sh` (rebuilds and compares from scratch), `README.md`,
`IDEA_SOURCE.md`, `REPORT.md`, `logs/` (steps 1-4), `FILES.txt`, `SHA256SUMS`.
