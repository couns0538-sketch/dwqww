# R3-1 self-play matrix, git head afd3ae98

Generated 2026-10-27 21:29:25 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| corr_ext | opus_r3sp_base.exe `644830f9ecba` | 1 | CorrExt=1 | 500/500 | 54991 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312961 | 323.1 |
| cuckoo_rep | opus_r3sp_base.exe `644830f9ecba` | 1 | CuckooRep=true | 500/500 | 55879 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 324211 | 326.1 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| corr_ext | 57730 | 56591 | 3073946 | 58730 | 2569 | 1625 | 31988/4418/5513/4365/3198/2700/2809 | 0 | 0 | 0 (0.0 ms) | checkmate 414, threefold 51, ply_cap 18, insufficient_material 14, fifty_moves 3 |
| cuckoo_rep | 58660 | 57436 | 3198001 | 59660 | 2621 | 1580 | 32580/4445/5653/4397/3242/2716/2846 | 0 | 0 | 0 (0.0 ms) | checkmate 403, threefold 55, ply_cap 30, insufficient_material 9, fifty_moves 3 |
