# Item B - SPSA tuner and exposed search constants - RESULTS

No Elo claim: the crew gates (UHO [0,5] SPRT, 8moves_v3 confirm). Own games are tuning only.

## Options (step B.2)
- The lock exe FD3A5190 (kit -Expose) already advertises 41 search constants + 10 time-management constants at the
  lock's own values (`uci_options`, 2026-11-03 15:5x): LmrQuietBase, LmrQuietDivisor, LmrNoisyBase, LmrNoisyDivisor,
  NullMoveMinDepth, NullMoveBase, NullMoveDepthDivisor, NullMoveEvalDivisor, RfpDepth, RfpMargin, RfpImproving,
  RazorDepth, RazorBase, RazorMultiplier, FutilityDepth, FutilityBase, FutilityMultiplier, LmpBase, HistoryPruneDepth,
  HistoryPruneMultiplier, SeeQuietMultiplier, SeeNoisyMultiplier, SingularDepth, SingularMargin, IirDepth, ProbcutDepth,
  ProbcutMargin, QsFutilityMargin, QsSeeMargin, AspirationDelta, HistoryBonusQuadratic, HistoryBonusLinear,
  HistoryBonusMax, LmrHistoryDivisor, CheckExtensionDepth, LmrCutoffThreshold, MaterialCorrectionWeight,
  CaptureFutilityBase, CaptureFutilityMultiplier, CaptureFutilityDepth, FailLowContinuationBonus.
- New: `opus_30h/b/o30_expose.py` exposes 22 more (18 anchored edits in src/search.cpp, the literal sites R9 proved
  identical; no switch: each option's default is the literal it replaces): NmpEvalDepthMargin 24, NmpEvalBase 180,
  NullMoveEvalMax 3, NullMoveVerifyDepth 14, ProbcutImproving 50, ProbcutReduction 4, SingularTtDepth 3,
  SingularDoubleMargin 24, SingularDoubleLimit 6, LmrTtPv / LmrNotImproving / LmrTtCapture / LmrGivesCheck / LmrInCheck /
  LmrCutoffCount 1024 and LmrCutNode 2048 (LMR adjustments in 1/1024 ply), HistoryMalusPercent 100,
  HistoryDepthBonusMargin 100, AspirationMinDepth 4, AspirationGrowPercent 50, AspirationGrowAdd 4, QuietCheckBonus 12000.
  Patch `opus_30h/b/expose22.patch` md5 73cd35917a872d2a00b8ce6219d6f7d7.
| check | result |
|---|---|
| plain build `D:\o30\plain\spsa_1\forge_plain.exe` (sha256 3e8cf18f03506b2c33c688355ad43458bafcf7c534c02bbff96499a871522e5a) | 0 warnings, vfmadd 0 |
| defaults = lock: pin_check -Full | PASS d11 312866 / d13 862329 / d16 3024920 / d20 12389307 / d22 34048354, perft 4865609 / 193690690 |
| each new option moved once (pin_check ON mode, d11/d13/d16 must differ) | 22 / 22 LIVE (LmrNotImproving and LmrInCheck were dead at half-ply values 1536 / 512 - the other LMR terms are whole plies, so a lone half ply rounds away - and LIVE at whole-ply values 2048 / 0) |
