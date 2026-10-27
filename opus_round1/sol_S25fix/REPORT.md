# S25fix — S25 output-contract checker v2: per-tree pins, PIN_MISMATCH + UCI always, timeout, own temp dir, --allow-expose — DONE

Branch `opus-sol-S25fix` = AL1 base `d4f4312` + CI baseline `0d99f02` (cherry-pick 7578c69b) + aec6c695 (job folder only).
Tests/tooling only: `git diff --stat 294dbed3 -- src include tests tools bench CMakeLists.txt` is empty.
Sol's S25 files (17aa0cae) are unchanged. Machine exclusive: no (Idle priority, single-threaded, JOBS=1, free RAM >= 10 GB).

## Acceptance
| line | result | evidence |
|---|---|---|
| S25-1 pins per tree from --ref (default AL1 312866/862329/3024920/12389307/34048354) | PASS: lock exe 5d4df7f1 passes at d11 and at all 5 depths | logs/real_runs_v2.log R1, R2; logs/real_runs/r2_contract_result.json |
| S25-1 mismatch = bench=PIN_MISMATCH and the UCI check still runs | PASS: `--ref Lprime` -> bench=PIN_MISMATCH, uci=PASS, exit 1 | R3; unit tests test_pin_mismatch_and_uci_still_runs, test_tail_is_fail_not_pin |
| v1 contrast on the same exe | v1: bench FAIL (308972 gate), uci UNVERIFIED -> on AL1 v1 never checked UCI | R4 |
| S25-2 L4 subprocess timeout | PASS: --timeout (default 300 s) per process; only its own child is killed; *_timeout recorded | test_timeout_kills_own_child_and_is_recorded |
| S25-2 L5 mkdtemp outside build tree + cleanup | PASS: NEW mkdtemp under TMP or --work-root, removed after the run (marker + token); --out and --keep kept; foreign dirs refused | R7b, R8 (TMP entries 25/25 before/after); 3 unit tests; CMake ON build tree has no forge_s25_contract_* dir |
| S25-2 L6 expose builds / --allow-expose | PASS: box build with -DFORGE_EXPOSE_TUNABLES=1 (286e87d5, FMA 0) advertises 51 extra spin options -> FAIL without, PASS with --allow-expose (approved 10 still exact; bench = AL1 pins at 5 depths) | R5, R6; README |
| S25-2 L7 Windows runner notes | written (CRLF, forge.exe, X_OK semantics, venv -I -B, TMP, MinGW static ctest, JOBS=1, nice) | README; whole job ran on the PC |
| registration patch v3 (FORGE_OUTPUT_CONTRACT default OFF, no build-tree output path, --allow-expose when FORGE_EXPOSE_TUNABLES) | PASS: git apply --check + GNU -F0 clean on AL1; PC: ON -> 15 tests, ctest forge_sol_S25_output_contract_v2 PASS; OFF -> 14 tests, none from S25 | logs/patch_v3_apply_check.log, logs/cmake_ctest_on.log, logs/cmake_on_off_checks.log |
| tests | 17 OK (incl. Sol's 12 parser cases, ported with explicit pins) | logs/tests_v2.log |
| planted bugs | 6/6 caught | logs/mutants_v2.log |

## Findings
- v1 hard-coded Sol's dev-base d11 (308972) and skipped UCI when that gate failed, so on AL1 it never checked UCI.
- AL1 src/uci.cpp and book.cpp hashes equal Sol's trusted hashes, and the lock exe advertises exactly his 10 options, so the allowlist carries over; pins moved to --ref.
- v1/v2 CMake passed --out-root into the build tree; v3 passes no path (the checker's own temp dir is cleaned).
- The 6 warnings in the CMake build log come from the existing AL1 C++ under CMake's -Wconversion; the patch adds no C++.

## Process note (main session, from the sub-agent's hand-back)
By design (S25-2), the v2 checker removes only its own marker-checked temp dirs, and its timeout kills only its own
child process (the fake engine in the tests). No other process was killed and no existing file on the PC was deleted.

## Left / UNVERIFIED
- The v3 patch is not applied to any accepted tree (it is a deliverable for review).
- Linux run of the v2 checker: UNVERIFIED (the code is portable; tests use a .bat wrapper on Windows and a .sh wrapper elsewhere).
- No Elo or speed claim.
