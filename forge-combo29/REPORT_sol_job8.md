# Sol — Job 8 history ageing and cold hard-budget sensitivity

## Step 0 and narrowed source check

**Step 0 met on both executables.** Each passed all eight fresh-process pins, defaults 312866 / 862329 / 3024920 / 4865609, S14 242796 / 656517 and PC20 278024 / 587276. The age copy additionally advertised `HistoryAgeKeep`, default 1024, range 0–1024. [Original raw output](sol/job8/step0-count.raw.txt) · [Age copy raw output](sol/job8/step0-age.raw.txt)

All three source statements met in the exact Job 4 counting source under the narrowed protocol.

1. The ordinary root path initializes search stack fields and clears killers. The continuation pointer assignment keeps the existing table. `src/search.cpp:2677,2893–2914`.
2. No intervening command in the fixed Threads 1, MultiPV 1 warm replay resets or scales a history table. Worker construction calls `clear()` at `src/search.cpp:1253`. `Searcher::clear()` calls it at 3289 from `ucinewgame`, the two pruning-policy setters and the separate bench searcher. The alternate MultiPV worker calls it at 3103. The unused Job 4 button calls it at 3273. The root setup and `position`/search loop do not issue those calls during a game. The exact call graph and verbatim source are linked below.
3. The gravity update clamps the bonus to `[-HistoryMax, HistoryMax]` with `HistoryMax=16384`, and preserves that interval from zero-initialized entries. `src/search.cpp:396,469–472`. [Verbatim Forge excerpts](sol/job8/forge-history-lines.txt)

## Step 1 tables

## Worker history tables

Unless otherwise qualified, read, update, and clear line numbers in this table
are in `src/search.cpp`. Member declarations are in
`include/forge/search.hpp:494–503,556–559`. The integer table aliases and
correction bound are in `include/forge/search.hpp:389–413` and
`include/forge/b4.hpp:20–22,103–108`.

| Member and stored value | Element type and bound | Updates | Reads | Emptied by `Worker::clear()` | Read by `quiet_history` under PC20 |
| --- | --- | --- | --- | --- | --- |
| `main_history_`, butterfly score by side/from/to | `std::int16_t`, ±16384 | Quiet cutoff bonus/malus 1718,1727. Quiet PV bonus 2563–2564. Optional TT cutoff history 2014 and eval swing 2055–2057. | Move picker 1013,1025 and `quiet_history` 1594–1604. Rework's blend also reads the plain entry at 1634. | Yes, 1260 | **Yes** |
| `threat_history_`, threat-indexed quiet score | `std::int16_t`, ±16384 | Threat-history update 1684–1687 from quiet cutoff 1719,1728 and PV bonus 2565. | Helper 1648–1651, used at 1025 and 1600. `ThreatHistory=false` at 306 returns before any table read. | Yes, 1261 | No |
| `capture_history_`, capture ordering score | `std::int16_t`, ±16384 | Capture bonus/malus 1738–1751 from beta cutoff 2560. | Capture picker 1127–1137, optional capture evasions 1207–1213, and 1690–1693 called by main for non-quiets at 2264. | Yes, 1266 | No |
| `continuation_history_`, prior move/current move score | `std::int16_t`, ±16384 | Gravity at 1696–1702 via quiet cutoff 1723,1732, optional TT cutoff 2015, LMR success 2507, and optional fail-low continuation 2575–2580. Updates include contexts 1, 2, and 4 plies back when available. | `quiet_history_sum` reads entries at 488–490 from 1594–1599, also used by move picker at 1014–1025. Search binds prior-move contexts at 1865,2121,2175,2441. | Yes, 1267 | **Yes**, contexts 1 and 2 under PC20. `ContHist4PlyRead=false` at 302 disables the optional fourth-ply read. |
| `rework_history_`, lesser-threat-keyed butterfly twin | `std::int16_t`, ±16384 | Gravity 1641–1644 via quiet cutoff 1735, and quiet PV bonus 2572. | 1624–1635, called by the move picker at 1029 and `quiet_history` at 1592. | Yes, 1274 | **Yes**, PC20 `HistRework=2` takes three quarters from this table and one quarter from the butterfly table, truncating the combined term toward zero. |
| `pawn_history_`, optional pawn-structure move score | `std::int16_t`, ±16384 when built | 1670–1675 via 1721,1730 and optional PV bonus 2566–2570. | 1656–1666 via 1026–1028 and 1601–1603. | When compiled and enabled, 1263–1265. Pointer is empty in this build, 1238–1242. | No, compiled out |
| `counter_moves_`, prior move to reply move | `Move`, no numeric score bound, empty is `Move{}` | Quiet cutoff learns reply at 1713–1715. | Move picker 815–819 and quiet extinction 2243–2245. | Yes, 1268 | No |
| `correction_history_`, pawn-structure evaluation correction | `std::int32_t`, ±8192 | 1472–1475. | 1439. | Yes, 1269 | No |
| `material_correction_`, material evaluation correction | `std::int32_t`, ±8192 | 1472–1474,1476 when weight is positive. | 1440–1441 when weight is positive. | Yes, 1270 | No |
| `non_pawn_white_correction_`, white non-pawn evaluation correction | `std::int32_t`, ±8192 | 1472–1474,1477–1478 with `NonPawnCorrection`. | 1443–1446. | Yes, 1271 | No |
| `non_pawn_black_correction_`, black non-pawn evaluation correction | `std::int32_t`, ±8192 | 1472–1474,1477,1479 with `NonPawnCorrection`. | 1443–1446. | Yes, 1272 | No |
| `joint_correction_`, pawn-structure × non-pawn-material correction | `std::int32_t`, ±8192 | B4 gravity 1483–1485 with `HistRework`. It clamps to ±8192 (`include/forge/b4.hpp:69–75`). | 1448–1451 with `HistRework`. | Yes, 1275 | No |
| `continuation_correction_`, corrections for prior moves | `std::int32_t`, ±8192 | 1472–1474,1487–1496 with `CorrHistV2`. | 1453–1463 with `CorrHistV2`. | Yes, 1276 | No |

All correction entries are updated under the main-search bound gate at
`src/search.cpp:2592–2598`, and read separately in `corrected_eval` from
quiescence, optional hindsight adjustment, and main search at 1817, 1989, and
2030. The corrected evaluation can influence pruning indirectly.

PC20 ageing therefore covers the entire butterfly, continuation, and
lesser-threat rework tables. This follows the live call at
`src/search.cpp:1590–1604`, the separate threat table's early return at
1648–1651, and the `HistRework=2` blend at 1633–1635 with
`include/forge/b4.hpp:24–28,62–67`. The three aged tables are distinct from the
correction tables. The quiet score is assigned at `src/search.cpp:2264`
and used by history pruning at 2332–2336 and LMR at 2475.

# Stockfish master history at a new search

Official Stockfish master was fetched with depth 1, a single branch and no tags. Commit `5d03b6e578a5eedc822e4563bdbb89e762fc2a59`. The UTC clock after the fetch and ref checks read `2026-11-18T03:52:46Z`.

