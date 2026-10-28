# R3-1 self-play matrix, git head 330237f3

Generated 2026-10-28 00:10:42 by run_matrix.py from F:/opus_scratch/r3/selfplay/runs/330237f3; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all_on | opus_r3sp_allsw.exe `52f337c864bd` | 2 | SyzygyPath=D:/grok-pc-data/dwqww/.claude/worktrees/syzygy345, CorrHistPlus=7, CorrMargins=1, CorrExt=1, CuckooRep=true, MaterialKeyTable=true, NetScale=99, HistRework=2, IntendedThreefold=true, HardDeadline=10, LocklessTT=true, SmpExactNodes=true, SmpBestThread=true, TtChildPrefetch=true, NnueLazyAcc=true, Profile=true, NnueInt16=true, NNUEKingBuckets=8, NNUEOutputBuckets=8, NNUEThreats=1, NNUEPawnPairs=1, NNUEFile=F:/opus_scratch/r3/selfplay/nets/replica_rm8_ob8_thr0_pp0.fnn2 | 500/500 | 48826 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 1017 | 362031 | 788.4 |
| all_on_pure | opus_r3sp_allsw.exe `52f337c864bd` | 2 | SyzygyPath=D:/grok-pc-data/dwqww/.claude/worktrees/syzygy345, CorrHistPlus=7, CorrMargins=1, CorrExt=1, CuckooRep=true, MaterialKeyTable=true, NetScale=99, HistRework=2, IntendedThreefold=true, HardDeadline=10, LocklessTT=true, SmpExactNodes=true, SmpBestThread=true, TtChildPrefetch=true, NnueLazyAcc=true, Profile=true, NnueInt16=true, NNUEKingBuckets=8, NNUEOutputBuckets=8, NNUEThreats=1, NNUEPawnPairs=1, PureNnue=1, NNUEFile=F:/opus_scratch/r3/selfplay/nets/pure_material_rm8_ob8_thr0_pp0.fnn2 | 500/500 | 52282 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 1054 | 368464 | 817.3 |
| all_on_v1net | opus_r3sp_allsw.exe `52f337c864bd` | 2 | SyzygyPath=D:/grok-pc-data/dwqww/.claude/worktrees/syzygy345, CorrHistPlus=7, CorrMargins=1, CorrExt=1, CuckooRep=true, MaterialKeyTable=true, NetScale=99, HistRework=2, IntendedThreefold=true, HardDeadline=10, LocklessTT=true, SmpExactNodes=true, SmpBestThread=true, TtChildPrefetch=true, NnueLazyAcc=true, Profile=true, NnueInt16=true | 500/500 | 50985 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 708 | 332408 | 725.0 |
| hard_deadline10 | opus_r3sp_base.exe `07eb6fdeb058` | 1 | HardDeadline=10 | 500/500 | 48948 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 261 | 312866 | 435.9 |
| sw_nnue_lazy_acc | opus_r3sp_lazyacc.exe `9ffef77efe05` | 1 | NnueLazyAcc=true | 500/500 | 51620 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 384.6 |
| sw_prof | opus_r3sp_prof.exe `1286cb9c7236` | 1 | Profile=true | 500/500 | 51527 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 367.4 |
| sw_nnue_int16 | opus_r3sp_int16.exe `f65cb2ce3844` | 1 | NnueInt16=true | 500/500 | 50342 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 330610 | 373.4 |
| sw_attacks_init_once | opus_r3sp_initonce.exe `feb109601b55` | 1 | (none) | 500/500 | 50227 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 363.6 |
| off | opus_r3sp_base.exe `07eb6fdeb058` | 1 | (none) | 500/500 | 50323 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 377.6 |
| smp_best_thread | opus_r3sp_base.exe `07eb6fdeb058` | 2 | SmpBestThread=true | 500/500 | 40728 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 485.6 |
| smp_exact_nodes | opus_r3sp_base.exe `07eb6fdeb058` | 2 | SmpExactNodes=true | 500/500 | 49053 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 679.2 |
| lockless_tt | opus_r3sp_base.exe `07eb6fdeb058` | 2 | LocklessTT=true | 500/500 | 41538 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 551.8 |
| syzygy | opus_r3sp_base.exe `07eb6fdeb058` | 1 | SyzygyPath=D:/grok-pc-data/dwqww/.claude/worktrees/syzygy345 | 500/500 | 51988 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 313631 | 351.4 |
| corrhistplus7 | opus_r3sp_base.exe `07eb6fdeb058` | 1 | CorrHistPlus=7 | 500/500 | 49496 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 317529 | 396.6 |
| nnue_king_buckets_rm8 | opus_r3sp_base.exe `07eb6fdeb058` | 1 | NNUEKingBuckets=8, NNUEFile=F:/opus_scratch/r3/selfplay/nets/replica_rm8.fnn2 | 500/500 | 52239 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 352.4 |
| nnue_output_buckets8 | opus_r3sp_base.exe `07eb6fdeb058` | 1 | NNUEOutputBuckets=8, NNUEFile=F:/opus_scratch/r3/selfplay/nets/replica_r1_ob8.fnn2 | 500/500 | 50844 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 350.4 |
| nnue_threats | opus_r3sp_base.exe `07eb6fdeb058` | 1 | NNUEThreats=1, NNUEFile=F:/opus_scratch/r3/selfplay/nets/replica_r1_thr0.fnn2 | 500/500 | 53581 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 360.4 |
| nnue_pawn_pairs | opus_r3sp_base.exe `07eb6fdeb058` | 1 | NNUEPawnPairs=1, NNUEFile=F:/opus_scratch/r3/selfplay/nets/replica_r1_pp0.fnn2 | 500/500 | 53538 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 357.4 |
| pure_nnue | opus_r3sp_base.exe `07eb6fdeb058` | 1 | PureNnue=1, NNUEFile=F:/opus_scratch/r3/selfplay/nets/pure_material.fnn2 | 500/500 | 55757 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 450072 | 352.3 |
| corr_margins | opus_r3sp_base.exe `07eb6fdeb058` | 1 | CorrMargins=1 | 500/500 | 53495 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 343365 | 344.3 |
| corr_ext | opus_r3sp_base.exe `07eb6fdeb058` | 1 | CorrExt=1 | 500/500 | 52466 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312961 | 338.3 |
| cuckoo_rep | opus_r3sp_base.exe `07eb6fdeb058` | 1 | CuckooRep=true | 500/500 | 54526 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 324211 | 346.3 |
| material_key_table | opus_r3sp_base.exe `07eb6fdeb058` | 1 | MaterialKeyTable=true | 500/500 | 53913 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 343.3 |
| netscale90 | opus_r3sp_base.exe `07eb6fdeb058` | 1 | NetScale=90 | 500/500 | 52832 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 314443 | 336.3 |
| netscale110 | opus_r3sp_base.exe `07eb6fdeb058` | 1 | NetScale=110 | 500/500 | 55596 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 268059 | 348.3 |
| hist_rework1 | opus_r3sp_base.exe `07eb6fdeb058` | 1 | HistRework=1 | 500/500 | 54252 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 373261 | 345.4 |
| hist_rework2 | opus_r3sp_base.exe `07eb6fdeb058` | 1 | HistRework=2 | 500/500 | 53877 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 320427 | 343.3 |
| hist_rework3 | opus_r3sp_base.exe `07eb6fdeb058` | 1 | HistRework=3 | 500/500 | 51783 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 336192 | 329.3 |
| intended_threefold | opus_r3sp_base.exe `07eb6fdeb058` | 1 | IntendedThreefold=true | 500/500 | 54165 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 339.3 |
| sw_nnue_o2 | opus_r3sp_o2.exe `373ae98655a1` | 1 | (none) | 500/500 | 52609 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 334.3 |
| sw_nozero_move_buffers | opus_r3sp_nozero.exe `2ab5ba01c222` | 1 | (none) | 500/500 | 56021 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 338.2 |
| sw_s13_tt_child_prefetch | opus_r3sp_s13.exe `d7c61881dfa7` | 1 | TtChildPrefetch=true | 500/500 | 54142 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 338.3 |
| sw_speedstack | opus_r3sp_speedstack.exe `2e6b15b4c101` | 1 | (none) | 500/500 | 53399 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 336.3 |
| corrhistplus1 | opus_r3sp_base.exe `07eb6fdeb058` | 1 | CorrHistPlus=1 | 500/500 | 53262 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 318363 | 324.3 |
| corrhistplus2 | opus_r3sp_base.exe `07eb6fdeb058` | 1 | CorrHistPlus=2 | 500/500 | 54755 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 296553 | 329.2 |
| corrhistplus4 | opus_r3sp_base.exe `07eb6fdeb058` | 1 | CorrHistPlus=4 | 500/500 | 54768 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 340927 | 342.3 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| all_on | 51187 | 47519 | 1961030 | 52187 | 2252 | 1473 | 28374/4000/4902/3892/2842/2393/2423 | 1017 | 50170 | 1 (12.5 ms) | checkmate 452, threefold 19, insufficient_material 16, ply_cap 8, stalemate 5 |
| all_on_pure | 54862 | 50987 | 1966903 | 55862 | 2450 | 1568 | 30331/4231/5231/4147/3112/2592/2638 | 1054 | 53808 | 3 (6.0 ms) | checkmate 443, threefold 21, ply_cap 18, insufficient_material 16, stalemate 1, fifty_moves 1 |
| all_on_v1net | 53517 | 50483 | 2404982 | 54517 | 2482 | 1503 | 29569/4114/5139/4030/3001/2536/2596 | 708 | 52809 | 5 (8.6 ms) | checkmate 445, threefold 34, insufficient_material 8, ply_cap 7, fifty_moves 5, stalemate 1 |
| hard_deadline10 | 51340 | 48194 | 2359999 | 52340 | 2339 | 1453 | 28387/3983/4945/3850/2913/2407/2463 | 261 | 0 | 0 (0.0 ms) | checkmate 463, threefold 16, insufficient_material 11, ply_cap 10 |
| sw_nnue_lazy_acc | 54156 | 51544 | 2598553 | 55156 | 2490 | 1527 | 29900/4269/5148/4061/3098/2548/2596 | 0 | 0 | 0 (0.0 ms) | checkmate 435, threefold 33, ply_cap 20, insufficient_material 10, stalemate 1, fifty_moves 1 |
| sw_prof | 54085 | 51883 | 2603917 | 55085 | 2436 | 1563 | 29883/4111/5194/4136/3048/2531/2624 | 0 | 54085 | 0 (0.0 ms) | checkmate 429, threefold 39, ply_cap 16, insufficient_material 13, fifty_moves 2, stalemate 1 |
| sw_nnue_int16 | 52842 | 50291 | 2524656 | 53842 | 2353 | 1531 | 29402/3956/5093/3906/2951/2464/2570 | 0 | 0 | 0 (0.0 ms) | checkmate 450, threefold 28, insufficient_material 10, ply_cap 10, fifty_moves 2 |
| sw_attacks_init_once | 52707 | 50112 | 2533590 | 53707 | 2312 | 1493 | 29166/4025/5130/3946/2980/2433/2547 | 0 | 0 | 0 (0.0 ms) | checkmate 444, threefold 28, insufficient_material 13, ply_cap 10, stalemate 3, fifty_moves 2 |
| off | 52834 | 49925 | 2508127 | 53834 | 2377 | 1457 | 29255/4070/5064/3993/2912/2446/2583 | 0 | 0 | 1 (7.1 ms) | checkmate 440, threefold 28, insufficient_material 17, ply_cap 13, fifty_moves 1, stalemate 1 |
| smp_best_thread | 42697 | 32946 | 1794851 | 43697 | 1898 | 1240 | 23699/3286/4100/3240/2344/2028/2031 | 0 | 0 | 1 (10.8 ms) | checkmate 459, insufficient_material 25, stalemate 9, threefold 5, ply_cap 1, fifty_moves 1 |
| smp_exact_nodes | 51493 | 48263 | 2434473 | 52493 | 2336 | 1460 | 28441/3950/4937/3911/2854/2459/2501 | 0 | 0 | 2 (11.6 ms) | checkmate 455, threefold 19, ply_cap 12, insufficient_material 12, fifty_moves 2 |
| lockless_tt | 43527 | 33779 | 1826395 | 44527 | 1968 | 1235 | 24186/3363/4187/3272/2454/2025/2051 | 0 | 0 | 1 (49.5 ms) | checkmate 468, insufficient_material 13, threefold 8, stalemate 7, ply_cap 4 |
| syzygy | 54547 | 52265 | 2669680 | 55547 | 2403 | 1562 | 30157/4220/5278/4153/3051/2500/2629 | 0 | 0 | 0 (0.0 ms) | checkmate 441, threefold 32, insufficient_material 13, ply_cap 12, stalemate 1, fifty_moves 1 |
| corrhistplus7 | 51899 | 49249 | 2479523 | 52899 | 2368 | 1497 | 28772/3982/5024/3917/2934/2395/2472 | 0 | 0 | 0 (0.0 ms) | checkmate 441, threefold 30, ply_cap 15, insufficient_material 11, fifty_moves 2, stalemate 1 |
| nnue_king_buckets_rm8 | 54806 | 52741 | 2635197 | 55806 | 2436 | 1527 | 30319/4208/5259/4142/3057/2611/2643 | 0 | 0 | 0 (0.0 ms) | checkmate 430, threefold 28, insufficient_material 20, ply_cap 20, fifty_moves 1, stalemate 1 |
| nnue_output_buckets8 | 53307 | 51022 | 2524113 | 54307 | 2378 | 1553 | 29549/4029/5168/4000/3061/2517/2520 | 0 | 0 | 0 (0.0 ms) | checkmate 428, threefold 40, insufficient_material 17, ply_cap 13, stalemate 1, fifty_moves 1 |
| nnue_threats | 56198 | 54371 | 2632344 | 57198 | 2524 | 1595 | 31081/4299/5446/4191/3193/2677/2694 | 0 | 0 | 0 (0.0 ms) | checkmate 424, threefold 34, ply_cap 20, insufficient_material 16, fifty_moves 5, stalemate 1 |
| nnue_pawn_pairs | 56199 | 54277 | 2676576 | 57199 | 2542 | 1609 | 31135/4312/5280/4273/3219/2583/2736 | 0 | 0 | 0 (0.0 ms) | checkmate 431, threefold 42, ply_cap 19, insufficient_material 7, fifty_moves 1 |
| pure_nnue | 58546 | 56805 | 2614853 | 59546 | 2649 | 1641 | 32335/4526/5586/4411/3263/2764/2872 | 0 | 0 | 0 (0.0 ms) | checkmate 417, threefold 35, ply_cap 32, insufficient_material 14, stalemate 2 |
| corr_margins | 56123 | 54291 | 2849371 | 57123 | 2564 | 1552 | 31040/4318/5379/4227/3192/2638/2701 | 0 | 0 | 0 (0.0 ms) | checkmate 423, threefold 44, ply_cap 17, insufficient_material 13, fifty_moves 2, stalemate 1 |
| corr_ext | 55071 | 53396 | 2821271 | 56071 | 2415 | 1542 | 30469/4149/5271/4190/3114/2593/2680 | 0 | 0 | 0 (0.0 ms) | checkmate 425, threefold 49, ply_cap 20, insufficient_material 5, stalemate 1 |
| cuckoo_rep | 57207 | 55468 | 2986171 | 58207 | 2561 | 1592 | 31495/4523/5508/4363/3203/2685/2749 | 0 | 0 | 0 (0.0 ms) | checkmate 422, threefold 40, ply_cap 21, insufficient_material 14, fifty_moves 3 |
| material_key_table | 56567 | 54905 | 2941309 | 57567 | 2589 | 1617 | 31246/4341/5442/4266/3185/2704/2729 | 0 | 0 | 0 (0.0 ms) | checkmate 424, threefold 45, ply_cap 17, insufficient_material 11, stalemate 2, fifty_moves 1 |
| netscale90 | 55448 | 53823 | 2855191 | 56448 | 2505 | 1602 | 30733/4198/5296/4200/3097/2630/2678 | 0 | 0 | 0 (0.0 ms) | checkmate 427, threefold 34, insufficient_material 20, ply_cap 17, fifty_moves 2 |
| netscale110 | 58288 | 56662 | 3053845 | 59288 | 2600 | 1635 | 32381/4442/5561/4385/3327/2731/2769 | 0 | 0 | 0 (0.0 ms) | checkmate 431, threefold 28, ply_cap 27, insufficient_material 11, fifty_moves 2, stalemate 1 |
| hist_rework1 | 56963 | 55321 | 2947324 | 57963 | 2571 | 1640 | 31573/4328/5450/4243/3198/2684/2776 | 0 | 0 | 0 (0.0 ms) | checkmate 415, threefold 44, ply_cap 25, insufficient_material 15, fifty_moves 1 |
| hist_rework2 | 56585 | 54961 | 2852155 | 57585 | 2556 | 1558 | 31269/4331/5441/4273/3166/2618/2779 | 0 | 0 | 0 (0.0 ms) | checkmate 417, threefold 41, ply_cap 26, insufficient_material 13, stalemate 2, fifty_moves 1 |
| hist_rework3 | 54329 | 52663 | 2754439 | 55329 | 2420 | 1553 | 30003/4182/5312/4087/3035/2559/2605 | 0 | 0 | 0 (0.0 ms) | checkmate 439, threefold 37, ply_cap 11, insufficient_material 10, stalemate 2, fifty_moves 1 |
| intended_threefold | 56855 | 55174 | 2913813 | 57855 | 2529 | 1589 | 31459/4297/5477/4288/3230/2657/2757 | 0 | 0 | 0 (0.0 ms) | checkmate 419, threefold 43, ply_cap 24, insufficient_material 8, fifty_moves 4, stalemate 2 |
| sw_nnue_o2 | 55222 | 53538 | 2817174 | 56222 | 2488 | 1569 | 30616/4136/5329/4175/3100/2561/2692 | 0 | 0 | 0 (0.0 ms) | checkmate 422, threefold 46, insufficient_material 16, ply_cap 14, fifty_moves 2 |
| sw_nozero_move_buffers | 58752 | 57272 | 3152388 | 59752 | 2573 | 1628 | 32542/4508/5702/4444/3248/2783/2794 | 0 | 0 | 0 (0.0 ms) | checkmate 414, threefold 46, insufficient_material 20, ply_cap 18, stalemate 1, fifty_moves 1 |
| sw_s13_tt_child_prefetch | 56774 | 55177 | 2920565 | 57774 | 2545 | 1632 | 31484/4427/5471/4241/3226/2592/2701 | 0 | 0 | 0 (0.0 ms) | checkmate 413, threefold 49, ply_cap 19, insufficient_material 15, stalemate 2, fifty_moves 2 |
| sw_speedstack | 56045 | 54508 | 2908273 | 57045 | 2561 | 1570 | 30997/4319/5365/4227/3152/2616/2723 | 0 | 0 | 0 (0.0 ms) | checkmate 431, threefold 35, insufficient_material 18, ply_cap 14, stalemate 1, fifty_moves 1 |
| corrhistplus1 | 55875 | 54496 | 2994383 | 56875 | 2526 | 1553 | 30855/4353/5329/4290/3106/2646/2683 | 0 | 0 | 0 (0.0 ms) | checkmate 422, threefold 46, ply_cap 18, insufficient_material 12, stalemate 1, fifty_moves 1 |
| corrhistplus2 | 57486 | 56310 | 3153142 | 58486 | 2556 | 1631 | 31744/4394/5498/4362/3268/2691/2798 | 0 | 0 | 0 (0.0 ms) | checkmate 406, threefold 50, ply_cap 21, insufficient_material 21, stalemate 2 |
| corrhistplus4 | 57468 | 55927 | 2971469 | 58468 | 2559 | 1580 | 31809/4359/5541/4374/3191/2721/2773 | 0 | 0 | 0 (0.0 ms) | checkmate 411, threefold 46, ply_cap 29, insufficient_material 11, fifty_moves 2, stalemate 1 |
