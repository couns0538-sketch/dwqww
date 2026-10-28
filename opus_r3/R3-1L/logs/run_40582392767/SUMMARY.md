# R3-1L Linux self-play double-check

release: 36 configs, 11000 games, 0 errors, 14 failing rows; sanitizer (ASan+UBSan / TSan): 8 rows, 500 games, 0 errors, 3 failing rows; jobs without artifact: asan-all_on-s1, asan-all_on-s2, tsan-smp_best_thread, rel-all_on_pure, rel-lockless_tt, rel-sw1, rel-sw3, rel-sw4, rel-base05, rel-base08, rel-base11.

Pass rule: all requested games (500 per release config) with 0 errors and a clean preflight, identity ALL OK (and FMA 0) for every build, 0 sanitizer reports.

| job | mode | config | exe (sha256) | identity | games | plies | errors | errors by kind | crashes | illegal moves | double bestmoves | timeouts | malformed | watchdog answers | HardDeadline fired | late after watchdog | sanitizer reports | wall s | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| asan-all_on-s1 | asan | all_on | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | **FAIL (no artifact)** |
| asan-all_on-s2 | asan | all_on | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | **FAIL (no artifact)** |
| tsan-all_on | tsan | all_on | allsw `51e46d533c37` | ALL OK | 100/100 | 11227 | 0 | - | 0 | 0 | 0 | 0 | 0 | 559 | 559 | 0 | 0 | 302.1 | **PASS** |
| tsan-all_on_pure | tsan | all_on_pure | allsw `51e46d533c37` | ALL OK | 100/100 | 12860 | 0 | - | 0 | 0 | 0 | 0 | 0 | 644 | 644 | 0 | 0 | 345.1 | **PASS** |
| tsan-all_on_v1net | tsan | all_on_v1net | allsw `51e46d533c37` | ALL OK | 100/100 | 11049 | 0 | - | 0 | 0 | 0 | 0 | 0 | 518 | 518 | 0 | 0 | 247.1 | **PASS** |
| tsan-smp_best_thread | tsan | smp_best_thread | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | **FAIL (no artifact)** |
| tsan-smp_exact_nodes | tsan | smp_exact_nodes | base `0ce5df3ee49c` | ALL OK | 100/100 | 10868 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 297.1 | **PASS** |
| tsan-lockless_tt | tsan | lockless_tt | base `0ce5df3ee49c` | ALL OK | 100/100 | 10785 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 277.1 | **PASS** |
| rel-all_on | release | all_on | allsw `baa4d9a65513` | ALL OK, FMA 0 | 500/500 | 55287 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 564.3 | **PASS** |
| rel-all_on_pure | release | all_on_pure | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | **FAIL (no artifact)** |
| rel-all_on_v1net | release | all_on_v1net | allsw `baa4d9a65513` | ALL OK, FMA 0 | 500/500 | 56027 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 579.4 | **PASS** |
| rel-smp_best_thread | release | smp_best_thread | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 43228 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 418.3 | **PASS** |
| rel-smp_exact_nodes | release | smp_exact_nodes | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 53939 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 514.3 | **PASS** |
| rel-lockless_tt | release | lockless_tt | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | **FAIL (no artifact)** |
| rel-sw1 | release | sw_nnue_lazy_acc | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | **FAIL (no artifact)** |
| rel-sw1 | release | sw_prof | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | **FAIL (no artifact)** |
| rel-sw2 | release | sw_nnue_int16 | int16 `4293370ba85c` | ALL OK, FMA 0 | 500/500 | 57466 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 338.1 | **PASS** |
| rel-sw2 | release | sw_attacks_init_once | initonce `f42b44756b0a` | ALL OK, FMA 0 | 500/500 | 56467 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 326.1 | **PASS** |
| rel-sw3 | release | sw_nnue_o2 | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | **FAIL (no artifact)** |
| rel-sw3 | release | sw_nozero_move_buffers | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | **FAIL (no artifact)** |
| rel-sw4 | release | sw_s13_tt_child_prefetch | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | **FAIL (no artifact)** |
| rel-sw4 | release | sw_speedstack | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | **FAIL (no artifact)** |
| rel-base01 | release | off | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 56212 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 358.2 | **PASS** |
| rel-base01 | release | hard_deadline10 | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 54859 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 353.2 | **PASS** |
| rel-base02 | release | syzygy | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 55560 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 337.1 | **PASS** |
| rel-base02 | release | corrhistplus7 | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 56475 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 345.1 | **PASS** |
| rel-base03 | release | nnue_king_buckets_rm8 | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 55885 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 362.2 | **PASS** |
| rel-base03 | release | nnue_output_buckets8 | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 55413 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 359.2 | **PASS** |
| rel-base04 | release | nnue_threats | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 55296 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 360.1 | **PASS** |
| rel-base04 | release | nnue_pawn_pairs | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 55803 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 356.1 | **PASS** |
| rel-base05 | release | pure_nnue | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | **FAIL (no artifact)** |
| rel-base05 | release | corr_margins | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | **FAIL (no artifact)** |
| rel-base06 | release | corr_ext | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 54991 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 323.1 | **PASS** |
| rel-base06 | release | cuckoo_rep | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 55879 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 326.1 | **PASS** |
| rel-base07 | release | material_key_table | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 56044 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 326.1 | **PASS** |
| rel-base07 | release | netscale90 | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 55384 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 325.1 | **PASS** |
| rel-base08 | release | netscale110 | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | **FAIL (no artifact)** |
| rel-base08 | release | hist_rework1 | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | **FAIL (no artifact)** |
| rel-base09 | release | hist_rework2 | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 56602 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 359.2 | **PASS** |
| rel-base09 | release | hist_rework3 | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 57181 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 360.2 | **PASS** |
| rel-base10 | release | intended_threefold | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 56337 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 364.2 | **PASS** |
| rel-base10 | release | corrhistplus1 | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 56056 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 365.2 | **PASS** |
| rel-base11 | release | corrhistplus2 | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | **FAIL (no artifact)** |
| rel-base11 | release | corrhistplus4 | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | **FAIL (no artifact)** |