Each active worker entering iterative deepening inside a game fills its low-ply table with 102 and multiplies each entry of its main (butterfly) table by 729/1024 before the first iteration. The C++ expression multiplies first and divides as integers, with truncation toward zero (`src/search.cpp:338–345`). If the main worker has no root moves, it returns before starting helpers or entering iterative deepening (`src/search.cpp:218–228`).

| History storage | Start of a new search inside a game | Initialization in `Worker::clear()` |
| --- | --- | --- |
| `mainHistory`, per worker | Scale every entry for both colors, `src/search.cpp:340–342` | Fill −5, `src/search.cpp:714` |
| `lowPlyHistory`, per worker | Fill 102, `src/search.cpp:338` | Fill occurs at iterative entry, `src/search.cpp:338,713–735` |
| `captureHistory`, per worker | Retain, `src/search.cpp:202–228,281–345` | Fill −742, `src/search.cpp:715` |
| `ttMoveHistory`, per-worker scalar | Retain, `src/search.cpp:202–228,281–345` | Set 0, `src/search.cpp:729` |
| `continuationHistory`, shared per NUMA node | Retain entries. New stack frames point to the existing sentinel, `src/search.cpp:300–312,338–345` | Fill −586 in all four sub-tables by the first worker on the NUMA node, `src/search.cpp:717–727` |
| `sharedHistory.pawnHistory`, shared per NUMA node | Retain, `src/search.cpp:202–228,281–345` | Fill each worker's share with −1338, `src/search.cpp:720` |
| `sharedHistory.correctionHistory`, shared per NUMA node, with pawn/minor/white-non-pawn/black-non-pawn fields | Retain, `src/search.cpp:202–228,281–345` | Fill each worker's share with −5, `src/search.cpp:719`; all four fields follow the assignment in `src/history.h:157–168` |
| `continuationCorrectionHistory`, per worker | Retain entries. New stack frames point to the existing sentinel, `src/search.cpp:300–312,338–345` | Fill 5, `src/search.cpp:731–733` |

Worker members are declared in `src/search.h:330–339`. The NUMA grouping and shared storage are in `src/history.h:197–215,249–251`. `position` rebuilds the board and move-state list (`src/uci.cpp:494–517`, `src/engine.cpp:195–214`). `go` starts thinking (`src/engine.cpp:153–158`). The root setup initializes per-search state (`src/thread.cpp:332–349`). `ucinewgame` takes the separate clear path through `Engine::search_clear()`, `ThreadPool::clear()` and `Thread::clear_worker()`.

[Forge inventory and caller map](sol/job8/forge-history.md) · [Pinned Stockfish inventory and excerpts](sol/job8/stockfish-history.md)

## Step 2 patch and Step 3 gates

The scratch history-age patch touches only the Job 4 copy's search translation unit. At the root it multiplies each entry of butterfly, continuation and lesser-threat rework history by the selected keep value and divides by 1024 in signed 32-bit arithmetic. C++ division truncates toward zero. At 1024 it skips all table work. The capture, counter-move, correction and TT paths stay as in the Job 4 copy. [Zero-fuzz age patch](sol/job8/history_age.patch.txt)

1. The age copy at default matched the three Job 6 baselines on 1,800/1,800 each, including raw CNT and the stable last-info fields. Warm soft recorded 6,753,665 actual nodes and 17,791 pruning takes. Warm hard recorded 36,000,000 nodes and 454,974 takes. Cold soft recorded 5,523,343 nodes and 349 takes. [Default identity](sol/job8/defaults-gate.txt)
2. The depth-12 Kimi5 bridge matched all expected counts and hashes.

   | Set | Positions | Total nodes | First three | Node hash prefix | Bestmove hash prefix |
   |---|---:|---:|---|---|---|
   | O | 200 | 8315168 | 21812 / 26844 / 35173 | fd609b7b1a8dd179 | 14583c86b5f56cb6 |
   | G | 353 | 17611204 | 31779 / 46086 / 84457 | 60b6916f01395e99 | 0846f027e7e9b77e |

   The named fixtures came from Kimi5 at `8f316b85a04bd4f2dedd6e15eefe8b3a18f1832f`. Both matched Job 2's fixtures byte for byte. [Fixture identity](sol/job8/bridge-fixtures.txt) · [Bridge gate](sol/job8/bridge-gate.txt)
3. Each nondefault keep/budget pair matched the default on all 30 opening rows. All 300 pairs matched in the opening-only gate before prediction and again in the full replay readback. [Opening gate](sol/job8/openings-gate.txt) · [Full-run gate](sol/job8/full-openings-gate.txt)
4. Cold soft at keep 512 and keep 0 each matched Job 6 cold soft on 1,800/1,800 rows.
5. Keep 0 warm soft produced 611 pruning takes in 6,224,814 nodes, 0.098156 per 1,000 nodes and 0.037261× default. It cleared the 0.2× gate. The opening-only and full keep-zero arms initially shared a status filename. The completed logs were preserved and the missing full warm arm ran after the names were separated. [Age controls](sol/job8/age-controls-gate.txt) · [Scheduler recovery](sol/job8/pre-recovery.txt)

The [prediction](sol/job8/prediction.txt) was pushed alone at `07ea8f431bc8498ad7422f205ab319beb8afa301` after the gates and before Step 4. Block D ran after Step 4 on the original, unchanged counting executable. Its cold-hard baseline matched Job 3 D on 1,800/1,800 rows, with 27,804 history-pruning takes in 36,000,000 actual nodes. The two QsSeeMargin controls each matched all 1,800 baseline rows. [Block D baseline gate](sol/job8/D-base-gate.txt) · [Block D controls](sol/job8/D-controls-gate.txt)

## Prediction grades

Each numeric forecast survives within a factor of 1.5. A zero guess requires observed zero.

| Keep | Budget | Quantity | Guess | Observed | Outcome |
|---:|---|---|---:|---:|---|
| 896 | soft | Pruning / default | 0.55 | 0.1373 | KILLED |
| 896 | soft | Changed vs default % | 34.00 | 39.0000 | survives |
| 896 | soft | Changed vs cold % | 46.00 | 47.7778 | survives |
| 896 | hard | Pruning / default | 0.78 | 0.1978 | KILLED |
| 896 | hard | Changed vs default % | 33.00 | 32.8333 | survives |
| 896 | hard | Changed vs cold % | 40.00 | 40.5556 | survives |
| 768 | soft | Pruning / default | 0.35 | 0.0536 | KILLED |
| 768 | soft | Changed vs default % | 38.00 | 38.5000 | survives |
| 768 | soft | Changed vs cold % | 45.00 | 48.2778 | survives |
| 768 | hard | Pruning / default | 0.62 | 0.0961 | KILLED |
| 768 | hard | Changed vs default % | 34.00 | 32.0556 | survives |
| 768 | hard | Changed vs cold % | 39.00 | 41.3333 | survives |
| 512 | soft | Pruning / default | 0.13 | 0.0314 | KILLED |
| 512 | soft | Changed vs default % | 40.00 | 40.8889 | survives |
| 512 | soft | Changed vs cold % | 44.00 | 48.6667 | survives |
| 512 | hard | Pruning / default | 0.41 | 0.0502 | KILLED |
| 512 | hard | Changed vs default % | 36.00 | 33.2778 | survives |
| 512 | hard | Changed vs cold % | 38.00 | 41.7778 | survives |
| 256 | soft | Pruning / default | 0.06 | 0.0354 | KILLED |
| 256 | soft | Changed vs default % | 40.00 | 40.7778 | survives |
| 256 | soft | Changed vs cold % | 43.00 | 46.2222 | survives |
| 256 | hard | Pruning / default | 0.23 | 0.0399 | KILLED |
| 256 | hard | Changed vs default % | 36.00 | 32.8889 | survives |
| 256 | hard | Changed vs cold % | 38.00 | 39.5556 | survives |

