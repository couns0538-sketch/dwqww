PROPOSAL N3: Add an NNUE v3 `int32` output-sum overflow fix and load-time check to P4 and P8 before any net wider than 1024 (or any raise of `MaxHidden`) is trained or loaded.

KIND: source fact

EVIDENCE:
1. `source/include/forge/nnue_v3.hpp:65,71` sets `MaxHidden = 1024`, `QA = 255`, `MaxW2 = 127`. Round 67's net already hits `max|w2| = 127` (`Forge65_build/build_clang.log:26`).
2. Exact worst-case derivation for `output_sum_avx2` (`source/src/nnue_v3.cpp:124-151`):
   - Each loop step processes 16 `int16` lanes (`h += 16`) via `_mm256_madd_epi16(_mm256_mullo_epi16(a, wa), a)`, producing 8 `int32` lanes where each lane adds 2 terms of `a^2 * w2`.
   - Max magnitude per `madd` `int32` lane: `2 * 255^2 * 127 = 16,516,350`.
   - Over `hidden / 16` iterations, each lane of `sum0` and `sum1` can reach `(hidden / 16) * 16,516,350`.
   - `hsum_epi32_pair_avx2` (`source/src/nnue_v3.cpp:125`) adds `sum0 + sum1` in `int32` BEFORE widening to `int64`: `const __m256i total32 = _mm256_add_epi32(sum0, sum1);`.
   - At `hidden = 1024`: `2 * (1024 / 16) * 16,516,350 = 128 * 16,516,350 = 2,114,092,800`, against `INT32_MAX = 2,147,483,647` — only **1.55% headroom** (`33,390,847`).
   - At `hidden = 1056` (one 32-unit step above 1024) or `1536` / `2048`: `2 * (1056 / 16) * 16,516,350 = 2,180,158,200 > INT32_MAX` — silent signed 32-bit wraparound in AVX2.
3. In `output_sum_avx512` (`nnue_v3.cpp:155-198`) and `apply_pair_and_sum_avx512` (`nnue_v3.cpp:477,510`), each ZMM lane sums `hidden / 32` steps per perspective and `hsum_epi32_pair_avx512` (`nnue_v3.cpp:156`) adds them in `int32`, giving 2x the AVX2 width (`hidden = 2048` has 1.55% headroom, `hidden = 2112` overflows).
4. `load_from_bytes` (`source/src/nnue_v3.cpp:678-681`) checks `max_w2 <= 127` and `max_b1 + 32 * max_w1 <= 32767`, but has NO check on worst-case `int32` output-lane sum if `MaxHidden` is raised, and AVX2 vs AVX-512 would silently diverge if an overflow occurs on AVX2 only.
5. Minimal fix: widen `sum0` and `sum1` to `int64` *before* adding them in `hsum_epi32_pair_avx2` (`125`) and `hsum_epi32_pair_avx512` (`156`) — ~2 extra instructions outside the inner loop, doubling AVX2 safe width to `hidden = 2048` and AVX-512 safe width to `hidden = 4096` — and add a `load_from_bytes` bound check tying `hidden` and `max_w2` to the lane limit.

COST: ~15 minutes engineering, ~1 CPU minute for a synthetic unit test, 0 GPU hours. Nothing waits on it while `hidden <= 1024`.

HOW IT IS JUDGED:
1. Build a synthetic adversarial `.fnn3` test (in a unit test, not production weights) with `hidden = 1024` and `1536` (once `MaxHidden` is raised), all `w1`/`b1` driving `a = 255` and all `w2 = +127`: before the fix, AVX2 wraps negative at `hidden = 1536` and disagrees with `Kernel::Scalar`; after the fix, `Kernel::Scalar`, `Kernel::Avx2`, and `Kernel::Avx512` return the exact same `int64` sum and evaluation.
2. Verify `bench 11` / `bench 13` on `loop/forge65_r0067.fnn3` remain `226187 / 616966` with zero measurable nps regression (2-build check).

WHAT WOULD CHANGE MY MIND:
- If P4 commits to never exceeding `hidden = 1024` (still safe by 1.55% at `MaxW2 = 127` on AVX2), this drops from a P4 blocker to a P8 hygiene guard; however, because P4 says "Which shape (width, king buckets, output buckets) is open" (`PLAN.md:208-209`) and `hsum` widening is ~4 lines outside the inner loop, fixing it preemptively eliminates a silent AVX2-only wraparound trap.
