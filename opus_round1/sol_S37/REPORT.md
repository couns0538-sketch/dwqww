# S37 [Sol leftover] NNUE inference microbench + per-stage cost table — DONE

Branch `opus-sol-S37` = `d4f4312` + `0d99f02` cherry-picked (`842e3bce`) + `20f55fab` (tool + evidence) +
`fe3e5e4a` (CI evidence, `[skip ci]`). Patch: `forge_sol_S37_nnue_microbench_20261027.patch` (3 files, +1105:
`tools/nnue_microbench.cpp`, `tools/nnue_microbench_wac300.epd` = lock archive `4_tests/suites/wac300.epd` sha256
9bfb7b42…, 7 CMake lines). No engine source touched. Machine exclusive: **no**; timings are PC (AMD Zen 5, TSC 4.70
GHz) at IDLE on CPUs 4-11 under gate + training + self-play load: advisory only, no speed claim. Sol left no S37 files.
Work and results by a sub-agent; this report text is its hand-back.

## 1. What was done
- `tools/nnue_microbench.cpp`, own CMake target `forge_nnue_microbench` (CTest `forge_nnue_microbench_check` runs its
  consistency checks only). It links forge_core and times the engine's own code, single-threaded: `nnue::refresh`,
  `nnue::dirty_pieces`, the three `nnue::update` paths, `nnue::evaluate` (output layer), a bit-exact activation/affine
  replica (the output layer split in two), `Worker::static_evaluate` (refresh / lazy-update / valid-accumulator
  paths, via the SearcherTestProbe friendship the tests already use) and `Evaluator::evaluate_uncached`.
- Corpus: the 8 bench FENs + WAC300 + deterministic random walks (1-8 plies, LCG) -> 10,000 positions (dedup by
  Zobrist key), 346,182 update pairs (quiet 310,219 / capture 35,664 / castle 299). Same FEN dump (sha256 d238dc06…)
  in all 12 final runs.
- Timing: regions (chunks of 32; output/activation/affine 4x on hot accumulators; updates kind by kind, <= 32 parents
  per region) read the TSC and the thread CPU time (QueryThreadCycleTime; Linux CLOCK_THREAD_CPUTIME_ID), minus the
  measured empty-region overhead; 15 passes per run -> median/p90; plus 2 per-call rdtsc passes -> per-call median/p90.
- Builds (PC lock recipe, `build_microbench_pc.sh`): avx2 = lock flags; scalar = S11's scalar NNUE recipe (0 packed float
  ops in `forge::nnue::`). Nets: lock AL1 s198 (`src/nnue_weights.inc`, a7ebcf3a…) and e48f006
  (`resid_h256_e48_f006_b06_ep48.inc`, 0fdf9bdb…; tree copy with only that file swapped). 4 configs x 3 rounds.

## 2. Acceptance

| # | line | result | evidence (logs/ unless noted) |
|---|---|---|---|
| 1 | own CMake target; engine exe sha unchanged with the patch | PASS | Patch = tools + CMake only. Box recipe on the S37 tree vs lock exe 5d4df7f1: `cmp -l` 6 bytes (PE timestamp 137-139, PE checksum 217-219), FMA 0 (`build_engine_s37.log`, `cmp_engine_vs_lock.log`). CI release: Linux forge sha256 6635d4d1… = the lock's Linux build |
| 2 | 10k fixed FENs from bench + WAC | PASS | 10,000 positions from 8 bench FENs + 300 WAC; deterministic (identical dump in 12 runs) |
| 3 | refresh, incremental update, output layer, whole evaluate(); median + p90 ns/call | PASS | table below (`cost_table_runs4.txt`, `runs4/cost_table.json`, 12 run JSONs in `runs4/`) |
| 4 | eval checksum == engine's own eval on the same FENs | PASS | `s37_cost_table.py`: sums and per-position FNV-1a of net and total equal the lock archive's `nnue_check.cpp` (built per net from the same sources, lock recipe) — lock net 116176 / HCE -65898 / total 50278, e48f006 117080 / -65898 / 51182; one checksum set per net across 3 rounds x avx2/scalar. Every run also checks: replica == `nnue::evaluate` (0 mismatches), incremental accumulator == refreshed accumulator bitwise and same eval (0 of 346,182), `Worker::static_evaluate` == clamp(evaluate_uncached + net) for 10,000 parents and 346,182 children (0) |
| 5 | lock net and e48f006, scalar vs AVX2 | PASS | 4 configs below |
| 6 | Std pass | PASS | PC CTest 14/15, only `forge_tests` (4 known lines), known-failure check PASS, `forge_nnue_microbench_check` passes (`ctest_cmake.log`); CI section 4 |
| 7 | planted bug | PASS | m1 engine quiet update `(src - removed) + added` -> `(src + removed) + added`: FAIL, 63,703 accumulator / 63,524 eval / 63,524 whole-update mismatches; m2 replica scale 400 -> 401: FAIL, 398 replica mismatches (`mutants.txt`) |
| 8 | box timings labelled / CPU time with repeats | PASS | PC (Zen 5) only, labelled advisory; CPU time per region, 15 passes x 3 rounds |