8 KILLED, 16 survive, 0 ungraded.

Below-2% cold-hard forecast: 8 hits.
Predicted below, measured at or above 2% (4): CaptureFutilityBase, LmrNoisyDivisor, NullMoveDepthDivisor, ProbcutMargin.
Measured below, not predicted (2): FutilityBase, FutilityMultiplier.
Predicted below but unmeasured (0): none.

## Table A. Warm replays by history retention and budget

Rates use actual main plus qsearch nodes. The largest ply group is by raw number of changed best moves against default. Counts are grouped by ply 0, 1–9, 10–29 and 30–59.

| Keep | Budget | Pruning / 1k | Pruning / default | Changed vs default | Changed vs cold | Soft actual nodes | Soft nodes/default | Soft median root depth | Changes by ply group | Largest non-opening group |
|---:|---|---:|---:|---|---|---:|---:|---:|---|---|
| 1024 | soft | 2.6343 | 1.0000 | 0/1800 (0.0000%) | 876/1800 (48.6667%) | 6753665 | 1.0000 | 8.0 | 0 / 0 / 0 / 0 | none |
| 1024 | hard | 12.6382 | 1.0000 | 0/1800 (0.0000%) | 738/1800 (41.0000%) | – | – | – | 0 / 0 / 0 / 0 | none |
| 896 | soft | 0.3616 | 0.1373 | 702/1800 (39.0000%) | 860/1800 (47.7778%) | 6396204 | 0.9471 | 8.0 | 0 / 105 / 232 / 365 | 30–59 |
| 896 | hard | 2.5001 | 0.1978 | 591/1800 (32.8333%) | 730/1800 (40.5556%) | – | – | – | 0 / 94 / 188 / 309 | 30–59 |
| 768 | soft | 0.1412 | 0.0536 | 693/1800 (38.5000%) | 869/1800 (48.2778%) | 6415074 | 0.9499 | 8.0 | 0 / 102 / 240 / 351 | 30–59 |
| 768 | hard | 1.2147 | 0.0961 | 577/1800 (32.0556%) | 744/1800 (41.3333%) | – | – | – | 0 / 96 / 193 / 288 | 30–59 |
| 512 | soft | 0.0828 | 0.0314 | 736/1800 (40.8889%) | 876/1800 (48.6667%) | 6412516 | 0.9495 | 8.0 | 0 / 110 / 254 / 372 | 30–59 |
| 512 | hard | 0.6345 | 0.0502 | 599/1800 (33.2778%) | 752/1800 (41.7778%) | – | – | – | 0 / 101 / 219 / 279 | 30–59 |
| 256 | soft | 0.0931 | 0.0354 | 734/1800 (40.7778%) | 832/1800 (46.2222%) | 6357004 | 0.9413 | 8.0 | 0 / 109 / 260 / 365 | 30–59 |
| 256 | hard | 0.5042 | 0.0399 | 592/1800 (32.8889%) | 712/1800 (39.5556%) | – | – | – | 0 / 102 / 194 / 296 | 30–59 |
| 0 | soft | 0.0982 | 0.0373 | 791/1800 (43.9444%) | 852/1800 (47.3333%) | 6224814 | 0.9217 | 8.0 | 0 / 127 / 264 / 400 | 30–59 |
| 0 | hard | 0.5590 | 0.0442 | 620/1800 (34.4444%) | 719/1800 (39.9444%) | – | – | – | 0 / 98 / 216 / 306 | 30–59 |

## Table D. Cold hard-budget tuning-step sensitivity, lowest first

Cold-soft percentages are recomputed from the exact changed/total counts in Job 6 Table 1. Cold-hard rates use actual main plus qsearch nodes.

