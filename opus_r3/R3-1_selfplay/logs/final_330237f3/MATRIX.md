# R3-1 self-play matrix, git head 330237f3

Generated 2026-10-27 22:48:50 by run_matrix.py from F:/opus_scratch/r3/selfplay/runs/330237f3; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

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
| off | not run | | | | | | | | | | | | | |
| smp_best_thread | opus_r3sp_base.exe `07eb6fdeb058` | 2 | SmpBestThread=true | 500/500 | 40728 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 485.6 |
| smp_exact_nodes | not run | | | | | | | | | | | | | |
| lockless_tt | not run | | | | | | | | | | | | | |
| syzygy | not run | | | | | | | | | | | | | |
| corrhistplus7 | not run | | | | | | | | | | | | | |
| nnue_king_buckets_rm8 | not run | | | | | | | | | | | | | |
| nnue_output_buckets8 | not run | | | | | | | | | | | | | |
| nnue_threats | not run | | | | | | | | | | | | | |
| nnue_pawn_pairs | not run | | | | | | | | | | | | | |
| pure_nnue | not run | | | | | | | | | | | | | |
| corr_margins | not run | | | | | | | | | | | | | |
| corr_ext | not run | | | | | | | | | | | | | |
| cuckoo_rep | not run | | | | | | | | | | | | | |
| material_key_table | not run | | | | | | | | | | | | | |
| netscale90 | not run | | | | | | | | | | | | | |
| netscale110 | not run | | | | | | | | | | | | | |
| hist_rework1 | not run | | | | | | | | | | | | | |
| hist_rework2 | not run | | | | | | | | | | | | | |
| hist_rework3 | not run | | | | | | | | | | | | | |
| intended_threefold | not run | | | | | | | | | | | | | |
| sw_nnue_o2 | not run | | | | | | | | | | | | | |
| sw_nozero_move_buffers | not run | | | | | | | | | | | | | |
| sw_s13_tt_child_prefetch | not run | | | | | | | | | | | | | |
| sw_speedstack | not run | | | | | | | | | | | | | |
| corrhistplus1 | not run | | | | | | | | | | | | | |
| corrhistplus2 | not run | | | | | | | | | | | | | |
| corrhistplus4 | not run | | | | | | | | | | | | | |

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
| smp_best_thread | 42697 | 32946 | 1794851 | 43697 | 1898 | 1240 | 23699/3286/4100/3240/2344/2028/2031 | 0 | 0 | 1 (10.8 ms) | checkmate 459, insufficient_material 25, stalemate 9, threefold 5, ply_cap 1, fifty_moves 1 |
