# status — UBSan sweep (swarm/ubsan)

**Complete.** Branch pushed, PR open. Full report in `FINDINGS.md`.

## Build, verbatim

- repo `couns0538-sketch/dwqww`, engine `forge-combo29/`, audit base **`6b98f2170a3210e71beed04bbd2553972c253ed7`**
- compiler `/usr/bin/g++` **13.3.0 (Ubuntu 13.3.0-6ubuntu2~24.04.1)**
  `LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13` (`/usr/bin/c++` is clang 18 with a broken header path)
- cmake 3.28.3, `-DCMAKE_BUILD_TYPE=Release -DFORGE_MARCH=x86-64-v4`
- **sanitizer flags, exact:**
  `-fsanitize=undefined,address -fno-sanitize-recover=all -fno-omit-frame-pointer -g`
- **resolved `CXX_FLAGS`:**
  `-fsanitize=undefined,address -fno-sanitize-recover=all -fno-omit-frame-pointer -g -O3 -DNDEBUG -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4`
- **resolved `CXX_DEFINES`:**
  `-DFORGE_EXPOSE_TUNABLES=1 -DFORGE_NNUE_HIDDEN=256 -DFORGE_NNUE_WEIGHTS="<src>/nnue_weights.inc" -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_TT_NOTLS=1 -DNDEBUG`
- **runtime:**
  `UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=0:report_error_type=1`
  `ASAN_OPTIONS=detect_leaks=1:abort_on_error=1:detect_stack_use_after_return=1`
  (`halt_on_error=0` as requested; `-fno-sanitize-recover=all` still turns every finding into an
  abort, so nothing is printed-and-continued. The two settings are consistent: UBSan prints the
  report, then the abort from the build flag ends the process.)
- **binary sha256**
  - UBSan+ASan sweep build `3104e9a5616ee6d4670b8aa97586be7d185b3a4d97cde8e155c0ca298c2cbcaa`
  - baseline, no sanitizer `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`
  - UBSan+ASan with float checks named `b6514b9f4a968b3b75ebb99c8810a043443683aa6e44e45ba720cb82c7070427`

## Numbers

| | |
|---|---|
| probes | **2,408** across 12 phases, ~20 min wall (1,204.7 s) |
| UBSan reports | **0** |
| ASan reports | **0** |
| leak reports at exit | **0** |
| crashed processes / restarts | 0 / 0 |
| `__ubsan_` symbols | **15** (sanitizer build) vs **0** (baseline) |
| planted UB classes caught | **12 of 12**, control clean |
| pins on the sanitizer build | 312,866 / 862,329 / 3,024,920 / 4,865,609 — **all four match** |
| widened float arm | 643 probes, **0** reports, non-vacuity audit passes |

## What was verified, in one line each

- sanitizer is linked and fires: 12 plants, one per check class, each caught by the same harness
- the workload reached the code: per-phase non-vacuity audit passes (`scripts/audit_vacuity.py`),
  720/720 depth-12 searches with nodes > 0, 11/11 live stress positions, 11 book moves, 240/240 eval lines
- exit-time reports are readable: drained to EOF every phase, proven with an exit-only plant
- two flag-set facts recorded as findings: `-fsanitize=integer` does not exist in GCC 13 (§3), and
  the default `undefined` group omits `float-cast-overflow` / `float-divide-by-zero` (§2)

## Not covered — do not read the clean run as covering these

unsigned/implicit integer conversion, float NaN/Inf, strict aliasing, data races (this is not TSan;
`Threads` was 1 throughout), the NNUE v3 path (`FORGE_NNUE_V3=0` here, compiled out), the Windows
build. Full list and reasoning in `FINDINGS.md` §6.

## Withdrawals

- **3 of my 12 first-run plants did not fire and were my errors, not sanitizer gaps.** A fixed-
  underlying-type enum is not UB; a compile-time-provable misalignment and a constant pointer
  overflow were optimized away before any check was emitted. Diagnosed and re-planted; all 12 now
  fire. Details in `FINDINGS.md` §1.
- **My first complete run's `0` was untrustworthy** — a partial-line token match dropped the
  terminating line from the evidence. Found by the non-vacuity audit failing on a zero. Fixed,
  re-ran the whole sweep. Details in `FINDINGS.md` §7.
- **4 of 11 stress positions were checkmates**, giving 0-node searches that looked like coverage.
  Rebuilt live-only; searches with nodes went 7/11 → 11/11.