| Setting | Cold hard changed | Job 6 cold soft changed | Cold hard nodes/base | Counter | Counter rate/base | Counter / 1k | Baseline counter / 1k |
|---|---|---|---:|---|---:|---:|---:|
| DrawJitter | 0/1800 (0.0000%) | 0/1800 (0.0000%) | 1.0000 | draw_jitter_taken | n/a (base zero) | 0.0002 | 0.0000 |
| NullMoveEvalDivisor | 0/3600 (0.0000%) | 0/3600 (0.0000%) | 1.0000 | null_move_taken | 1.0005 | 8.5002 | 8.4962 |
| HistoryPruneDepth | 0/3600 (0.0000%) | 0/3600 (0.0000%) | 1.0000 | history_pruning_taken | 0.9999 | 0.7722 | 0.7723 |
| FutilityDepth | 5/3600 (0.1389%) | 0/3600 (0.0000%) | 1.0000 | quiet_futility_taken | 0.9997 | 14.5350 | 14.5394 |
| RfpDepth | 17/3600 (0.4722%) | 0/3600 (0.0000%) | 1.0000 | rfp_taken | 0.9997 | 257.6532 | 257.7359 |
| FutilityBase | 40/3600 (1.1111%) | 7/3600 (0.1944%) | 1.0000 | quiet_futility_taken | 1.0010 | 14.5545 | 14.5394 |
| HistoryBonusMax | 46/3600 (1.2778%) | 1/3600 (0.0278%) | 1.0000 | history_pruning_taken | 0.9961 | 0.7693 | 0.7723 |
| FutilityMultiplier | 48/3600 (1.3333%) | 8/3600 (0.2222%) | 1.0000 | quiet_futility_taken | 1.0009 | 14.5528 | 14.5394 |
| LmrNoisyBase | 68/3600 (1.8889%) | 11/3600 (0.3056%) | 1.0000 | lmr_plies | 0.9995 | 756.9811 | 757.3908 |
| HistoryPruneMultiplier | 70/3600 (1.9444%) | 1/3600 (0.0278%) | 1.0000 | history_pruning_taken | 1.0175 | 0.7859 | 0.7723 |
| LmrNoisyDivisor | 137/3600 (3.8056%) | 29/3600 (0.8056%) | 1.0000 | lmr_plies | 0.9990 | 756.6047 | 757.3908 |
| RazorBase | 155/3600 (4.3056%) | 20/3600 (0.5556%) | 1.0000 | razor_taken | 1.0000 | 6.4197 | 6.4200 |
| ProbcutMargin | 190/3600 (5.2778%) | 16/3600 (0.4444%) | 1.0000 | probcut_taken | 0.9995 | 1.9443 | 1.9453 |
| CaptureFutilityBase | 101/1800 (5.6111%) | 6/1800 (0.3333%) | 1.0000 | capture_futility_taken | n/a (base zero) | 5.3876 | 0.0000 |
| RazorMultiplier | 207/3600 (5.7500%) | 31/3600 (0.8611%) | 1.0000 | razor_taken | 1.0077 | 6.4694 | 6.4200 |
| NullMoveDepthDivisor | 217/3600 (6.0278%) | 10/3600 (0.2778%) | 1.0000 | null_move_taken | 0.9958 | 8.4607 | 8.4962 |
| SeeNoisyMultiplier | 225/3600 (6.2500%) | 39/3600 (1.0833%) | 1.0000 | noisy_see_taken | 1.0142 | 103.7489 | 102.3004 |
| RazorDepth | 255/3600 (7.0833%) | 79/3600 (2.1944%) | 1.0000 | razor_taken | 0.9184 | 5.8964 | 6.4200 |
| NullMoveBase | 257/3600 (7.1389%) | 10/3600 (0.2778%) | 1.0000 | null_move_taken | 0.9893 | 8.4054 | 8.4962 |
| NullMoveMinDepth | 357/3600 (9.9167%) | 132/3600 (3.6667%) | 1.0000 | null_move_taken | 0.8779 | 7.4586 | 8.4962 |
| ProbcutDepth | 605/3600 (16.8056%) | 102/3600 (2.8333%) | 1.0000 | probcut_taken | 1.3356 | 2.5981 | 1.9453 |
| LmrHistoryDivisor | 615/3600 (17.0833%) | 45/3600 (1.2500%) | 1.0000 | lmr_plies | 0.9987 | 756.4047 | 757.3908 |
| SeeQuietMultiplier | 823/3600 (22.8611%) | 394/3600 (10.9444%) | 1.0000 | quiet_see_taken | 0.9786 | 145.9107 | 149.0960 |
| CheckExtensionDepth | 850/3600 (23.6111%) | 536/3600 (14.8889%) | 1.0000 | check_extension_taken | 1.2496 | 17.7912 | 14.2377 |
| HistoryBonusQuadratic | 883/3600 (24.5278%) | 209/3600 (5.8056%) | 1.0000 | history_pruning_taken | 0.9699 | 0.7491 | 0.7723 |
| MaterialCorrectionWeight | 900/3600 (25.0000%) | 363/3600 (10.0833%) | 1.0000 | none | n/a | n/a | n/a |
| HistoryBonusLinear | 955/3600 (26.5278%) | 394/3600 (10.9444%) | 1.0000 | history_pruning_taken | 0.9580 | 0.7399 | 0.7723 |
| QsFutilityMargin | 1018/3600 (28.2778%) | 529/3600 (14.6944%) | 1.0000 | q_futility_taken | 1.0018 | 95.7581 | 95.5865 |
| FailLowContinuationBonus | 538/1800 (29.8889%) | 295/1800 (16.3889%) | 1.0000 | fail_low_bonus_taken | n/a (base zero) | 47.7656 | 0.0000 |
| SingularMargin | 1099/3600 (30.5278%) | 314/3600 (8.7222%) | 1.0000 | singular_taken | 0.9936 | 3.3519 | 3.3735 |
| LmrQuietBase | 1184/3600 (32.8889%) | 925/3600 (25.6944%) | 1.0000 | lmr_plies | 0.9956 | 754.0468 | 757.3908 |
| LmrQuietDivisor | 1212/3600 (33.6667%) | 993/3600 (27.5833%) | 1.0000 | lmr_plies | 0.9933 | 752.3233 | 757.3908 |
| LmrCutoffThreshold | 1238/3600 (34.3889%) | 963/3600 (26.7500%) | 1.0000 | lmr_plies | 1.0029 | 759.6027 | 757.3908 |
| LmpBase | 1280/3600 (35.5556%) | 1267/3600 (35.1944%) | 1.0000 | lmp_taken | 0.9861 | 64.2089 | 65.1161 |
| AspirationDelta | 1280/3600 (35.5556%) | 1057/3600 (29.3611%) | 1.0000 | aspiration_taken | 0.9964 | 0.3056 | 0.3067 |
| RfpMargin | 1307/3600 (36.3056%) | 1305/3600 (36.2500%) | 1.0000 | rfp_taken | 1.0003 | 257.8171 | 257.7359 |
| RfpImproving | 1320/3600 (36.6667%) | 1346/3600 (37.3889%) | 1.0000 | rfp_taken | 0.9977 | 257.1444 | 257.7359 |
| SingularDepth | 1321/3600 (36.6944%) | 978/3600 (27.1667%) | 1.0000 | singular_taken | 1.1049 | 3.7274 | 3.3735 |
| EvalSwingMult | 664/1800 (36.8889%) | 859/1800 (47.7222%) | 1.0000 | eval_swing_taken | n/a (base zero) | 365.1396 | 0.0000 |
| IirDepth | 1456/3600 (40.4444%) | 1581/3600 (43.9167%) | 1.0000 | iir_no_tt_taken | 1.3532 | 59.9850 | 44.3281 |

Below 2% cold hard (10): DrawJitter, NullMoveEvalDivisor, HistoryPruneDepth, FutilityDepth, RfpDepth, FutilityBase, HistoryBonusMax, FutilityMultiplier, LmrNoisyBase, HistoryPruneMultiplier.

## Facts

- Even keep 896 reduced history-pruning takes per node to 0.1373× default at the soft budget and 0.1978× at the hard budget. The lowest measured soft rate was 0.0828 per thousand at keep 512. The lowest hard rate was 0.5042 at keep 256. The rates rose slightly at lower keeps. All age arms used the recorded copy and 1,800 fixed positions each.
- Keep 0 still differed from the cold baseline on 852/1,800 soft recommendations and 719/1,800 hard recommendations. The default differed on 876/1,800 and 738/1,800. Relative to default, keep 0 changed 791/1,800 soft and 620/1,800 hard bestmoves. All soft ages had reported root depth median 8. The largest changed-move count for each nondefault age came from plies 30–59, the bin with the most replay opportunities.
- Ten settings were below 2% changed bestmoves at cold hard, all within the 19 below 2% at cold soft. The largest cold-hard change rates were IirDepth `1456/3600` (40.4444%), EvalSwingMult `664/1800` (36.8889%) and SingularDepth `1321/3600` (36.6944%). LmrHistoryDivisor rose from 45/3,600 at cold soft to 615/3,600 at cold hard.
- DrawJitter, NullMoveEvalDivisor and HistoryPruneDepth changed zero bestmoves in cold hard. Their raw CNT rows differed from base in 5, 552 and 47 comparisons respectively. Their last-info node counts differed in 0, 227 and 13 comparisons. The zeroes therefore describe the bestmove recommendation. Table D reports the measured event rates next to the move counts. All 76 tuned cold-hard arms and both controls completed. [Read counts and actual nodes](sol/job8/read-counts.txt)

