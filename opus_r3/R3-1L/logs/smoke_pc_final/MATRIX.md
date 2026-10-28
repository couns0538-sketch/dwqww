# R3-1 self-play matrix, git head 34ef8a70

Generated 2026-10-27 23:17:07 by run_matrix.py from F:/opus_scratch/r3/R3-1L/smoke_final/runs; every engine also runs with Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: 0.

| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | double bestmoves | timeouts | malformed output | of which info after bestmove | HardDeadline answers | bench11 | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| smp_helpers_past_depth | opus_r3sp_base.exe `cb6f8897e333` | 2 | SmpHelpersPastDepth=true | 3/3 | 217 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 312866 | 3.0 |
| spsa_plus10 | opus_r3sp_base.exe `cb6f8897e333` | 1 | LmrQuietBase=94, LmrQuietDivisor=242, LmrNoisyBase=11, LmrNoisyDivisor=374, LmrHistoryDivisor=6600, LmrCutoffThreshold=4, NullMoveBase=4, NullMoveDepthDivisor=4, NullMoveEvalDivisor=220, NullMoveMarginDepth=26, NullMoveMarginBase=198, RfpMargin=79, RfpImproving=44, RfpDepth=9, FutilityBase=110, FutilityMultiplier=121, QsFutilityMargin=176, SeeQuietMultiplier=26, SeeNoisyMultiplier=165, AspirationDelta=20 | 3/3 | 217 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 320444 | 2.0 |
| spsa_minus10 | opus_r3sp_base.exe `cb6f8897e333` | 1 | LmrQuietBase=77, LmrQuietDivisor=198, LmrNoisyBase=9, LmrNoisyDivisor=306, LmrHistoryDivisor=5400, LmrCutoffThreshold=2, NullMoveBase=2, NullMoveDepthDivisor=2, NullMoveEvalDivisor=180, NullMoveMarginDepth=22, NullMoveMarginBase=162, RfpMargin=65, RfpImproving=36, RfpDepth=7, FutilityBase=90, FutilityMultiplier=99, QsFutilityMargin=144, SeeQuietMultiplier=22, SeeNoisyMultiplier=135, AspirationDelta=16 | 3/3 | 226 | **0** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 282806 | 4.0 |

## Coverage

| config | bestmoves | ponder moves checked | pv moves checked | isready barriers | mid-search isready | stray stops | go nodes/clock/movetime/depth/infinite/ponderhit/pondermiss | watchdog answers | profile blocks | clock overruns (max) | terminations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| smp_helpers_past_depth | 226 | 172 | 9516 | 232 | 14 | 7 | 126/18/27/18/8/11/9 | 0 | 0 | 0 (0.0 ms) | stalemate 1, checkmate 1, threefold 1 |
| spsa_plus10 | 221 | 207 | 7835 | 227 | 4 | 8 | 133/18/23/24/7/8/4 | 0 | 0 | 0 (0.0 ms) | checkmate 3 |
| spsa_minus10 | 230 | 219 | 10516 | 236 | 7 | 5 | 138/23/18/21/11/11/4 | 0 | 0 | 0 (0.0 ms) | checkmate 3 |
