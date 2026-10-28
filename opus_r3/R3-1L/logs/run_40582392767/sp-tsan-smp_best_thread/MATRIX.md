# R3-1 self-play matrix, git head afd3ae98

Generated 2026-10-27 21:33:38 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| smp_best_thread | opus_r3sp_base.exe `0ce5df3ee49c` | 2 | SmpBestThread=true | 100/100 | 11344 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 363.1 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| smp_best_thread | 11899 | 11302 | 208482 | 12099 | 551 | 344 | 6661/894/1124/880/648/571/566 | 0 | 0 | 37 (56.9 ms) | checkmate 86, ply_cap 8, threefold 4, insufficient_material 2 |