## Build and protocol

- Case A, Codex Cloud Linux x86_64, GPT-6 (Codex). Both builds were PC r15 on Forge base `6b98f2170a3210e71beed04bbd2553972c253ed7` with the Job 2 counter and Job 4 buttons patches. Unchanged executable SHA-256 `63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333`. Age copy SHA-256 `559961f449b5e742f60984a43b7b1c672c2512b4ec1e6af2b5e4b6d4ecc60fd9`, applied age patch SHA-256 `a0f3d81f4dc471655e2f70fda7a6dd4b532211df97d7d1994f051b87e62b83ac`. GCC 14.2.0, CMake 4.2.3 Release, libstdc++ `6.0.33`, glibc 2.41, `x86-64-v4`, `FORGE_MATE_ALPHA_GUARD=1`. [Job 4 build record](REPORT_sol_job4.md)
- Both used PC20, Threads 1, Hash 16 MiB, one PV, OwnBook false, built-in AL1 s198 evaluation, weights source SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`, no external network file. Variants sent a single explicit override after PC20 and recorded their responses in the sidecar. The history-age copy supplied all age rows. The original binary supplied Block D. [PC20 recipe](REPORT_sol_job2.md) · [Age raw rows](sol/job8/age-raw) · [Cold hard rows](sol/job8/raw)
- First 30 Job 3 games, 1,800 positions per arm, full game list SHA-256 `6d3343843f1bd6e9597f1e54ea64779fab78a1df64abb2431c749151e5a060a1`. Warm reset once per game. Cold reset before each search. The hard budget was `go nodes 20000`, the soft budget was `go softnodes 2000`. Replay always used the original FEN and preceding recorded moves. [Recorded games](sol/job3/games.txt) · [UTC stamps](sol/job8/stamps.txt)

From `forge-combo29/sol/job8`, the readbacks and tables can be reproduced with:

```sh
for gate in baselines bridge openings full-openings age-controls D-base D-controls; do
  python3 verify_gates.py "$gate"
