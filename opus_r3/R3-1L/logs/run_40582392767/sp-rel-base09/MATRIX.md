# R3-1 self-play matrix, git head afd3ae98

Generated 2026-10-27 21:15:03 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| hist_rework2 | opus_r3sp_base.exe `644830f9ecba` | 1 | HistRework=2 | 500/500 | 56602 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 320427 | 359.2 |
| hist_rework3 | opus_r3sp_base.exe `644830f9ecba` | 1 | HistRework=3 | 500/500 | 57181 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 336192 | 360.2 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| hist_rework2 | 59379 | 58226 | 2763207 | 60379 | 2697 | 1673 | 32932/4487/5717/4530/3315/2774/2847 | 0 | 0 | 0 (0.0 ms) | checkmate 405, threefold 51, ply_cap 23, insufficient_material 17, fifty_moves 2, stalemate 2 |
| hist_rework3 | 60039 | 58867 | 2869135 | 61039 | 2673 | 1707 | 33193/4616/5771/4544/3364/2762/2931 | 0 | 0 | 0 (0.0 ms) | checkmate 401, threefold 48, ply_cap 33, insufficient_material 11, fifty_moves 6, stalemate 1 |
