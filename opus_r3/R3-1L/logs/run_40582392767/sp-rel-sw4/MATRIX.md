# R3-1 self-play matrix, git head afd3ae98

Generated 2026-10-27 21:35:20 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sw_s13_tt_child_prefetch | opus_r3sp_s13.exe `045b297298cd` | 1 | TtChildPrefetch=true | 500/500 | 56220 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 361.2 |
| sw_speedstack | opus_r3sp_speedstack.exe `476a82c4477a` | 1 | (none) | 500/500 | 56303 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 364.2 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sw_s13_tt_child_prefetch | 58958 | 57796 | 2790680 | 59958 | 2650 | 1671 | 32720/4470/5689/4468/3319/2753/2801 | 0 | 0 | 0 (0.0 ms) | checkmate 413, threefold 42, ply_cap 23, insufficient_material 18, fifty_moves 4 |
| sw_speedstack | 59089 | 57944 | 2802280 | 60089 | 2659 | 1684 | 32727/4507/5694/4434/3320/2758/2863 | 0 | 0 | 0 (0.0 ms) | checkmate 410, threefold 45, ply_cap 24, insufficient_material 20, fifty_moves 1 |