done
python3 summarize.py ../job3/games.txt age-raw raw --settings settings.tsv --job6-raw ../job6/raw --job6-summary ../../REPORT_sol_job6.md --job3-raw ../job3/raw --prediction prediction.txt
```

## Suspicions

The quiet-history reset can sharply suppress pruning while leaving substantial divergence from a cold replay. The hash and other worker entries are still warm, and each search can relearn history within its node budget. This run keeps those remaining effects together.

## What I did not do

No owner-PC run, active standalone v3 net, tune change, timing comparison, competitive match or Elo measurement. The engine changes are confined to the scratch copy and the unified text patch.

## What I am not sure about

The live PC net or self-play data could produce different sensitivity rankings. The fixed replay supplies no direction of a strength effect and the per-ply counts do not isolate the propensity within each bin.

## Pre-commit readback

```text
M  forge-combo29/NOTES_sol.md
AM forge-combo29/REPORT_sol_job8.md
A  forge-combo29/sol/job8/D-base-gate.txt
A  forge-combo29/sol/job8/D-controls-gate.txt
A  forge-combo29/sol/job8/age-controls-gate.txt
A  forge-combo29/sol/job8/age-raw/keep-0-cold-soft.jsonl
A  forge-combo29/sol/job8/age-raw/keep-0-cold-soft.jsonl.meta
A  forge-combo29/sol/job8/age-raw/keep-0-warm-hard.jsonl
A  forge-combo29/sol/job8/age-raw/keep-0-warm-hard.jsonl.meta
A  forge-combo29/sol/job8/age-raw/keep-0-warm-soft.jsonl
A  forge-combo29/sol/job8/age-raw/keep-0-warm-soft.jsonl.meta
A  forge-combo29/sol/job8/age-raw/keep-1024-cold-soft.jsonl
A  forge-combo29/sol/job8/age-raw/keep-1024-cold-soft.jsonl.meta
A  forge-combo29/sol/job8/age-raw/keep-1024-warm-hard.jsonl
A  forge-combo29/sol/job8/age-raw/keep-1024-warm-hard.jsonl.meta
A  forge-combo29/sol/job8/age-raw/keep-1024-warm-soft.jsonl
A  forge-combo29/sol/job8/age-raw/keep-1024-warm-soft.jsonl.meta
A  forge-combo29/sol/job8/age-raw/keep-256-warm-hard.jsonl
A  forge-combo29/sol/job8/age-raw/keep-256-warm-hard.jsonl.meta
A  forge-combo29/sol/job8/age-raw/keep-256-warm-soft.jsonl
A  forge-combo29/sol/job8/age-raw/keep-256-warm-soft.jsonl.meta
A  forge-combo29/sol/job8/age-raw/keep-512-cold-soft.jsonl
A  forge-combo29/sol/job8/age-raw/keep-512-cold-soft.jsonl.meta
A  forge-combo29/sol/job8/age-raw/keep-512-warm-hard.jsonl
A  forge-combo29/sol/job8/age-raw/keep-512-warm-hard.jsonl.meta
A  forge-combo29/sol/job8/age-raw/keep-512-warm-soft.jsonl
A  forge-combo29/sol/job8/age-raw/keep-512-warm-soft.jsonl.meta
A  forge-combo29/sol/job8/age-raw/keep-768-warm-hard.jsonl
A  forge-combo29/sol/job8/age-raw/keep-768-warm-hard.jsonl.meta
A  forge-combo29/sol/job8/age-raw/keep-768-warm-soft.jsonl
A  forge-combo29/sol/job8/age-raw/keep-768-warm-soft.jsonl.meta
A  forge-combo29/sol/job8/age-raw/keep-896-warm-hard.jsonl
A  forge-combo29/sol/job8/age-raw/keep-896-warm-hard.jsonl.meta
A  forge-combo29/sol/job8/age-raw/keep-896-warm-soft.jsonl
A  forge-combo29/sol/job8/age-raw/keep-896-warm-soft.jsonl.meta
A  forge-combo29/sol/job8/block-A-run.txt
A  forge-combo29/sol/job8/block-D-run.txt
A  forge-combo29/sol/job8/bridge-fixtures.txt
A  forge-combo29/sol/job8/bridge-gate.txt
A  forge-combo29/sol/job8/bridge-raw/bridge-G.jsonl
A  forge-combo29/sol/job8/bridge-raw/bridge-G.jsonl.meta
A  forge-combo29/sol/job8/bridge-raw/bridge-O.jsonl
A  forge-combo29/sol/job8/bridge-raw/bridge-O.jsonl.meta
A  forge-combo29/sol/job8/defaults-gate.txt
A  forge-combo29/sol/job8/forge-history-lines.txt
A  forge-combo29/sol/job8/forge-history.md
A  forge-combo29/sol/job8/full-openings-gate.txt
A  forge-combo29/sol/job8/history_age.patch.txt
A  forge-combo29/sol/job8/opening-raw/keep-0-warm-hard.jsonl
A  forge-combo29/sol/job8/opening-raw/keep-0-warm-hard.jsonl.meta
A  forge-combo29/sol/job8/opening-raw/keep-0-warm-soft.jsonl
A  forge-combo29/sol/job8/opening-raw/keep-0-warm-soft.jsonl.meta
A  forge-combo29/sol/job8/opening-raw/keep-1024-warm-hard.jsonl
A  forge-combo29/sol/job8/opening-raw/keep-1024-warm-hard.jsonl.meta
A  forge-combo29/sol/job8/opening-raw/keep-1024-warm-soft.jsonl
A  forge-combo29/sol/job8/opening-raw/keep-1024-warm-soft.jsonl.meta
A  forge-combo29/sol/job8/opening-raw/keep-256-warm-hard.jsonl
A  forge-combo29/sol/job8/opening-raw/keep-256-warm-hard.jsonl.meta
A  forge-combo29/sol/job8/opening-raw/keep-256-warm-soft.jsonl
A  forge-combo29/sol/job8/opening-raw/keep-256-warm-soft.jsonl.meta
A  forge-combo29/sol/job8/opening-raw/keep-512-warm-hard.jsonl
A  forge-combo29/sol/job8/opening-raw/keep-512-warm-hard.jsonl.meta
A  forge-combo29/sol/job8/opening-raw/keep-512-warm-soft.jsonl
A  forge-combo29/sol/job8/opening-raw/keep-512-warm-soft.jsonl.meta
A  forge-combo29/sol/job8/opening-raw/keep-768-warm-hard.jsonl
A  forge-combo29/sol/job8/opening-raw/keep-768-warm-hard.jsonl.meta
A  forge-combo29/sol/job8/opening-raw/keep-768-warm-soft.jsonl
A  forge-combo29/sol/job8/opening-raw/keep-768-warm-soft.jsonl.meta
A  forge-combo29/sol/job8/opening-raw/keep-896-warm-hard.jsonl
A  forge-combo29/sol/job8/opening-raw/keep-896-warm-hard.jsonl.meta
A  forge-combo29/sol/job8/opening-raw/keep-896-warm-soft.jsonl
A  forge-combo29/sol/job8/opening-raw/keep-896-warm-soft.jsonl.meta
A  forge-combo29/sol/job8/openings-gate.txt
A  forge-combo29/sol/job8/pre-recovery.txt
A  forge-combo29/sol/job8/pre-run.txt
A  forge-combo29/sol/job8/raw/AspirationDelta-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/AspirationDelta-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/AspirationDelta-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/AspirationDelta-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/CaptureFutilityBase-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/CaptureFutilityBase-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/CheckExtensionDepth-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/CheckExtensionDepth-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/CheckExtensionDepth-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/CheckExtensionDepth-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/DrawJitter-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/DrawJitter-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/EvalSwingMult-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/EvalSwingMult-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/FailLowContinuationBonus-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/FailLowContinuationBonus-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/FutilityBase-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/FutilityBase-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/FutilityBase-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/FutilityBase-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/FutilityDepth-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/FutilityDepth-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/FutilityDepth-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/FutilityDepth-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/FutilityMultiplier-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/FutilityMultiplier-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/FutilityMultiplier-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/FutilityMultiplier-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/HistoryBonusLinear-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/HistoryBonusLinear-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/HistoryBonusLinear-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/HistoryBonusLinear-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/HistoryBonusMax-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/HistoryBonusMax-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/HistoryBonusMax-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/HistoryBonusMax-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/HistoryBonusQuadratic-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/HistoryBonusQuadratic-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/HistoryBonusQuadratic-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/HistoryBonusQuadratic-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/HistoryPruneDepth-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/HistoryPruneDepth-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/HistoryPruneDepth-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/HistoryPruneDepth-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/HistoryPruneMultiplier-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/HistoryPruneMultiplier-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/HistoryPruneMultiplier-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/HistoryPruneMultiplier-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/IirDepth-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/IirDepth-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/IirDepth-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/IirDepth-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/LmpBase-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/LmpBase-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/LmpBase-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/LmpBase-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/LmrCutoffThreshold-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/LmrCutoffThreshold-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/LmrCutoffThreshold-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/LmrCutoffThreshold-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/LmrHistoryDivisor-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/LmrHistoryDivisor-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/LmrHistoryDivisor-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/LmrHistoryDivisor-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/LmrNoisyBase-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/LmrNoisyBase-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/LmrNoisyBase-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/LmrNoisyBase-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/LmrNoisyDivisor-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/LmrNoisyDivisor-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/LmrNoisyDivisor-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/LmrNoisyDivisor-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/LmrQuietBase-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/LmrQuietBase-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/LmrQuietBase-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/LmrQuietBase-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/LmrQuietDivisor-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/LmrQuietDivisor-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/LmrQuietDivisor-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/LmrQuietDivisor-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/MaterialCorrectionWeight-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/MaterialCorrectionWeight-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/MaterialCorrectionWeight-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/MaterialCorrectionWeight-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/NullMoveBase-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/NullMoveBase-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/NullMoveBase-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/NullMoveBase-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/NullMoveDepthDivisor-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/NullMoveDepthDivisor-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/NullMoveDepthDivisor-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/NullMoveDepthDivisor-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/NullMoveEvalDivisor-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/NullMoveEvalDivisor-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/NullMoveEvalDivisor-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/NullMoveEvalDivisor-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/NullMoveMinDepth-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/NullMoveMinDepth-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/NullMoveMinDepth-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/NullMoveMinDepth-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/ProbcutDepth-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/ProbcutDepth-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/ProbcutDepth-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/ProbcutDepth-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/ProbcutMargin-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/ProbcutMargin-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/ProbcutMargin-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/ProbcutMargin-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/QsFutilityMargin-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/QsFutilityMargin-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/QsFutilityMargin-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/QsFutilityMargin-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/QsSeeMargin-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/QsSeeMargin-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/QsSeeMargin-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/QsSeeMargin-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/RazorBase-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/RazorBase-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/RazorBase-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/RazorBase-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/RazorDepth-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/RazorDepth-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/RazorDepth-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/RazorDepth-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/RazorMultiplier-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/RazorMultiplier-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/RazorMultiplier-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/RazorMultiplier-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/RfpDepth-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/RfpDepth-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/RfpDepth-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/RfpDepth-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/RfpImproving-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/RfpImproving-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/RfpImproving-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/RfpImproving-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/RfpMargin-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/RfpMargin-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/RfpMargin-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/RfpMargin-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/SeeNoisyMultiplier-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/SeeNoisyMultiplier-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/SeeNoisyMultiplier-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/SeeNoisyMultiplier-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/SeeQuietMultiplier-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/SeeQuietMultiplier-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/SeeQuietMultiplier-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/SeeQuietMultiplier-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/SingularDepth-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/SingularDepth-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/SingularDepth-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/SingularDepth-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/SingularMargin-minus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/SingularMargin-minus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/SingularMargin-plus-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/SingularMargin-plus-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/raw/base-cold-hard.jsonl
A  forge-combo29/sol/job8/raw/base-cold-hard.jsonl.meta
A  forge-combo29/sol/job8/read-counts.txt
A  forge-combo29/sol/job8/run_age.py
A  forge-combo29/sol/job8/run_blocks.py
A  forge-combo29/sol/job8/settings.tsv
A  forge-combo29/sol/job8/stamps.txt
A  forge-combo29/sol/job8/step0-age.raw.txt
A  forge-combo29/sol/job8/step0-age.summary.txt
A  forge-combo29/sol/job8/step0-count.raw.txt
A  forge-combo29/sol/job8/step0.summary.txt
A  forge-combo29/sol/job8/stockfish-history.md
A  forge-combo29/sol/job8/summarize.py
A  forge-combo29/sol/job8/verify_gates.py
?? forge-combo29/sol/job2/__pycache__/
forge-combo29/sol/job8:
D-base-gate.txt
D-controls-gate.txt
age-controls-gate.txt
age-raw
block-A-run.txt
block-D-run.txt
bridge-fixtures.txt
bridge-gate.txt
bridge-raw
defaults-gate.txt
forge-history-lines.txt
forge-history.md
full-openings-gate.txt
history_age.patch.txt
opening-raw
openings-gate.txt
pre-recovery.txt
pre-run.txt
prediction.txt
raw
read-counts.txt
run_age.py
run_blocks.py
settings.tsv
stamps.txt
step0-age.raw.txt
step0-age.summary.txt
step0-count.raw.txt
step0.summary.txt
stockfish-history.md
summarize.py
verify_gates.py

