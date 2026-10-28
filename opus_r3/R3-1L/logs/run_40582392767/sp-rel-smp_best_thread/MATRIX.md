# R3-1 self-play matrix, git head afd3ae98

Generated 2026-10-27 21:17:43 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| smp_best_thread | opus_r3sp_base.exe `644830f9ecba` | 2 | SmpBestThread=true | 500/500 | 43228 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 418.3 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| smp_best_thread | 45336 | 36990 | 1839793 | 46336 | 2074 | 1326 | 25104/3449/4353/3454/2512/2185/2171 | 0 | 0 | 0 (0.0 ms) | checkmate 446, insufficient_material 23, stalemate 17, threefold 10, ply_cap 3, fifty_moves 1 |
