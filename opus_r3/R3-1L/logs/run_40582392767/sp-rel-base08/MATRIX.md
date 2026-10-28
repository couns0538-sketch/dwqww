# R3-1 self-play matrix, git head afd3ae98

Generated 2026-10-27 21:33:47 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| netscale110 | opus_r3sp_base.exe `644830f9ecba` | 1 | NetScale=110 | 500/500 | 56854 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 268059 | 344.1 |
| hist_rework1 | opus_r3sp_base.exe `644830f9ecba` | 1 | HistRework=1 | 500/500 | 56692 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 373261 | 347.1 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| netscale110 | 59638 | 58475 | 3076509 | 60638 | 2641 | 1688 | 33042/4553/5718/4545/3317/2825/2854 | 0 | 0 | 0 (0.0 ms) | checkmate 416, threefold 43, ply_cap 24, insufficient_material 14, fifty_moves 3 |
| hist_rework1 | 59499 | 58322 | 3009894 | 60499 | 2621 | 1699 | 32882/4608/5752/4484/3322/2776/2868 | 0 | 0 | 0 (0.0 ms) | checkmate 413, threefold 46, ply_cap 24, insufficient_material 13, fifty_moves 4 |
