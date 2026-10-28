# R3-1 self-play matrix, git head afd3ae98

Generated 2026-10-27 21:43:55 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sw_nnue_lazy_acc | opus_r3sp_lazyacc.exe `7657f7003d52` | 1 | NnueLazyAcc=true | 500/500 | 57208 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 368.2 |
| sw_prof | opus_r3sp_prof.exe `cba7e7e67d9b` | 1 | Profile=true | 500/500 | 56857 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 386.2 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sw_nnue_lazy_acc | 59992 | 58838 | 2822597 | 60992 | 2648 | 1678 | 33319/4613/5709/4504/3365/2843/2855 | 0 | 0 | 0 (0.0 ms) | checkmate 408, threefold 44, ply_cap 28, insufficient_material 17, fifty_moves 3 |
| sw_prof | 59665 | 58484 | 2866220 | 60665 | 2694 | 1685 | 32918/4562/5758/4551/3395/2792/2881 | 0 | 59665 | 0 (0.0 ms) | checkmate 404, threefold 53, ply_cap 26, insufficient_material 14, fifty_moves 3 |
