# R3-1 self-play matrix, git head afd3ae98

Generated 2026-10-27 21:37:10 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lockless_tt | opus_r3sp_base.exe `644830f9ecba` | 2 | LocklessTT=true | 500/500 | 44565 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 436.3 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| lockless_tt | 46803 | 39691 | 1966046 | 47803 | 2132 | 1362 | 25860/3612/4504/3483/2610/2203/2293 | 0 | 0 | 0 (0.0 ms) | checkmate 441, insufficient_material 31, threefold 16, stalemate 5, ply_cap 5, fifty_moves 2 |
