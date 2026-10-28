# R3-1 self-play matrix, git head afd3ae98

Generated 2026-10-27 21:19:57 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| intended_threefold | opus_r3sp_base.exe `644830f9ecba` | 1 | IntendedThreefold=true | 500/500 | 56337 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 364.2 |
| corrhistplus1 | opus_r3sp_base.exe `644830f9ecba` | 1 | CorrHistPlus=1 | 500/500 | 56056 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 318363 | 365.2 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| intended_threefold | 59093 | 57862 | 2765791 | 60093 | 2661 | 1690 | 32742/4476/5706/4517/3356/2716/2824 | 0 | 0 | 0 (0.0 ms) | checkmate 413, threefold 51, ply_cap 17, insufficient_material 17, stalemate 1, fifty_moves 1 |
| corrhistplus1 | 58762 | 57603 | 2761546 | 59762 | 2678 | 1690 | 32473/4532/5644/4483/3324/2814/2786 | 0 | 0 | 0 (0.0 ms) | checkmate 407, threefold 49, ply_cap 27, insufficient_material 13, stalemate 2, fifty_moves 2 |
