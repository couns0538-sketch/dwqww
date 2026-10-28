# R3-1 self-play matrix, git head 6f4067c3

Generated 2026-10-27 21:40:15 by run_matrix.py from /home/runner/work/dwqww/dwqww/sp_out/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| spsa_plus10 | opus_r3sp_base.exe `d6190041a757` | 1 | LmrQuietBase=94, LmrQuietDivisor=242, LmrNoisyBase=11, LmrNoisyDivisor=374, LmrHistoryDivisor=6600, LmrCutoffThreshold=4, NullMoveBase=4, NullMoveDepthDivisor=4, NullMoveEvalDivisor=220, NullMoveMarginDepth=26, NullMoveMarginBase=198, RfpMargin=79, RfpImproving=44, RfpDepth=9, FutilityBase=110, FutilityMultiplier=121, QsFutilityMargin=176, SeeQuietMultiplier=26, SeeNoisyMultiplier=165, AspirationDelta=20 | 500/500 | 55625 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 320444 | 357.2 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| spsa_plus10 | 58376 | 57245 | 2685081 | 59376 | 2642 | 1679 | 32374/4391/5602/4422/3277/2737/2822 | 0 | 0 | 0 (0.0 ms) | checkmate 401, threefold 50, ply_cap 27, insufficient_material 18, stalemate 2, fifty_moves 2 |