forge-combo29/sol/job8/age-raw:
keep-0-cold-soft.jsonl
keep-0-cold-soft.jsonl.meta
keep-0-warm-hard.jsonl
keep-0-warm-hard.jsonl.meta
keep-0-warm-soft.jsonl
keep-0-warm-soft.jsonl.meta
keep-1024-cold-soft.jsonl
keep-1024-cold-soft.jsonl.meta
keep-1024-warm-hard.jsonl
keep-1024-warm-hard.jsonl.meta
keep-1024-warm-soft.jsonl
keep-1024-warm-soft.jsonl.meta
keep-256-warm-hard.jsonl
keep-256-warm-hard.jsonl.meta
keep-256-warm-soft.jsonl
keep-256-warm-soft.jsonl.meta
keep-512-cold-soft.jsonl
keep-512-cold-soft.jsonl.meta
keep-512-warm-hard.jsonl
keep-512-warm-hard.jsonl.meta
keep-512-warm-soft.jsonl
keep-512-warm-soft.jsonl.meta
keep-768-warm-hard.jsonl
keep-768-warm-hard.jsonl.meta
keep-768-warm-soft.jsonl
keep-768-warm-soft.jsonl.meta
keep-896-warm-hard.jsonl
keep-896-warm-hard.jsonl.meta
keep-896-warm-soft.jsonl
keep-896-warm-soft.jsonl.meta

forge-combo29/sol/job8/bridge-raw:
bridge-G.jsonl
bridge-G.jsonl.meta
bridge-O.jsonl
bridge-O.jsonl.meta

forge-combo29/sol/job8/opening-raw:
keep-0-warm-hard.jsonl
keep-0-warm-hard.jsonl.meta
keep-0-warm-soft.jsonl
keep-0-warm-soft.jsonl.meta
keep-1024-warm-hard.jsonl
keep-1024-warm-hard.jsonl.meta
keep-1024-warm-soft.jsonl
keep-1024-warm-soft.jsonl.meta
keep-256-warm-hard.jsonl
keep-256-warm-hard.jsonl.meta
keep-256-warm-soft.jsonl
keep-256-warm-soft.jsonl.meta
keep-512-warm-hard.jsonl
keep-512-warm-hard.jsonl.meta
keep-512-warm-soft.jsonl
keep-512-warm-soft.jsonl.meta
keep-768-warm-hard.jsonl
keep-768-warm-hard.jsonl.meta
keep-768-warm-soft.jsonl
keep-768-warm-soft.jsonl.meta
keep-896-warm-hard.jsonl
keep-896-warm-hard.jsonl.meta
keep-896-warm-soft.jsonl
keep-896-warm-soft.jsonl.meta

