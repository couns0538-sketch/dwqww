# R3-1 self-play matrix, git head 6f4067c3

Generated 2026-10-27 21:40:20 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| spsa_minus10 | opus_r3sp_base.exe `d6190041a757` | 1 | LmrQuietBase=77, LmrQuietDivisor=198, LmrNoisyBase=9, LmrNoisyDivisor=306, LmrHistoryDivisor=5400, LmrCutoffThreshold=2, NullMoveBase=2, NullMoveDepthDivisor=2, NullMoveEvalDivisor=180, NullMoveMarginDepth=22, NullMoveMarginBase=162, RfpMargin=65, RfpImproving=36, RfpDepth=7, FutilityBase=90, FutilityMultiplier=99, QsFutilityMargin=144, SeeQuietMultiplier=22, SeeNoisyMultiplier=135, AspirationDelta=16 | 500/500 | 55963 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 282806 | 360.2 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| spsa_minus10 | 58677 | 57522 | 2905667 | 59677 | 2567 | 1664 | 32472/4484/5631/4547/3273/2768/2788 | 0 | 0 | 0 (0.0 ms) | checkmate 417, threefold 40, ply_cap 22, insufficient_material 17, fifty_moves 3, stalemate 1 |
