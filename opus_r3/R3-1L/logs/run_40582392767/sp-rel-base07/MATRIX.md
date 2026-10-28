# R3-1 self-play matrix, git head afd3ae98

Generated 2026-10-27 21:30:10 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| material_key_table | opus_r3sp_base.exe `644830f9ecba` | 1 | MaterialKeyTable=true | 500/500 | 56044 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 326.1 |
| netscale90 | opus_r3sp_base.exe `644830f9ecba` | 1 | NetScale=90 | 500/500 | 55384 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 314443 | 325.1 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| material_key_table | 58841 | 57697 | 3171179 | 59841 | 2684 | 1661 | 32725/4431/5584/4381/3261/2795/2867 | 0 | 0 | 0 (0.0 ms) | checkmate 386, threefold 65, ply_cap 29, insufficient_material 16, fifty_moves 4 |
| netscale90 | 58096 | 56967 | 3106328 | 59096 | 2590 | 1611 | 32148/4455/5660/4328/3228/2780/2785 | 0 | 0 | 0 (0.0 ms) | checkmate 415, threefold 51, ply_cap 22, insufficient_material 10, stalemate 2 |
