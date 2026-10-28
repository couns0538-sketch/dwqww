# R3-1 self-play matrix, git head afd3ae98

Generated 2026-10-27 21:32:47 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sw_nnue_int16 | opus_r3sp_int16.exe `4293370ba85c` | 1 | NnueInt16=true | 500/500 | 57466 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 330610 | 338.1 |
| sw_attacks_init_once | opus_r3sp_initonce.exe `f42b44756b0a` | 1 | (none) | 500/500 | 56467 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 326.1 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sw_nnue_int16 | 60323 | 59173 | 3256466 | 61323 | 2739 | 1690 | 33436/4618/5697/4533/3391/2863/2928 | 0 | 0 | 0 (0.0 ms) | checkmate 402, threefold 50, ply_cap 32, insufficient_material 14, stalemate 1, fifty_moves 1 |
| sw_attacks_init_once | 59266 | 58118 | 3243928 | 60266 | 2677 | 1699 | 32708/4529/5697/4517/3341/2797/2878 | 0 | 0 | 0 (0.0 ms) | checkmate 406, threefold 54, ply_cap 23, insufficient_material 16, fifty_moves 1 |