forge-combo29/sol/job8/raw:
AspirationDelta-minus-cold-hard.jsonl
AspirationDelta-minus-cold-hard.jsonl.meta
AspirationDelta-plus-cold-hard.jsonl
AspirationDelta-plus-cold-hard.jsonl.meta
CaptureFutilityBase-plus-cold-hard.jsonl
CaptureFutilityBase-plus-cold-hard.jsonl.meta
CheckExtensionDepth-minus-cold-hard.jsonl
CheckExtensionDepth-minus-cold-hard.jsonl.meta
CheckExtensionDepth-plus-cold-hard.jsonl
CheckExtensionDepth-plus-cold-hard.jsonl.meta
DrawJitter-plus-cold-hard.jsonl
DrawJitter-plus-cold-hard.jsonl.meta
EvalSwingMult-plus-cold-hard.jsonl
EvalSwingMult-plus-cold-hard.jsonl.meta
FailLowContinuationBonus-plus-cold-hard.jsonl
FailLowContinuationBonus-plus-cold-hard.jsonl.meta
FutilityBase-minus-cold-hard.jsonl
FutilityBase-minus-cold-hard.jsonl.meta
FutilityBase-plus-cold-hard.jsonl
FutilityBase-plus-cold-hard.jsonl.meta
FutilityDepth-minus-cold-hard.jsonl
FutilityDepth-minus-cold-hard.jsonl.meta
FutilityDepth-plus-cold-hard.jsonl
FutilityDepth-plus-cold-hard.jsonl.meta
FutilityMultiplier-minus-cold-hard.jsonl
FutilityMultiplier-minus-cold-hard.jsonl.meta
FutilityMultiplier-plus-cold-hard.jsonl
FutilityMultiplier-plus-cold-hard.jsonl.meta
HistoryBonusLinear-minus-cold-hard.jsonl
HistoryBonusLinear-minus-cold-hard.jsonl.meta
HistoryBonusLinear-plus-cold-hard.jsonl
HistoryBonusLinear-plus-cold-hard.jsonl.meta
HistoryBonusMax-minus-cold-hard.jsonl
HistoryBonusMax-minus-cold-hard.jsonl.meta
HistoryBonusMax-plus-cold-hard.jsonl
HistoryBonusMax-plus-cold-hard.jsonl.meta
HistoryBonusQuadratic-minus-cold-hard.jsonl
HistoryBonusQuadratic-minus-cold-hard.jsonl.meta
HistoryBonusQuadratic-plus-cold-hard.jsonl
HistoryBonusQuadratic-plus-cold-hard.jsonl.meta
HistoryPruneDepth-minus-cold-hard.jsonl
HistoryPruneDepth-minus-cold-hard.jsonl.meta
HistoryPruneDepth-plus-cold-hard.jsonl
HistoryPruneDepth-plus-cold-hard.jsonl.meta
HistoryPruneMultiplier-minus-cold-hard.jsonl
HistoryPruneMultiplier-minus-cold-hard.jsonl.meta
HistoryPruneMultiplier-plus-cold-hard.jsonl
HistoryPruneMultiplier-plus-cold-hard.jsonl.meta
IirDepth-minus-cold-hard.jsonl
IirDepth-minus-cold-hard.jsonl.meta
IirDepth-plus-cold-hard.jsonl
IirDepth-plus-cold-hard.jsonl.meta
LmpBase-minus-cold-hard.jsonl
LmpBase-minus-cold-hard.jsonl.meta
LmpBase-plus-cold-hard.jsonl
LmpBase-plus-cold-hard.jsonl.meta
LmrCutoffThreshold-minus-cold-hard.jsonl
LmrCutoffThreshold-minus-cold-hard.jsonl.meta
LmrCutoffThreshold-plus-cold-hard.jsonl
LmrCutoffThreshold-plus-cold-hard.jsonl.meta
LmrHistoryDivisor-minus-cold-hard.jsonl
LmrHistoryDivisor-minus-cold-hard.jsonl.meta
LmrHistoryDivisor-plus-cold-hard.jsonl
LmrHistoryDivisor-plus-cold-hard.jsonl.meta
LmrNoisyBase-minus-cold-hard.jsonl
LmrNoisyBase-minus-cold-hard.jsonl.meta
LmrNoisyBase-plus-cold-hard.jsonl
LmrNoisyBase-plus-cold-hard.jsonl.meta
LmrNoisyDivisor-minus-cold-hard.jsonl
LmrNoisyDivisor-minus-cold-hard.jsonl.meta
LmrNoisyDivisor-plus-cold-hard.jsonl
LmrNoisyDivisor-plus-cold-hard.jsonl.meta
LmrQuietBase-minus-cold-hard.jsonl
LmrQuietBase-minus-cold-hard.jsonl.meta
LmrQuietBase-plus-cold-hard.jsonl
LmrQuietBase-plus-cold-hard.jsonl.meta
LmrQuietDivisor-minus-cold-hard.jsonl
LmrQuietDivisor-minus-cold-hard.jsonl.meta
LmrQuietDivisor-plus-cold-hard.jsonl
LmrQuietDivisor-plus-cold-hard.jsonl.meta
MaterialCorrectionWeight-minus-cold-hard.jsonl
MaterialCorrectionWeight-minus-cold-hard.jsonl.meta
MaterialCorrectionWeight-plus-cold-hard.jsonl
MaterialCorrectionWeight-plus-cold-hard.jsonl.meta
NullMoveBase-minus-cold-hard.jsonl
NullMoveBase-minus-cold-hard.jsonl.meta
NullMoveBase-plus-cold-hard.jsonl
NullMoveBase-plus-cold-hard.jsonl.meta
NullMoveDepthDivisor-minus-cold-hard.jsonl
NullMoveDepthDivisor-minus-cold-hard.jsonl.meta
NullMoveDepthDivisor-plus-cold-hard.jsonl
NullMoveDepthDivisor-plus-cold-hard.jsonl.meta
NullMoveEvalDivisor-minus-cold-hard.jsonl
NullMoveEvalDivisor-minus-cold-hard.jsonl.meta
NullMoveEvalDivisor-plus-cold-hard.jsonl
NullMoveEvalDivisor-plus-cold-hard.jsonl.meta
NullMoveMinDepth-minus-cold-hard.jsonl
NullMoveMinDepth-minus-cold-hard.jsonl.meta
NullMoveMinDepth-plus-cold-hard.jsonl
NullMoveMinDepth-plus-cold-hard.jsonl.meta
ProbcutDepth-minus-cold-hard.jsonl
ProbcutDepth-minus-cold-hard.jsonl.meta
ProbcutDepth-plus-cold-hard.jsonl
ProbcutDepth-plus-cold-hard.jsonl.meta
ProbcutMargin-minus-cold-hard.jsonl
ProbcutMargin-minus-cold-hard.jsonl.meta
ProbcutMargin-plus-cold-hard.jsonl
ProbcutMargin-plus-cold-hard.jsonl.meta
QsFutilityMargin-minus-cold-hard.jsonl
QsFutilityMargin-minus-cold-hard.jsonl.meta
QsFutilityMargin-plus-cold-hard.jsonl
QsFutilityMargin-plus-cold-hard.jsonl.meta
QsSeeMargin-minus-cold-hard.jsonl
QsSeeMargin-minus-cold-hard.jsonl.meta
QsSeeMargin-plus-cold-hard.jsonl
QsSeeMargin-plus-cold-hard.jsonl.meta
RazorBase-minus-cold-hard.jsonl
RazorBase-minus-cold-hard.jsonl.meta
RazorBase-plus-cold-hard.jsonl
RazorBase-plus-cold-hard.jsonl.meta
RazorDepth-minus-cold-hard.jsonl
RazorDepth-minus-cold-hard.jsonl.meta
RazorDepth-plus-cold-hard.jsonl
RazorDepth-plus-cold-hard.jsonl.meta
RazorMultiplier-minus-cold-hard.jsonl
RazorMultiplier-minus-cold-hard.jsonl.meta
RazorMultiplier-plus-cold-hard.jsonl
RazorMultiplier-plus-cold-hard.jsonl.meta
RfpDepth-minus-cold-hard.jsonl
RfpDepth-minus-cold-hard.jsonl.meta
RfpDepth-plus-cold-hard.jsonl
RfpDepth-plus-cold-hard.jsonl.meta
RfpImproving-minus-cold-hard.jsonl
RfpImproving-minus-cold-hard.jsonl.meta
RfpImproving-plus-cold-hard.jsonl
RfpImproving-plus-cold-hard.jsonl.meta
RfpMargin-minus-cold-hard.jsonl
RfpMargin-minus-cold-hard.jsonl.meta
RfpMargin-plus-cold-hard.jsonl
RfpMargin-plus-cold-hard.jsonl.meta
SeeNoisyMultiplier-minus-cold-hard.jsonl
SeeNoisyMultiplier-minus-cold-hard.jsonl.meta
SeeNoisyMultiplier-plus-cold-hard.jsonl
SeeNoisyMultiplier-plus-cold-hard.jsonl.meta
SeeQuietMultiplier-minus-cold-hard.jsonl
SeeQuietMultiplier-minus-cold-hard.jsonl.meta
SeeQuietMultiplier-plus-cold-hard.jsonl
SeeQuietMultiplier-plus-cold-hard.jsonl.meta
SingularDepth-minus-cold-hard.jsonl
SingularDepth-minus-cold-hard.jsonl.meta
SingularDepth-plus-cold-hard.jsonl
SingularDepth-plus-cold-hard.jsonl.meta
SingularMargin-minus-cold-hard.jsonl
SingularMargin-minus-cold-hard.jsonl.meta
SingularMargin-plus-cold-hard.jsonl
SingularMargin-plus-cold-hard.jsonl.meta
base-cold-hard.jsonl
base-cold-hard.jsonl.meta
```
