# R3-1 self-play matrix, git head afd3ae98

Generated 2026-10-27 21:38:10 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| corrhistplus2 | opus_r3sp_base.exe `644830f9ecba` | 1 | CorrHistPlus=2 | 500/500 | 55935 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 296553 | 360.2 |
| corrhistplus4 | opus_r3sp_base.exe `644830f9ecba` | 1 | CorrHistPlus=4 | 500/500 | 57072 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 340927 | 366.2 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| corrhistplus2 | 58743 | 57597 | 2747643 | 59743 | 2576 | 1680 | 32516/4462/5673/4420/3266/2714/2884 | 0 | 0 | 0 (0.0 ms) | checkmate 414, threefold 48, insufficient_material 19, ply_cap 16, fifty_moves 3 |
| corrhistplus4 | 59913 | 58741 | 2843097 | 60913 | 2681 | 1709 | 33142/4595/5792/4559/3282/2784/2918 | 0 | 0 | 0 (0.0 ms) | checkmate 416, threefold 31, ply_cap 29, insufficient_material 20, stalemate 2, fifty_moves 2 |
