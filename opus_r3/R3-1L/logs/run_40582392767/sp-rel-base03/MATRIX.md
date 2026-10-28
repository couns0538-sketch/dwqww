# R3-1 self-play matrix, git head afd3ae98

Generated 2026-10-27 21:16:39 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| nnue_king_buckets_rm8 | opus_r3sp_base.exe `644830f9ecba` | 1 | NNUEKingBuckets=8, NNUEFile=/home/runner/work/dwqww/dwqww/sp_out/nets/replica_rm8.fnn2 | 500/500 | 55885 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 362.2 |
| nnue_output_buckets8 | opus_r3sp_base.exe `644830f9ecba` | 1 | NNUEOutputBuckets=8, NNUEFile=/home/runner/work/dwqww/dwqww/sp_out/nets/replica_r1_ob8.fnn2 | 500/500 | 55413 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 359.2 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| nnue_king_buckets_rm8 | 58708 | 57555 | 2706132 | 59708 | 2633 | 1691 | 32356/4444/5649/4481/3322/2738/2895 | 0 | 0 | 0 (0.0 ms) | checkmate 407, threefold 47, ply_cap 32, insufficient_material 12, fifty_moves 2 |
| nnue_output_buckets8 | 58134 | 56985 | 2680873 | 59134 | 2600 | 1649 | 32206/4410/5556/4450/3253/2735/2803 | 0 | 0 | 0 (0.0 ms) | checkmate 407, threefold 52, ply_cap 19, insufficient_material 16, stalemate 3, fifty_moves 3 |
