# sol3 — Job 14 null search settings on O and G

**Step 0 passed.** Both retained Job 13 executable hashes matched. kF and the counted kF gave the same fresh default pins (bench 11 312866, bench 13 862329, startpos perft 5 4865609) and PC20 embedded pins (bench 11 278024, bench 13 587276). [Hash gate](sol3/job14/stage0/input_hashes.txt) · [kF raw pins](sol3/job14/stage0/kF/pins.txt) · [Counted kF raw pins](sol3/job14/stage0/counted/pins.txt)

### Independent floor and K1–K3

I froze `NullChildFloor` before opening any Astra5 floor-patch source. It advertises a spin range of 0–3 with default 0. The new code clamps the null child's depth only for a positive floor and leaves the verification on the original reduced depth. NC0 uses the child depth actually searched. A clean `patch -p1 -F0` reproduced the scratch edit. [Patch](sol3/job14/null_floor.patch.txt) · [UCI definition](sol3/job14/floor/option_gate.txt) · [Build](sol3/job14/floor/build.txt)

O and G came from kimi5 commit `5db05e095d5e81622eb0de13eb8a738a0ae1d22a`, in order. I used the prior reference runner's four-field EPD position and default `0 1` clocks for O. All 200 O rows differ from their authored clock fields. G's 353 authored rows already end in `0 1`. Both authored inputs passed their SHA-256 checks. Every suite run used PC20, Threads 1, Hash 16 MiB, MultiPV 1, a new-game/ready reset per position and `go depth 12`. The standalone net768 used in N2 is synthetic and untrained. [Fixture provenance and convention](sol3/job14/references/source.txt) · [Pinned inputs](sol3/job14/references/fixture_hash_gate.txt) · [Reference readback](sol3/job14/references/reference_proof.txt)

- K1 matched all 200 O rows and all 353 G rows, including all five NC0 values. The G rows carried the same 17611204 nodes and NC0 totals as Job 13 C1. [O gate](sol3/job14/K1/O/known_gate.json) · [G gate](sol3/job14/K1/G/known_gate.json)
- K2 floor 1 matched Astra5's nodes and bestmove on all 200 O rows and all 353 G rows. The full K1 and K2 first-three and total rows appear in the results table. [O gate](sol3/job14/K2/O/known_gate.json) · [G gate](sol3/job14/K2/G/known_gate.json)
- K3 matched every one of Astra5's 20 P rungs for both variants. Base4 first found `g3g6 mate 2` at depth 16 with 196077 nodes and used 196956 at depth 20. Floor1 found it at depth 10 with 13182 nodes and used 14993 at depth 20. [Base4 ladder](sol3/job14/K3/Base4/rows.tsv) · [Floor1 ladder](sol3/job14/K3/Floor1/rows.tsv)
- The synthetic G Base5 baseline also matched every search label and all five NC0 fields from Job 13 C2 across 353 positions. Each N2 run logged the active net768 line and checksum `30ab43b4ba5db5f3`. [Job 13 C2 gate](sol3/job14/N2/G/Base5/job13_C2_gate.txt) · [Synthetic G setup and raw output](sol3/job14/N2/G/Base5/engine.stdout.txt)

### Prediction grade

4 of 12 completed forecasts landed inside all three ranges. Across metrics, 23 of 36 observed values landed inside their ranges. [Frozen prediction](sol3/job14/prediction.txt)

