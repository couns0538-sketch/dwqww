# S15 exact-L parameter account — 2026-10-27

Source search.cpp SHA256 `44680416e008f4ccc0ac7d95a1452ae3db34459f945ea3311dc456536fcb0e55`. All51 integer declarations match exactly one named pointer/range entry. Bounds/defaults below are parsed from this Forge source, not invented tuning ranges.

|Parameter|Default|Minimum|Maximum|
|---|---:|---:|---:|
|LmrQuietBase|85|0|300|
|LmrQuietDivisor|220|100|500|
|LmrNoisyBase|10|0|300|
|LmrNoisyDivisor|340|100|800|
|NullMoveMinDepth|3|1|10|
|NullMoveBase|3|1|6|
|NullMoveDepthDivisor|3|1|10|
|NullMoveEvalDivisor|200|50|1000|
|RfpDepth|8|0|15|
|RfpMargin|72|10|300|
|RfpImproving|40|0|200|
|RazorDepth|2|0|6|
|RazorBase|150|0|1000|
|RazorMultiplier|350|0|1000|
|FutilityDepth|7|0|15|
|FutilityBase|100|0|500|
|FutilityMultiplier|110|0|500|
|LmpBase|4|0|20|
|HistoryPruneDepth|3|0|10|
|HistoryPruneMultiplier|2048|0|20000|
|SeeQuietMultiplier|24|0|200|
|SeeNoisyMultiplier|150|0|1000|
|SingularDepth|7|2|20|
|SingularMargin|2|0|10|
|IirDepth|4|1|20|
|ProbcutDepth|5|1|20|
|ProbcutMargin|180|0|1000|
|QsFutilityMargin|160|0|1000|
|QsSeeMargin|40|0|500|
|AspirationDelta|18|4|200|
|HistoryBonusQuadratic|20|0|100|
|HistoryBonusLinear|48|0|500|
|HistoryBonusMax|2048|100|10000|
|LmrHistoryDivisor|6000|1000|30000|
|CheckExtensionDepth|2|1|30|
|LmrCutoffThreshold|3|0|20|
|MaterialCorrectionWeight|100|0|300|
|TmSoftDivisor|22|5|80|
|TmIncrementPercent|75|0|150|
|TmHardPercent|60|10|95|
|TmHardSoftMultiple|5|1|20|
|TmStableFactor|60|20|150|
|TmSemiStableFactor|80|20|150|
|TmUnstableFactor|140|50|300|
|TmEffortBase|155|100|250|
|TmFallingEvalPercent|100|0|400|
|TmMinFactorPercent|45|10|100|
|CaptureFutilityBase|0|0|1000|
|CaptureFutilityMultiplier|250|0|1000|
|CaptureFutilityDepth|6|0|15|
|FailLowContinuationBonus|0|0|300|

NetScale is requested by S15 but absent from exact L. It has no source-defined default/range here and is explicitly unsupported. NetScalePct in separate idea/status records is not silently treated as an alias or applied patch. All51 existing tune:: parameters remain usable independently.

L accepts table names from setoption, parses integers with from_chars, clamps to table bounds, and refreshes derived tuning tables. Its CMake FORGE_EXPOSE_TUNABLES option is OFF by default and affects advertisement only. The tool requires a captured, complete, duplicate-free exposed UCI profile matching selected source bounds. It does not prove that the supplied profile belongs to the supplied executable; that execution binding remains a deferred real-smoke gate.
