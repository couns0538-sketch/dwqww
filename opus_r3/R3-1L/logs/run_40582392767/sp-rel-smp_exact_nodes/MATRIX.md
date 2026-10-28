# R3-1 self-play matrix, git head afd3ae98

Generated 2026-10-27 21:15:08 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| smp_exact_nodes | opus_r3sp_base.exe `644830f9ecba` | 2 | SmpExactNodes=true | 500/500 | 53939 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 514.3 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| smp_exact_nodes | 56579 | 54844 | 2500409 | 57579 | 2544 | 1614 | 31323/4335/5439/4313/3173/2643/2713 | 0 | 0 | 0 (0.0 ms) | checkmate 429, threefold 33, ply_cap 21, insufficient_material 16, fifty_moves 1 |
