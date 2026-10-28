# R3-1 self-play matrix, git head afd3ae98

Generated 2026-10-27 21:29:40 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lockless_tt | opus_r3sp_base.exe `0ce5df3ee49c` | 2 | LocklessTT=true | 100/100 | 10785 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 277.1 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| lockless_tt | 11317 | 10734 | 208416 | 11517 | 494 | 330 | 6291/872/1054/882/589/553/544 | 0 | 0 | 28 (35.7 ms) | checkmate 87, threefold 5, ply_cap 5, insufficient_material 2, stalemate 1 |
