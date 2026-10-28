# R3-1 self-play matrix, git head afd3ae98

Generated 2026-10-27 21:42:22 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure_nnue | opus_r3sp_base.exe `644830f9ecba` | 1 | PureNnue=1, NNUEFile=/home/runner/work/dwqww/dwqww/sp_out/nets/pure_material.fnn2 | 500/500 | 60098 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 450072 | 367.1 |
| corr_margins | opus_r3sp_base.exe `644830f9ecba` | 1 | CorrMargins=1 | 500/500 | 55656 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 343365 | 353.2 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| pure_nnue | 63077 | 61899 | 2590922 | 64077 | 2894 | 1775 | 34870/4825/6011/4781/3583/2976/3052 | 0 | 0 | 0 (0.0 ms) | checkmate 389, ply_cap 51, threefold 40, insufficient_material 19, fifty_moves 1 |
| corr_margins | 58410 | 57278 | 2721907 | 59410 | 2645 | 1621 | 32226/4531/5655/4404/3314/2697/2829 | 0 | 0 | 0 (0.0 ms) | checkmate 403, threefold 58, ply_cap 19, insufficient_material 16, fifty_moves 4 |