### Cost table (CPU ns per call: median over 3 rounds of each run's 15-pass median; per-call median/p90 from the rdtsc passes, ~10 ns resolution)

| stage | calls/pass | lock AVX2 | lock scalar | e48f006 AVX2 | e48f006 scalar | lock AVX2 per-call med/p90 | lock scalar per-call med/p90 |
|---|---|---|---|---|---|---|---|
| refresh (both perspectives) | 10,000 | 658.4 | 4304.6 | 663.9 | 4297.1 | 640/830 | 4310/5700 |
| dirty_pieces | 346,182 | 7.9 | 8.3 | 7.8 | 8.3 | <10/10 | <10/10 |
| update quiet (sub + add) | 310,219 | 48.5 | 253.1 | 49.7 | 251.0 | 40/60 | 240/260 |
| update capture (2 sub + add) | 35,664 | 99.6 | 373.5 | 99.9 | 371.3 | 60/80 | 320/340 |
| update castle (generic, 4 changes) | 299 | 290.6 | 1041.2 | 304.4 | 1065.2 | 130/150 | 800/860 |
| output layer (fused SCReLU + affine) | 40,000 | 43.4 | 268.9 | 43.2 | 270.0 | 50/60 | 270/300 |
| activation (replica) | 40,000 | 37.0 | 238.5 | 37.6 | 238.0 | 30/40 | 230/250 |
| affine (replica) | 40,000 | 24.4 | 128.2 | 24.7 | 128.5 | 30/40 | 130/150 |
| whole eval, refresh path | 10,000 | 1143.8 | 5062.4 | 1137.1 | 5076.0 | 1140/1390 | 5110/6510 |
| whole eval, lazy-update path (search case) | 346,182 | 403.1 | 864.9 | 399.7 | 878.4 | 380/570 | 840/1050 |
| whole eval, valid accumulator | 10,000 | 274.9 | 537.4 | 273.8 | 540.9 | 270/330 | 520/620 |
| HCE evaluate_uncached | 10,000 | 396.1 | 435.6 | 395.2 | 440.2 | 390/480 | 430/540 |

Ranges over the 3 rounds are in `cost_table_runs4.txt` (most stages within ±2%).

## 3. Findings
- **Search-case static eval ≈ 403 ns (AVX2):** HCE ≈ 232 ns (57%, with pawn cache and runtime PSQT), NNUE update +
  output ≈ 97 ns (24%: move-weighted update 54 + output 43), rest ≈ 74 ns (18%: runtime-PSQT update, lazy-update walk,
  calls). The HCE is the largest single cost of the residual evaluation.
- A full refresh costs 13.6 quiet updates; the generic (castling) path is ~3x a quiet update at the per-call median
  (130 vs 40-50 ns) and ~6x in the mean (cold weight columns), but only 0.09% of moves.
- **Net-independent:** e48f006 vs lock within ±2.5% on every stage with >= 10k calls (dense float code, no sparsity).
- **Scalar vs AVX2:** NNUE stages 3.6-6.5x slower (refresh 6.5x, quiet update 5.2x, output 6.2x); whole static eval
  2.0-2.2x (update/valid paths), 4.4x (refresh path). HCE — identical code in both binaries — differs by 10%: treat
  cross-binary differences under ~10% as noise on this PC.
- The two-loop replica costs 61 ns vs 43 ns fused (AVX2): fusion saves the 2 KB buffer round trip; ~60% activation,
  ~40% affine. Incremental and refreshed accumulators are bitwise identical (int16/4096 float sums are exact).
- **Method notes:** per-call resolution is one TSC step (~10 ns on Zen 5, 100 MHz reference), so per-call figures
  under ~50 ns are coarse; region CPU time is the primary number. Pitfall found: `<x86intrin.h>`'s target pragmas
  re-define `__AVX2__`/`__SSE__` after `-U__AVX2__ -U__SSE__`, so a TU that includes it gets the AVX2 branch in a
  "scalar" build (fixed by capturing the macros before any include; the engine's nnue.cpp is unaffected — 0 packed
  ops). Superseded development runs: `logs/history.txt`.

## 4. CI
opus-ci 40513394598 on 20f55fab: release (job 122220743427), asan (122220744106), tsan (122220743772): all success.
Release: Linux forge sha256 6635d4d1… (= lock build), FMA 0, uci_check --full ALL OK. CTest 14/15 in all three modes,
only forge_tests (4 known lines), known-failure check PASS; forge_nnue_microbench_check passes (release 0.16 s, ASan
2.69 s, TSan 14.56 s); no ASan/UBSan report; TSan 0 reports (`logs/ci_40513394598_summary.log`).

## 5. Left / UNVERIFIED
- Quiet-machine / Linux-box timings: not run (CI runs the checks only); all timings are a loaded PC's (advisory).
- The SSE (x86-64 baseline) output path is not timed (AVX2 and scalar only).
- The activation/affine split is a bit-exact replica, not the engine's fused loop.
- The engine binary has no eval command: "engine's own eval" = forge::nnue + Worker::static_evaluate in-process and the
  archive harness nnue_check.cpp (as used by S21/S31). The MSVC build of the tool is untested (rdtsc path is GCC/Clang).