- Embedded O Base4 had other move changes 37 outside [6, 33]. [Readback](sol3/job14/N1/O/Base4/summary.json)
- Embedded G Base4 had node ratio 0.97077 outside [0.98, 1.1]. [Readback](sol3/job14/N1/G/Base4/summary.json)
- Synthetic net768 G Base4 had flagged move changes 100 outside [11, 65], other move changes 56 outside [7, 46]. [Readback](sol3/job14/N2/G/Base4/summary.json)
- Synthetic net768 G Base3 had flagged move changes 102 outside [19, 89], other move changes 77 outside [11, 63]. [Readback](sol3/job14/N2/G/Base3/summary.json)
- Synthetic net768 G Floor1 had flagged move changes 100 outside [16, 82], other move changes 71 outside [10, 61]. [Readback](sol3/job14/N2/G/Floor1/summary.json)
- Synthetic net768 O Base4 had flagged move changes 75 outside [2, 39], other move changes 54 outside [2, 35]. [Readback](sol3/job14/N2/O/Base4/summary.json)
- Synthetic net768 O Base3 had flagged move changes 81 outside [5, 52]. [Readback](sol3/job14/N2/O/Base3/summary.json)
- Synthetic net768 O Floor1 had flagged move changes 81 outside [3, 48], other move changes 46 outside [3, 44]. [Readback](sol3/job14/N2/O/Floor1/summary.json)

### Results

Ratios use the same evaluation and set at Base5. The split uses the Base5 position flags. Every completed row links to the readback from its full raw log. [Comparator](sol3/job14/summarize_arm.py)

| Setting | Evaluation | Set | Node sum | Ratio | First three | NC0 sums [0]–[4] | [4] positions | Changed moves flagged / others |
| --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| [Base5](sol3/job14/K1/O/summary.json) | Embedded | O | 8,315,168 | 1.00000 | 21,812, 26,844, 35,173 | 123578 / 113502 / 86995 / 85212 / 5 | 4 | 0/4 · 0/196 |
| [Base4](sol3/job14/N1/O/Base4/summary.json) | Embedded | O | 8,448,399 | 1.01602 | 14,877, 25,981, 42,802 | 125179 / 102366 / 87997 / 80965 / 3 | 3 | 1/4 · 37/196 |
| [Base3](sol3/job14/N1/O/Base3/summary.json) | Embedded | O | 8,705,140 | 1.04690 | 20,369, 23,497, 31,494 | 124778 / 57713 / 86526 / 47738 / 1 | 1 | 0/4 · 43/196 |
| [Floor1](sol3/job14/K2/O/summary.json) | Embedded | O | 8,768,825 | 1.05456 | 13,712, 30,033, 28,584 | 126542 / 0 / 87422 / 0 / 0 | 0 | 0/4 · 46/196 |
| [Base5](sol3/job14/K1/G/summary.json) | Embedded | G | 17,611,204 | 1.00000 | 31,779, 46,086, 84,457 | 357628 / 325285 / 244577 / 233592 / 513 | 81 | 0/81 · 0/272 |
| [Base4](sol3/job14/N1/G/Base4/summary.json) | Embedded | G | 17,096,422 | 0.97077 | 33,706, 38,382, 77,557 | 342769 / 276769 / 236065 / 206517 / 400 | 79 | 22/81 · 48/272 |
| [Base3](sol3/job14/N1/G/Base3/summary.json) | Embedded | G | 18,137,422 | 1.02988 | 30,662, 62,601, 64,398 | 341297 / 165826 / 231582 / 126400 / 280 | 73 | 16/81 · 57/272 |
| [Floor1](sol3/job14/K2/G/summary.json) | Embedded | G | 18,559,820 | 1.05386 | 41,983, 65,584, 80,217 | 351588 / 0 / 231554 / 0 / 0 | 0 | 23/81 · 51/272 |
| [Base5](sol3/job14/N2/O/Base5/summary.json) | Synthetic net768 | O | 32,504,791 | 1.00000 | 37,409, 213,822, 139,142 | 426716 / 402179 / 179259 / 174906 / 539 | 118 | 0/118 · 0/82 |
| [Base4](sol3/job14/N2/O/Base4/summary.json) | Synthetic net768 | O | 31,430,920 | 0.96696 | 33,012, 228,863, 102,557 | 410437 / 351324 / 167593 / 153968 / 489 | 124 | 75/118 · 54/82 |
| [Base3](sol3/job14/N2/O/Base3/summary.json) | Synthetic net768 | O | 33,380,771 | 1.02695 | 51,414, 196,649, 130,961 | 417803 / 251200 / 161262 / 112345 / 395 | 111 | 81/118 · 44/82 |
| [Floor1](sol3/job14/N2/O/Floor1/summary.json) | Synthetic net768 | O | 34,040,029 | 1.04723 | 86,584, 157,434, 76,633 | 428324 / 0 / 143296 / 0 / 0 | 0 | 81/118 · 46/82 |
| [Base5](sol3/job14/N2/G/Base5/summary.json) | Synthetic net768 | G | 42,620,225 | 1.00000 | 95,007, 39,469, 131,900 | 525990 / 495511 / 264362 / 256034 / 1453 | 189 | 0/189 · 0/164 |
| [Base4](sol3/job14/N2/G/Base4/summary.json) | Synthetic net768 | G | 43,950,793 | 1.03122 | 77,952, 59,985, 185,787 | 542901 / 462041 / 265496 / 238970 / 1369 | 188 | 100/189 · 56/164 |
| [Base3](sol3/job14/N2/G/Base3/summary.json) | Synthetic net768 | G | 45,461,893 | 1.06667 | 78,112, 78,811, 105,225 | 550870 / 324192 / 252657 / 167574 / 959 | 194 | 102/189 · 77/164 |
| [Floor1](sol3/job14/N2/G/Floor1/summary.json) | Synthetic net768 | G | 46,488,516 | 1.09076 | 126,251, 51,808, 121,540 | 551565 / 0 / 220950 / 0 / 0 | 0 | 100/189 · 71/164 |

