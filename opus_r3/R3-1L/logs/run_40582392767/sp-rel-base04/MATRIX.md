# R3-1 self-play matrix, git head afd3ae98

Generated 2026-10-27 21:20:52 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| nnue_threats | opus_r3sp_base.exe `644830f9ecba` | 1 | NNUEThreats=1, NNUEFile=/home/runner/work/dwqww/dwqww/sp_out/nets/replica_r1_thr0.fnn2 | 500/500 | 55296 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 360.1 |
| nnue_pawn_pairs | opus_r3sp_base.exe `644830f9ecba` | 1 | NNUEPawnPairs=1, NNUEFile=/home/runner/work/dwqww/dwqww/sp_out/nets/replica_r1_pp0.fnn2 | 500/500 | 55803 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 356.1 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| nnue_threats | 57990 | 56856 | 2604249 | 58990 | 2608 | 1688 | 32127/4466/5546/4378/3264/2765/2750 | 0 | 0 | 0 (0.0 ms) | checkmate 407, threefold 48, ply_cap 23, insufficient_material 20, fifty_moves 1, stalemate 1 |
| nnue_pawn_pairs | 58608 | 57485 | 2746375 | 59608 | 2693 | 1646 | 32467/4459/5533/4437/3287/2749/2871 | 0 | 0 | 0 (0.0 ms) | checkmate 394, threefold 53, ply_cap 27, insufficient_material 20, fifty_moves 4, stalemate 2 |
