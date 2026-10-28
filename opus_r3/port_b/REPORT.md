# port_b (R3-1): S32 datagen, S37 NNUE microbench, S04fix cold-init probe merged into the R3 stack — DONE

(Text of the sub-agent's report, saved by the main session; the agent could not write REPORT.md.)

Branch `opus-r3-port-b` = `2432670b` (opus-r3-cifix) + `f48e08bd` (merge opus-sol-S32) + `49fae95a` (merge opus-sol-S37) + `a06b00d0` (merge opus-sol-S04fix) + `2e4d1800` (evidence, `[skip ci]`).
- Every feature keeps its own switch, default OFF. The default engine is byte-identical to the 2432670b build.
- Machine exclusive: no. Gates, NNUE training, self-play and other agents were running; everything here ran at nice 19, with one g++ process or CMake JOBS=1.
- No Elo or speed claim.

## 1. Merges

| branch (head) | conflicts | resolution |
|---|---|---|
| opus-sol-S32 (2974675f) | src/uci.cpp (include list), CMakeLists.txt (2 hunks) | Union. The stack's includes stay and `forge/datagen.hpp` follows under `FORGE_DATAGEN`. The switched `main(argc, argv)` that dispatches to `forge::datagen::run` merged cleanly in front of the stack's UCI loop. `src/datagen.cpp` joins forge_core (a static library, so it is not linked into the default forge). The option and the `forge_datagen` / `forge_datagen_tests` targets come after `forge_debughooks`. `add_test forge_datagen_tests` comes after `forge_net_scale_tests`; `datagen_cli_tests` goes at the end of the Python block. |
| opus-sol-S37 (4822281e) | CMakeLists.txt (add_test list) | Union. `forge_nnue_microbench_check` is appended after `forge_datagen_tests`; the target merged cleanly after `forge_bench`. The tool reaches `Worker::static_evaluate` and `stack_` through the SearcherTestProbe friendship. After the O3 split `stack_` lives in ThreadData (Worker's private base), which the friend still reaches, so no source change was needed. |
| opus-sol-S04fix (ea541f2c) | none | Auto-merge (the stack never touched src/bitboard.cpp). The option sits after FORGE_NOZERO_MOVE_BUFFERS and the ON block after the FORGE_SPEEDSTACK block. I reworded the local merge message to describe this. `opus-sol-s04fix-ci.yml` triggers only on opus-sol-S04fix, so it is inactive here. |

- Each branch carries its own copy of the CI baseline (0d99f02), which matches the stack's, so run_ci.sh and opus-ci.yml are unchanged.
- No new tsan_extra.sh hook was added.
- Outside opus_round1/opus_r3, the merges change 12 files (+2533 lines, nothing removed).

## 2. Acceptance (evidence is under `opus_r3/port_b/logs/`)

| # | line | result | evidence |
|---|---|---|---|
| 1 | Default PC build equals the PC build of 2432670b | **PASS.** Same size (4,544,650 bytes); `cmp -l` shows 2 bytes (137 PE timestamp, 217 PE checksum). FMA 0, 0 warnings. | cmp_head_default_vs_base.log, build_head_default.log, build_base_2432670b.log, pc_builds.sha256 |
| 2 | Default build hits the lock pins | `uci_check --full` ALL OK: bench d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690 | uci_check_full_head_default.log |
| 3 | FORGE_DATAGEN PC build (`FORGE_EXTRA_SRCS=src/datagen.cpp`, `-DFORGE_DATAGEN=1`) | **PASS:** 0 warnings, FMA 0, ALL OK | build_head_datagen.log, uci_check_full_head_datagen.log |
| 4 | S32: same seed gives the same bytes, equal to S32's own output | **PASS.** S32's determinism run (25 games, 5000 nodes, seed 20261027, `--text`) done 3 times. All 5 files (.games, .pos, .hce, .info, .txt) are byte-identical across runs and equal S32's recorded sha256 (pos 6ff0de3d, hce 7763c7da). The summary (25 games, 2500 positions, 3365 plies, 9-8-8) is identical. Tiny output files are in F:\opus_scratch\r3\port_b\datagen_smoke\. | step2b_datagen_determinism.log, datagen_smoke.sha256 |
| 5 | S32: a reused output prefix is refused | **PASS:** exit 1, existing files unchanged | datagen_reuse_refused.log |
| 6 | FORGE_ATTACKS_INIT_ONCE PC build | **PASS:** 0 warnings, FMA 0, ALL OK | build_head_initonce.log, uci_check_full_head_initonce.log |
| 7 | S37 microbench builds and runs (S37's own `build_microbench_pc.sh avx2`) | **PASS.** 0 warnings, FMA 0. `--check-only` on 2000 positions matches S37's check_quick checksums (25647 / -14991 / 10656 / 322547, fnv dde345d4). On 10000 positions it matches S37's lock checksums (116176 / -65898 / 50278 / 1943594, fnv b3886383) with 0 of 346,182 mismatches. The corpus dump sha256 d238dc06 equals S37's. The timed run completes. | build_microbench_avx2.log, microbench_check2000.log, microbench_check10000.log, microbench_timed.* |
| 8 | Full CMake build, all targets (JOBS=1), plus full ctest, default config | **PASS.** 38 executables. 31 compiler warnings, all already in the stack's search modules (alphabeta.inc 24, qsearch.inc 6, tt_lockless.inc 1); the merges do not touch those files. ctest 39/40, only forge_tests with the 4 known lines: KNOWN-FAILURE CHECK PASS. | cmake.build.log, ctest_cmake.log, known_cmake.log |
| 9 | CMake `-DFORGE_DATAGEN=ON` plus full ctest | **PASS:** 39/40, known lines only | cmake_datagen.build.log, ctest_cmake_datagen.log, known_cmake_datagen.log |
| 10 | CMake `-DFORGE_ATTACKS_INIT_ONCE=ON` plus full ctest plus `ctest -L cold-init -V` | **PASS on re-run:** 41/42, known lines only. The first run also failed forge_smp_tests (overshoot 26333 and 27724 against a bound of 26300); see Findings. The native cold test passes. The probe gives COLD_PROBE_PASS for 1000 of 1000 fresh processes with 8 workers each (165 s, 133 s and 127 s on the three runs). TIMEOUT 120 and RUN_SERIAL are set as designed. | ctest_cmake_initonce.log, ctest_cmake_initonce_rerun.log, known_cmake_initonce_rerun.log, ctest_initonce_cold_V.log, cold_tests_show_only.json |
| 11 | GitHub CI opus-ci | **Run 40568260400 on a06b00d0: success.** Jobs: release 122415236349, asan 122415235698, tsan 122415236246. Linux forge sha256 3a9e13bf equals base run 40565363595's. ALL OK, FMA 0. Known-failure check passes in all 3 jobs. TSan reported 0 issues and all 8 tsan_extra hooks ran. New tests under TSan took 17.6 s (datagen), 14.9 s (microbench check) and 38.0 s (datagen CLI). | ci_40568260400_summary.log, ci_40568260400/ |

## 3. Findings
- **No search changes.** None of the three branches touches the search. With all options off the stack searches exactly like the lock, so datagen reproduces S32's files byte for byte and the microbench reproduces S37's checksums exactly.
- **forge_smp_tests is load-sensitive on this PC.** Its overshoot bound assumes threads see the stop flag promptly, which fails on a busy machine at Idle priority. Over 20 alternating runs (step3b) it failed 7 times with the default build and 10 times with the ON build. The default build's smp test binary is functionally the 2432670b one. The CI runners pass it. I did not change it.
- **CI TSan took longer than the base run** (22 min vs 11 min) because the runner was about twice as slow: unchanged tests doubled too (forge_smp_tests 134 s to 217 s, forge_pure_nnue_tests 96 s to 194 s). The three new tests add about 70 s. This is well inside the 60-minute cap.
- **Microbench timings (advisory only, machine not exclusive, 5 passes):** search-case whole eval 369.5 ns (S37 measured 403.1), refresh 571.2 ns (S37: 658.4), HCE 401.7 ns (S37: 396.1).
- **The stack's new board.cpp code adds no startup-time statics.** Its threefold claim and C6 cuckoo table use a constexpr table, so the cold first-Board test exercises the same init path as at S04fix's base.
- **Merge into 2047348a:** one CMake conflict (the shared `endif()` trap); the main session resolved it the same way in `e523aae9`. Evidence: `logs/premerge_2047348a_syntax.log`, `logs/premerge_stack2047348a_CMakeLists.txt`.
- **Process slips.**
  - In step2, the RAM-guard function overwrote the datagen loop variable, so its first run wrote to `datagen_smoke/9/` and its second was refused (S32's prefix protection working).
  - Step2's line-by-line diff also printed a false "MISMATCH": sha256sum's `*` marker differed while the hashes were equal.
  - step2b redid the runs into det_a/det_b, compares by hash only, and checks all 3 runs.
  - The first merge message file sits at F:\opus_scratch\r3\port_b_msg_s32.txt, left in place.
  - A mislabelled preview log (F:\opus_scratch\r3\port_b\premerge_7b431d48_syntax.log) was not committed; logs/premerge_2047348a_syntax.log replaces it.

## 4. Left / UNVERIFIED
- **Switch-on configurations were checked on the PC only** (MinGW, native cold test, no TSan runtime). opus-ci builds only the default configuration.
- **No Linux sanitizer run of FORGE_ATTACKS_INIT_ONCE=ON on the stack.** The existing Linux ASan/TSan evidence is S04fix's own run 40505295463, at the lock base. Its workflow cannot be manually triggered on the stack: the release job requires the OFF build's disassembly to match lock 294dbed, so it would fail. A stack-adapted job running only the asan and tsan modes of ci_s04fix.sh is a possible follow-up.
- **Not re-run on the stack:** the S37 scalar build and the e48f006 net (the tool is unchanged and its checksums match).
- **No datagen throughput or NPS measured on the stack.**

port_b (R3-1) | opus-r3-port-b | DONE (2e4d1800) | S32 datagen + S37 microbench + S04fix cold-init merged onto 2432670b, all default OFF; default exe = 2432670b build; switch-ON builds ALL OK; CMake/ctest clean except the 4 known forge_tests lines; opus-ci 40568260400 green
