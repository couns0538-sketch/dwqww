| # | parameter | lock value | engine range | origin | bench 11 moves | tuned in stc_main (range, c_end) |
|---|---|---|---|---|---|---|
| 1 | LmrQuietBase | 85 | 0..300 | lock tune:: | yes | yes (0..200, 12) |
| 2 | LmrQuietDivisor | 220 | 100..500 | lock tune:: | yes | yes (120..400, 16) |
| 3 | LmrNoisyBase | 10 | 0..300 | lock tune:: | yes |  |
| 4 | LmrNoisyDivisor | 340 | 100..800 | lock tune:: | yes |  |
| 5 | NullMoveMinDepth | 3 | 1..10 | lock tune:: | yes |  |
| 6 | NullMoveBase | 3 | 1..6 | lock tune:: | yes |  |
| 7 | NullMoveDepthDivisor | 3 | 1..10 | lock tune:: | yes |  |
| 8 | NullMoveEvalDivisor | 200 | 50..1000 | lock tune:: | yes |  |
| 9 | RfpDepth | 8 | 0..15 | lock tune:: | yes |  |
| 10 | RfpMargin | 72 | 10..300 | lock tune:: | yes | yes (30..150, 7) |
| 11 | RfpImproving | 40 | 0..200 | lock tune:: | yes |  |
| 12 | RazorDepth | 2 | 0..6 | lock tune:: | yes |  |
| 13 | RazorBase | 150 | 0..1000 | lock tune:: | yes |  |
| 14 | RazorMultiplier | 350 | 0..1000 | lock tune:: | yes |  |
| 15 | FutilityDepth | 7 | 0..15 | lock tune:: | yes |  |
| 16 | FutilityBase | 100 | 0..500 | lock tune:: | yes | yes (0..250, 14) |
| 17 | FutilityMultiplier | 110 | 0..500 | lock tune:: | yes | yes (40..250, 12) |
| 18 | LmpBase | 4 | 0..20 | lock tune:: | yes |  |
| 19 | HistoryPruneDepth | 3 | 0..10 | lock tune:: | no |  |
| 20 | HistoryPruneMultiplier | 2048 | 0..20000 | lock tune:: | yes |  |
| 21 | SeeQuietMultiplier | 24 | 0..200 | lock tune:: | yes | yes (5..60, 3) |
| 22 | SeeNoisyMultiplier | 150 | 0..1000 | lock tune:: | yes |  |
| 23 | SingularDepth | 7 | 2..20 | lock tune:: | yes |  |
| 24 | SingularMargin | 2 | 0..10 | lock tune:: | yes |  |
| 25 | IirDepth | 4 | 1..20 | lock tune:: | yes |  |
| 26 | ProbcutDepth | 5 | 1..20 | lock tune:: | yes |  |
| 27 | ProbcutMargin | 180 | 0..1000 | lock tune:: | yes | yes (80..350, 16) |
| 28 | QsFutilityMargin | 160 | 0..1000 | lock tune:: | yes |  |
| 29 | QsSeeMargin | 40 | 0..500 | lock tune:: | no |  |
| 30 | AspirationDelta | 18 | 4..200 | lock tune:: | yes | yes (6..50, 2.5) |
| 31 | HistoryBonusQuadratic | 20 | 0..100 | lock tune:: | yes |  |
| 32 | HistoryBonusLinear | 48 | 0..500 | lock tune:: | yes |  |
| 33 | HistoryBonusMax | 2048 | 100..10000 | lock tune:: | yes |  |
| 34 | LmrHistoryDivisor | 6000 | 1000..30000 | lock tune:: | yes |  |
| 35 | CheckExtensionDepth | 2 | 1..30 | lock tune:: | yes |  |
| 36 | LmrCutoffThreshold | 3 | 0..20 | lock tune:: | yes |  |
| 37 | MaterialCorrectionWeight | 100 | 0..300 | lock tune:: | yes |  |
| 38 | TmSoftDivisor | 22 | 5..80 | lock tune:: | no |  |
| 39 | TmIncrementPercent | 75 | 0..150 | lock tune:: | no |  |
| 40 | TmHardPercent | 60 | 10..95 | lock tune:: | no |  |
| 41 | TmHardSoftMultiple | 5 | 1..20 | lock tune:: | no |  |
| 42 | TmStableFactor | 60 | 20..150 | lock tune:: | no |  |
| 43 | TmSemiStableFactor | 80 | 20..150 | lock tune:: | no |  |
| 44 | TmUnstableFactor | 140 | 50..300 | lock tune:: | no |  |
| 45 | TmEffortBase | 155 | 100..250 | lock tune:: | no |  |
| 46 | TmFallingEvalPercent | 100 | 0..400 | lock tune:: | no |  |
| 47 | TmMinFactorPercent | 45 | 10..100 | lock tune:: | no |  |
| 48 | CaptureFutilityBase | 0 | 0..1000 | lock tune:: | yes |  |
| 49 | CaptureFutilityMultiplier | 250 | 0..1000 | lock tune:: | no |  |
| 50 | CaptureFutilityDepth | 6 | 0..15 | lock tune:: | no |  |
| 51 | FailLowContinuationBonus | 0 | 0..300 | lock tune:: | yes |  |
| 52 | NmpEvalDepthMargin | 24 | 0..100 | R9 (former literal) | yes |  |
| 53 | NmpEvalBase | 180 | -200..600 | R9 (former literal) | yes | yes (-100..500, 30) |
| 54 | NullMoveEvalMax | 3 | 0..10 | R9 (former literal) | yes |  |
| 55 | NullMoveVerifyDepth | 14 | 6..64 | R9 (former literal) | no |  |
| 56 | ProbcutImproving | 50 | 0..200 | R9 (former literal) | yes |  |
| 57 | ProbcutReduction | 4 | 2..8 | R9 (former literal) | yes |  |
| 58 | SingularTtDepth | 3 | 1..8 | R9 (former literal) | yes |  |
| 59 | SingularDoubleMargin | 24 | 0..200 | R9 (former literal) | yes | yes (0..80, 5) |
| 60 | SingularDoubleLimit | 6 | 0..20 | R9 (former literal) | no |  |
| 61 | LmrTtPv | 1024 | 0..4096 | R9 (former literal) | yes | yes (0..3072, 192) |
| 62 | LmrNotImproving | 1024 | 0..4096 | R9 (former literal) | yes | yes (0..3072, 192) |
| 63 | LmrCutNode | 2048 | 0..6144 | R9 (former literal) | yes | yes (0..4096, 256) |
| 64 | LmrTtCapture | 1024 | 0..4096 | R9 (former literal) | yes |  |
| 65 | LmrGivesCheck | 1024 | 0..4096 | R9 (former literal) | yes | yes (0..3072, 192) |
| 66 | LmrInCheck | 1024 | 0..4096 | R9 (former literal) | yes |  |
| 67 | LmrCutoffCount | 1024 | 0..4096 | R9 (former literal) | yes |  |
| 68 | HistoryBonusOffset | 32 | -200..300 | R9 (former literal) | yes |  |
| 69 | HistoryMalusPercent | 100 | 0..300 | R9 (former literal) | yes | yes (40..200, 10) |
| 70 | HistoryDepthBonusMargin | 100 | 0..1000 | R9 (former literal) | yes |  |
| 71 | AspirationMinDepth | 4 | 1..16 | R9 (former literal) | yes |  |
| 72 | AspirationGrowPercent | 50 | 10..300 | R9 (former literal) | yes |  |
| 73 | AspirationGrowAdd | 4 | 1..100 | R9 (former literal) | yes |  |
| 74 | QuietCheckBonus | 12000 | 0..40000 | R9 (former literal) | yes | yes (0..30000, 1500) |
