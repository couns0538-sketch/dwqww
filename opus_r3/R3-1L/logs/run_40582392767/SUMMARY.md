# R3-1L Linux self-play double-check

release: 36 configs, 18000 games, 0 errors, 0 failing rows; sanitizer (ASan+UBSan / TSan): 8 rows, 1100 games, 0 errors, 0 failing rows; jobs without artifact: none.

Pass rule: all requested games (500 per release config) with 0 errors and a clean preflight, identity ALL OK (and FMA 0) for every build, 0 sanitizer reports.

| job | mode | config | exe (sha256) | identity | games | plies | errors | errors by kind | crashes | illegal moves | double bestmoves | timeouts | malformed | watchdog answers | HardDeadline fired | late after watchdog | sanitizer reports | wall s | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| asan-all_on-s1 | asan | all_on | allsw `fef5e70d73b9` | ALL OK | 250/250 | 28677 | 0 | - | 0 | 0 | 0 | 0 | 0 | 778 | 778 | 0 | 0 | 490.2 | **PASS** |
| asan-all_on-s2 | asan | all_on | allsw `fef5e70d73b9` | ALL OK | 250/250 | 29111 | 0 | - | 0 | 0 | 0 | 0 | 0 | 654 | 654 | 0 | 0 | 452.2 | **PASS** |
| tsan-all_on | tsan | all_on | allsw `51e46d533c37` | ALL OK | 100/100 | 11227 | 0 | - | 0 | 0 | 0 | 0 | 0 | 559 | 559 | 0 | 0 | 302.1 | **PASS** |
| tsan-all_on_pure | tsan | all_on_pure | allsw `51e46d533c37` | ALL OK | 100/100 | 12860 | 0 | - | 0 | 0 | 0 | 0 | 0 | 644 | 644 | 0 | 0 | 345.1 | **PASS** |
| tsan-all_on_v1net | tsan | all_on_v1net | allsw `51e46d533c37` | ALL OK | 100/100 | 11049 | 0 | - | 0 | 0 | 0 | 0 | 0 | 518 | 518 | 0 | 0 | 247.1 | **PASS** |
| tsan-smp_best_thread | tsan | smp_best_thread | base `0ce5df3ee49c` | ALL OK | 100/100 | 11344 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 363.1 | **PASS** |
| tsan-smp_exact_nodes | tsan | smp_exact_nodes | base `0ce5df3ee49c` | ALL OK | 100/100 | 10868 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 297.1 | **PASS** |
| tsan-lockless_tt | tsan | lockless_tt | base `0ce5df3ee49c` | ALL OK | 100/100 | 10785 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 277.1 | **PASS** |
| rel-all_on | release | all_on | allsw `baa4d9a65513` | ALL OK, FMA 0 | 500/500 | 55287 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 564.3 | **PASS** |
| rel-all_on_pure | release | all_on_pure | allsw `baa4d9a65513` | ALL OK, FMA 0 | 500/500 | 57981 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 598.4 | **PASS** |
| rel-all_on_v1net | release | all_on_v1net | allsw `baa4d9a65513` | ALL OK, FMA 0 | 500/500 | 56027 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 579.4 | **PASS** |
| rel-smp_best_thread | release | smp_best_thread | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 43228 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 418.3 | **PASS** |
| rel-smp_exact_nodes | release | smp_exact_nodes | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 53939 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 514.3 | **PASS** |
| rel-lockless_tt | release | lockless_tt | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 44565 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 436.3 | **PASS** |
| rel-sw1 | release | sw_nnue_lazy_acc | lazyacc `7657f7003d52` | ALL OK, FMA 0 | 500/500 | 57208 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 368.2 | **PASS** |
| rel-sw1 | release | sw_prof | prof `cba7e7e67d9b` | ALL OK, FMA 0 | 500/500 | 56857 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 386.2 | **PASS** |
| rel-sw2 | release | sw_nnue_int16 | int16 `4293370ba85c` | ALL OK, FMA 0 | 500/500 | 57466 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 338.1 | **PASS** |
| rel-sw2 | release | sw_attacks_init_once | initonce `f42b44756b0a` | ALL OK, FMA 0 | 500/500 | 56467 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 326.1 | **PASS** |
| rel-sw3 | release | sw_nnue_o2 | o2 `6cde63b71c25` | ALL OK, FMA 0 | 500/500 | 57118 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 364.2 | **PASS** |
| rel-sw3 | release | sw_nozero_move_buffers | nozero `26f0fd821207` | ALL OK, FMA 0 | 500/500 | 56021 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 358.2 | **PASS** |
| rel-sw4 | release | sw_s13_tt_child_prefetch | s13 `045b297298cd` | ALL OK, FMA 0 | 500/500 | 56220 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 361.2 | **PASS** |
| rel-sw4 | release | sw_speedstack | speedstack `476a82c4477a` | ALL OK, FMA 0 | 500/500 | 56303 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 364.2 | **PASS** |
| rel-base01 | release | off | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 56212 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 358.2 | **PASS** |
| rel-base01 | release | hard_deadline10 | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 54859 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 353.2 | **PASS** |
| rel-base02 | release | syzygy | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 55560 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 337.1 | **PASS** |
| rel-base02 | release | corrhistplus7 | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 56475 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 345.1 | **PASS** |
| rel-base03 | release | nnue_king_buckets_rm8 | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 55885 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 362.2 | **PASS** |
| rel-base03 | release | nnue_output_buckets8 | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 55413 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 359.2 | **PASS** |
| rel-base04 | release | nnue_threats | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 55296 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 360.1 | **PASS** |
| rel-base04 | release | nnue_pawn_pairs | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 55803 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 356.1 | **PASS** |
| rel-base05 | release | pure_nnue | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 60098 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 367.1 | **PASS** |
| rel-base05 | release | corr_margins | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 55656 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 353.2 | **PASS** |
| rel-base06 | release | corr_ext | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 54991 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 323.1 | **PASS** |
| rel-base06 | release | cuckoo_rep | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 55879 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 326.1 | **PASS** |
| rel-base07 | release | material_key_table | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 56044 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 326.1 | **PASS** |
| rel-base07 | release | netscale90 | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 55384 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 325.1 | **PASS** |
| rel-base08 | release | netscale110 | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 56854 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 344.1 | **PASS** |
| rel-base08 | release | hist_rework1 | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 56692 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 347.1 | **PASS** |
| rel-base09 | release | hist_rework2 | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 56602 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 359.2 | **PASS** |
| rel-base09 | release | hist_rework3 | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 57181 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 360.2 | **PASS** |
| rel-base10 | release | intended_threefold | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 56337 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 364.2 | **PASS** |
| rel-base10 | release | corrhistplus1 | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 56056 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 365.2 | **PASS** |
| rel-base11 | release | corrhistplus2 | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 55935 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 360.2 | **PASS** |
| rel-base11 | release | corrhistplus4 | base `644830f9ecba` | ALL OK, FMA 0 | 500/500 | 57072 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 366.2 | **PASS** |