### Answer

Floor1 removed the measured shallow-cutoff class in all 4 completed evaluation/suite pairs. It made each actual null child at least depth 1 and still made null cutoffs. Base4 and Base3 each retained measured [4] events in all four pairs. [Floor depth calculation](sol3/job14/null_floor.patch.txt)

- Embedded node changes from Base5 were G Base4 -2.92%, Base3 +2.99%, Floor1 +5.39% and O Base4 +1.60%, Base3 +4.69%, Floor1 +5.46%. [G Base4](sol3/job14/N1/G/Base4/summary.json) · [G Base3](sol3/job14/N1/G/Base3/summary.json) · [G Floor1](sol3/job14/K2/G/summary.json) · [O Base4](sol3/job14/N1/O/Base4/summary.json) · [O Base3](sol3/job14/N1/O/Base3/summary.json) · [O Floor1](sol3/job14/K2/O/summary.json)
- Synthetic net768 node changes from Base5 were G Base4 +3.12%, Base3 +6.67%, Floor1 +9.08% and O Base4 -3.30%, Base3 +2.69%, Floor1 +4.72%. [G Base4](sol3/job14/N2/G/Base4/summary.json) · [G Base3](sol3/job14/N2/G/Base3/summary.json) · [G Floor1](sol3/job14/N2/G/Floor1/summary.json) · [O Base4](sol3/job14/N2/O/Base4/summary.json) · [O Base3](sol3/job14/N2/O/Base3/summary.json) · [O Floor1](sol3/job14/N2/O/Floor1/summary.json)

On G, the move-change rate was higher among the Base5-flagged positions in 5 of 6 setting/evaluation comparisons. The exception was embedded Base3 (19.8% vs 21.0%). [Base5 flag and move counts](sol3/job14/incidence.json)

On O, the move-change rate was higher among the Base5-flagged positions in 3 of 6 setting/evaluation comparisons. The exceptions were embedded Base3 (0.0% vs 21.9%), embedded Floor1 (0.0% vs 23.5%), synthetic net768 Base4 (63.6% vs 65.9%). [Base5 flag and move counts](sol3/job14/incidence.json)

Synthetic G Base3 reduced the total [4] events and increased the number of distinct positions with an event. The incidence readback separately counts events on originally flagged positions and on positions first flagged by the alternative. [Baseline-relative incidence](sol3/job14/incidence.json)

## Facts

