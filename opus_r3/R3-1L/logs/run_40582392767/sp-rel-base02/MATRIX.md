# R3-1 self-play matrix, git head afd3ae98

Generated 2026-10-27 21:27:24 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| syzygy | opus_r3sp_base.exe `644830f9ecba` | 1 | SyzygyPath=/home/runner/syzygy345 | 500/500 | 55560 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 313631 | 337.1 |
| corrhistplus7 | opus_r3sp_base.exe `644830f9ecba` | 1 | CorrHistPlus=7 | 500/500 | 56475 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 317529 | 345.1 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| syzygy | 58279 | 56971 | 2891534 | 59279 | 2634 | 1706 | 32393/4433/5535/4418/3248/2743/2790 | 0 | 0 | 0 (0.0 ms) | checkmate 400, threefold 52, ply_cap 24, insufficient_material 22, fifty_moves 2 |
| corrhistplus7 | 59266 | 58124 | 3013761 | 60266 | 2609 | 1693 | 32751/4600/5738/4385/3336/2807/2858 | 0 | 0 | 0 (0.0 ms) | checkmate 411, threefold 42, ply_cap 30, insufficient_material 14, fifty_moves 2, stalemate 1 |
