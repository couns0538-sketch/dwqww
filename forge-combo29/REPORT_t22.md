# Task t22 Report: Search Inventory and Candidates (WIP)

## Baseline Verification

Branch `carbon/t22-search-candidates` created from `origin/integrate/combo29-fixes` (`bf5574ee654a773f0ef3d06878707056b90cdad7`).

Initial baseline check (`Threads 1`, `Hash 16`, `OwnBook false`):
- `bench 11`: 312866 nodes
- `bench 13`: 862329 nodes
- `bench 16`: 3024920 nodes
- `go perft 5` (startpos): 4865609 nodes

## 1. Search Inventory Table

| Technique | Status | Locations (`src/search.cpp`, `include/forge/search.hpp`) | Tuning Options (`forge::tune`) |
|---|---|---|---|
| Aspiration windows | present | `src/search.cpp:48, 90, 1659-1682`; `include/forge/search.hpp:245` | `AspirationDelta` |
| Principal-variation search (PVS) | present | `src/search.cpp:1121, 1411, 1423, 1426, 1435, 1437-1439` | (none) |
| Null-move pruning and verification | present | `src/search.cpp:25-28, 77-80, 1213-1251`; `include/forge/search.hpp:220-223, 299, 378-379` | `NullMoveMinDepth`, `NullMoveBase`, `NullMoveDepthDivisor`, `NullMoveEvalDivisor` |
| Reverse futility pruning (RFP) | present | `src/search.cpp:29-31, 81-82, 1208-1212`; `include/forge/search.hpp:224-226` | `RfpDepth`, `RfpMargin`, `RfpImproving` |
| Futility pruning (quiet moves) | present | `src/search.cpp:35-37, 84-85, 1329-1334`; `include/forge/search.hpp:230-232` | `FutilityDepth`, `FutilityBase`, `FutilityMultiplier` |
| Futility pruning (captures) | partly (code present, default off) | `src/search.cpp:69-71, 106-107, 1340-1345`; `include/forge/search.hpp:264-266` | `CaptureFutilityBase`, `CaptureFutilityMultiplier`, `CaptureFutilityDepth` |
| Razoring | present | `src/search.cpp:32-34, 82-83, 1202-1207`; `include/forge/search.hpp:227-229` | `RazorDepth`, `RazorBase`, `RazorMultiplier` |
| Late-move reductions (LMR) and adjustments | partly (present with `tt_pv`, `improving`, `cut_node`, `tt_capture`, `gives_check`, `in_check`, child `cutoff_count`, quiet `history`; no capture-history adjustment, no deeper/shallower post-LMR adjustment) | `src/search.cpp:21-24, 52, 54, 75-76, 97, 99, 133-155, 1412-1433`; `include/forge/search.hpp:216-219, 249, 251` | `LmrQuietBase`, `LmrQuietDivisor`, `LmrNoisyBase`, `LmrNoisyDivisor`, `LmrHistoryDivisor`, `LmrCutoffThreshold` |
| Late-move pruning (LMP) | present | `src/search.cpp:38, 86, 157-159, 1327`; `include/forge/search.hpp:233` | `LmpBase` |
| History pruning (quiet moves) | present | `src/search.cpp:39-40, 86-87, 1335`; `include/forge/search.hpp:234-235` | `HistoryPruneDepth`, `HistoryPruneMultiplier` |
| Static-exchange pruning of captures | present | `src/search.cpp:42, 47, 89, 93, 1069, 1346-1348`; `include/forge/search.hpp:237, 244` | `SeeNoisyMultiplier` (main search), `QsSeeMargin` (qsearch) |
| Static-exchange pruning of quiet moves | present | `src/search.cpp:41, 88, 1336`; `include/forge/search.hpp:236` | `SeeQuietMultiplier` |
| Main history (butterfly) | present | `src/search.cpp:49-51, 94-96, 161-168, 179-187, 614-633, 921-935, 965, 970, 1477-1479`; `include/forge/search.hpp:246-248, 274, 343` | `HistoryBonusQuadratic`, `HistoryBonusLinear`, `HistoryBonusMax` |
| Capture history | present | `src/search.cpp:680-693, 937-941, 975-989, 1323`; `include/forge/search.hpp:277, 344` | `HistoryBonusQuadratic`, `HistoryBonusLinear`, `HistoryBonusMax` |
| Continuation history (plies) | partly (updated at 1, 2, 4 plies back; queried only at 1 and 2 plies back; 6-ply absent; fail-low parent bonus default off) | `src/search.cpp:72, 107, 179-187, 614-633, 921-935, 943-950, 966, 971, 1431, 1480-1485`; `include/forge/search.hpp:267, 275-276, 300, 345` | `HistoryBonusQuadratic`, `HistoryBonusLinear`, `HistoryBonusMax`, `FailLowContinuationBonus` |
| Countermove table | present | `src/search.cpp:440-443, 485-489, 960-962`; `include/forge/search.hpp:278, 346` | (none) |
| Pawn history (quiet move ordering indexed by pawn hash) | absent | — | (none) |
| Correction history | partly (pawn-key and material-key present; non-pawn, minor/major, and continuation correction histories absent) | `src/search.cpp:55, 100, 802-810, 852-870, 1036, 1186, 1496-1502`; `include/forge/search.hpp:252, 279-282, 347-348` | `MaterialCorrectionWeight` |
| Singular extensions (single, double, negative, multi-cut) | present | `src/search.cpp:43-44, 90, 1354-1376, 1381`; `include/forge/search.hpp:238-239, 289, 296` | `SingularDepth`, `SingularMargin` |
| ProbCut | present | `src/search.cpp:46-47, 91-92, 1252-1286`; `include/forge/search.hpp:241-242` | `ProbcutDepth`, `ProbcutMargin` |
| Internal iterative reductions (IIR) | present | `src/search.cpp:45, 91, 1290`; `include/forge/search.hpp:240` | `IirDepth` |
| Hash-table cutoffs in quiescence | present | `src/search.cpp:1009-1025, 1037-1049, 1108-1114` | (none) |
| Mate-distance pruning | present | `src/search.cpp:130-131, 1140-1143` | (none) |
| Check extensions | present | `src/search.cpp:53, 98, 1377-1380`; `include/forge/search.hpp:250` | `CheckExtensionDepth` |
| Checks in quiescence | partly (evasions when already in check are generated; quiet checking moves when not in check are absent) | `src/search.cpp:435-437, 514-538, 1029-1031, 1056-1062, 1106` | (none) |
| Delta / futility pruning in quiescence | present | `src/search.cpp:48, 92, 1052, 1064-1068`; `include/forge/search.hpp:243` | `QsFutilityMargin` |
| Hash-table ageing and replacement | present | `src/search.cpp:270-406, 1794`; `include/forge/search.hpp:75-102, 127-132` | (none; `Hash` UCI option sizes table) |
| Time management (best-move stability, node share, score swings) | present | `src/search.cpp:56-68, 101-105, 1530-1556, 1708-1740`; `include/forge/search.hpp:254-263, 350-352, 361-363` | `TmSoftDivisor`, `TmIncrementPercent`, `TmHardPercent`, `TmHardSoftMultiple`, `TmStableFactor`, `TmSemiStableFactor`, `TmUnstableFactor`, `TmEffortBase`, `TmFallingEvalPercent`, `TmMinFactorPercent` |
