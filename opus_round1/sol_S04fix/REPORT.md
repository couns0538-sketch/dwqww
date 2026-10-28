# S04fix — cold-start probe as a ctest target, cold-test TIMEOUTs, ON build with MinGW — DONE

Branch `opus-sol-S04fix` = AL1 lock tree `d4f4312` + CI baseline `0d99f02` (cherry-picked as `2c003e97`)
+ `84408bcd` (Sol's S04 v2 patch, code parts verbatim) + `54d0fa78` (fix-ups S04-1/S04-2 + Linux CI for the ON
build) + `12c98d8e` (evidence) + the REPORT commit. `FORGE_ATTACKS_INIT_ONCE` stays default OFF; the OFF build is the lock.
Machine exclusive: no (gates, NNUE training and self-play kept running; PC load 72-90% during the PC steps; all
PC work at Idle priority, builds JOBS=1). Work and results by a sub-agent; this report text is its hand-back.

## Acceptance

| Item | Command | Result | Evidence |
|---|---|---|---|
| S04-1 probe = ctest target (PC, MinGW) | `ctest -L cold-init -V` in the ON CMake build | `forge_sol_S04_cold_probe` Passed: 1000/1000 fresh processes, 8 cold first-Board threads each, 41.2 s; cold test Passed | `logs/ctest_on_cold_mingw.log` |
| S04-1 probe = ctest target (Linux TSan) | CI `ci_s04fix.sh` release / asan / tsan, full ctest | probe Passed in all 3 jobs (1000 TSan processes: 267 s / 490 s / 499 s); TSan cold test Passed (0.35-0.68 s) | `logs/ci_40505295463/*/ctest_*_on.log` |
| S04-2 TIMEOUT on the TSan test | `ctest --show-only=json-v1 -L cold-init` | cold test TIMEOUT 120 s, probe TIMEOUT 3120 s (3 s x runs + 120), RUN_SERIAL; they override CI's `--timeout 600` | `logs/ci_40505295463/*/cold_tests_*_on.log`, `logs/ctest_on_cold_mingw.log` |
| S04-2 build ON with MinGW (CMake) | `JOBS=1 cmake_build.sh ... -DFORGE_ATTACKS_INIT_ONCE=ON` | build OK (g++ 15.2 ucrt64, posix threads); 6 warnings = the known -Wconversion lines in search.cpp that every AL1 build shows, 0 in S04 code | `logs/cmake_on_ninja_build.log`, `logs/toolchain.log` |
| S04-2 ON full ctest (MinGW) | `ctest --output-on-failure --timeout 900` + `check_known_failures.py` | 15/16, only forge_tests with exactly the 4 known lines: KNOWN-FAILURE CHECK PASS | `logs/ctest_on_full_mingw.log`, `logs/known_on_full_mingw.log` |
| ON identity (box recipe) | `build_pc.sh ... -DFORGE_ATTACKS_INIT_ONCE=1`; `uci_check.py --full` | bench 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690: ALL OK; FMA 0 | `logs/build_pc_off_on.log`, `logs/uci_check_off_on.log` |
| OFF = lock | `build_pc.sh` (OFF); `cmp -l` vs `forge_h256_s198.exe`; `uci_check.py --full` | 5 differing bytes, all PE timestamp/checksum (137-139, 217-218); ALL OK; FMA 0. Linux CI: OFF binary and disassembly IDENTICAL to lock 294dbed | `logs/off_vs_lock_cmp.log`, `logs/ci_40505295463/release/identity_default_vs_lock.log` |
| ON identity (Linux) | CI release `uci_check.py --full` on the ON build | ALL OK, FMA 0 | `logs/ci_40505295463/release/identity_on.log` |
| Planted bug (PC) | cold test built with the option OFF (original init bool), probe driver | 50/50 fresh processes crash; probe: `COLD_PROBE_FAIL run 1/1000: exit=Access violation` | `logs/mutant_off_probe_RED.log` |
| Planted bug (Linux TSan) | CI tsan RED control | 3/3 runs exit 66: TSan data race on `KnightTable` (bitboard.cpp:130) and the init bool (:123) | `logs/ci_40505295463/tsan/red_off_race.log` |
| CI | `gh run list --branch opus-sol-S04fix` | opus-ci 40505295150 (OFF: release, asan, tsan) success; opus-sol-s04fix-ci 40505295463 (ON: release, asan, tsan) success | `logs/ci_40505295150/`, `logs/ci_40505295463/` |

## What changed (vs Sol's v2)
- `tests/forge_sol_S04_cold_probe.cmake` (new): CMake-script port of Sol's `forge_sol_S04_cold_runs_20261025.py`
  (fresh process per run, stop at the first nonzero exit / unexpected stdout / any stderr, print that run's streams,
  keep a caller's `TSAN_OPTIONS`, else `halt_on_error=1:exitcode=66`). No Python needed.
- `CMakeLists.txt`: the ON block registers the cold test for every toolchain (TSan variant on Linux GNU/Clang = Sol's
  target; uninstrumented `forge_sol_S04_cold_test_native` elsewhere, e.g. MinGW), `TIMEOUT 120`, and
  `forge_sol_S04_cold_probe` (`FORGE_S04_COLD_PROBE_RUNS`, default 1000; TIMEOUT 3 s/run + 120 s). OFF: nothing new.
- `.github/workflows/opus-sol-s04fix-ci.yml` + `ci_s04fix.sh`; full diff vs AL1 in `forge_sol_S04_v3.patch`.

## Findings
- The OFF code's cold-init race crashes natively on the PC toolchain (50/50 processes), not only under TSan. The UCI
  engine builds its first Board on the main thread, so normal startup does not hit it (Sol's observation).
- The TSan probe costs 0.27-0.50 s per process on the GitHub runner (Sol measured 1.34 s); 3120 s TIMEOUT leaves >= 6x
  headroom. Without its own TIMEOUT the probe would be close to CI's 600 s in the asan/tsan jobs (490-499 s).
- MinGW-w64 GCC has no TSan runtime: on the PC the cold test is a functional check only; race detection is Linux CI.

## Process note (main session, from the sub-agent's hand-back)
A CI test binary was moved (not deleted) out of the job folder to `F:\opus_scratch\sol_S04fix\ci\moved_from_jobdir`.

## Left / UNVERIFIED
- No speed or Elo claim; NPS effect of ON not measured (one call_once per Board construction, outside search).
- Race freedom shown by TSan on Linux only.
