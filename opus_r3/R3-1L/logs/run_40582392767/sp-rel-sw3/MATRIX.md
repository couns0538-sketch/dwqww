# R3-1 self-play matrix, git head afd3ae98

Generated 2026-10-27 21:33:10 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sw_nnue_o2 | opus_r3sp_o2.exe `6cde63b71c25` | 1 | (none) | 500/500 | 57118 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 364.2 |
| sw_nozero_move_buffers | opus_r3sp_nozero.exe `26f0fd821207` | 1 | (none) | 500/500 | 56021 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 358.2 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sw_nnue_o2 | 59917 | 58737 | 2860533 | 60917 | 2668 | 1723 | 33277/4532/5798/4518/3358/2753/2882 | 0 | 0 | 0 (0.0 ms) | checkmate 406, threefold 41, ply_cap 29, insufficient_material 18, fifty_moves 5, stalemate 1 |
| sw_nozero_move_buffers | 58738 | 57592 | 2802910 | 59738 | 2648 | 1644 | 32561/4538/5579/4471/3313/2768/2791 | 0 | 0 | 0 (0.0 ms) | checkmate 400, threefold 49, ply_cap 30, insufficient_material 19, fifty_moves 2 |
