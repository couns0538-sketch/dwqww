# R3-1 self-play matrix, git head afd3ae98

Generated 2026-10-27 21:28:53 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| off | opus_r3sp_base.exe `644830f9ecba` | 1 | (none) | 500/500 | 56212 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 358.2 |
| hard_deadline10 | opus_r3sp_base.exe `644830f9ecba` | 1 | HardDeadline=10 | 500/500 | 54859 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 353.2 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| off | 58915 | 57749 | 2783951 | 59915 | 2636 | 1637 | 32684/4547/5666/4449/3304/2794/2768 | 0 | 0 | 0 (0.0 ms) | checkmate 386, threefold 74, ply_cap 20, insufficient_material 15, fifty_moves 5 |
| hard_deadline10 | 57555 | 56446 | 2749629 | 58555 | 2548 | 1642 | 31854/4394/5547/4329/3243/2720/2772 | 0 | 0 | 0 (0.0 ms) | checkmate 410, threefold 54, ply_cap 21, insufficient_material 13, fifty_moves 2 |