- The independent floor executable SHA-256 is `86f5a663466e8787b28dd8a10f1a8184d4f28b86741abd21a7c4fc9989ed8dbf`. It was built with GCC 14.2.0, Debian libstdc++ from GCC 14.2.0-19 and the same CMake Release flags as the counted kF. [Build output](sol3/job14/floor/build.txt)
- The prediction commit `7d9bdb96b35e5638aa3b0eec48ca9e45f6119e4d` contains only the forecast. Both evaluators completed all their O and G arms, including the optional synthetic O runs. [Prediction](sol3/job14/prediction.txt) · [Order and exits](sol3/job14/stamps.txt)

## Suspicions

Base4 and Base3 change the child depth only by one or two plies at a fixed node and can change future pruning, so their aggregate node totals need not move in the same direction as the local depth. The larger synthetic move-change counts also suggest that the root choice is sensitive to the evaluator in this test.

## What I did not do

I ran no strength match or wall-clock comparison. The floor build and clean patch applications stayed in scratch.

## What I am not sure about

Embedded O has only four baseline-flagged positions, so one changed move moves that group's observed rate by 25 percentage points. The reference clock normalization removes the authored O halfmove and move-number fields, which could matter to the exact result. This NC0 probe classifies child depths of zero or less. It gives no count of quiet mates in depth-one null children. [O clock provenance](sol3/job14/references/source.txt) · [Counter readback](sol3/job14/incidence.json)

## Limits of this check

The PC's own net and exe, other depths, games, time. A node count or a changed move is not strength. [Evidence stamps](sol3/job14/stamps.txt)

<details>
<summary>Literal diff and patch application output</summary>

```diff
diff -ruN base/src/search.cpp tree/src/search.cpp
--- base/src/search.cpp	2026-11-18 05:55:01.807977026 -0800
+++ tree/src/search.cpp	2026-11-18 06:13:21.653026605 -0800
@@ -102,6 +102,7 @@
 int LmrNoisyDivisor = 340;
 int NullMoveMinDepth = 3;
 int NullMoveBase = 3;
+int NullChildFloor = 0;
 int NullMoveDepthDivisor = 3;
 int NullMoveEvalDivisor = 200;
 int RfpDepth = 8;
@@ -189,6 +190,7 @@
         {"LmrQuietBase", &LmrQuietBase, 0, 300},         {"LmrQuietDivisor", &LmrQuietDivisor, 100, 500},
         {"LmrNoisyBase", &LmrNoisyBase, 0, 300},         {"LmrNoisyDivisor", &LmrNoisyDivisor, 100, 800},
         {"NullMoveMinDepth", &NullMoveMinDepth, 1, 10},  {"NullMoveBase", &NullMoveBase, 1, 6},
+        {"NullChildFloor", &NullChildFloor, 0, 3},
         {"NullMoveDepthDivisor", &NullMoveDepthDivisor, 1, 10},
         {"NullMoveEvalDivisor", &NullMoveEvalDivisor, 50, 1000},
         {"RfpDepth", &RfpDepth, 0, 15},                  {"RfpMargin", &RfpMargin, 10, 300},
@@ -2613,7 +2615,9 @@
             !(tune::NullSeeVeto && null_see_veto_threat(board))) {
             const int reduction = tune::NullMoveBase + depth / tune::NullMoveDepthDivisor +
                                   std::min((eval - beta) / tune::NullMoveEvalDivisor, 3);
-            const int child_depth = depth - reduction;
+            const int reduced_depth = depth - reduction;
+            const int child_depth = tune::NullChildFloor > 0
+                ? std::max(reduced_depth, tune::NullChildFloor) : reduced_depth;
             ss->current_move = Move::none();
             ss->moved_piece = Empty;
             ss->continuation = &(*continuation_history_)[Empty][0];
@@ -2647,7 +2651,7 @@
                 const bool saved_block = null_blocked_;
                 if (threat_gate) null_blocked_ = true;
                 ss->null_move_allowed = false;
-                const int verification = search_child(board, ss, child_depth, beta - 1, beta, false);
+                const int verification = search_child(board, ss, reduced_depth, beta - 1, beta, false);
                 null_blocked_ = saved_block;
                 ss->double_extensions = inherited_double_extensions;
                 ss->null_move_allowed = true;
```

```text
patching file src/search.cpp
```

</details>
