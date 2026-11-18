# astra5 job 4 — testing the null-move cause of the missed mate

## Step 0 — all 12 known answers matched

Each command used a fresh process. The tests used the Job 1 PC executable (SHA-256 `9279d02c2ea8c42875ec83a55399aeb588b72a3ae13e8067969be2cee8219306`) and PCA (`49b56941b2acc0c2b9272c4e14992f2561c9ef71dbaf3da74a8a684ae8bc416a`). [Raw inputs and outputs](astra5/job4/step0)

| Build | Settings | Bench 11 | Bench 13 | Perft 5 |
|---|---|---:|---:|---:|
| PC | No setoption | 312,866 | 862,329 | 4,865,609 |
| PC | S14 | 242,796 | 656,517 | — |
| PC | PC20 | 278,024 | 587,276 | — |
| PCA | No setoption | 312,866 | 862,329 | 4,865,609 |
| PCA | PC20 | 278,024 | 587,276 | — |

## Part A — changing only the null move recovered the mate

P is `2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1`. Each arm used PC20, Threads 1, Hash 16 and the built-in evaluation. Each requested depth from 1 through 20 started with `ucinewgame`, followed by `isready` and `readyok`. The first winning move in each row was `g3g6`, scored mate 2. [Ladders and raw transcripts](astra5/job4/A)

| Arm | Single change after PC20 | First mate depth | Nodes there |
|---|---|---:|---:|
| A1, plain PC | NullMoveBase 3 | 15 | 220,500 |
| A2, plain PC | NullMoveBase 4 | 16 | 196,077 |
| A3, PC with floor patch | NullChildFloor 1 | 10 | 13,182 |

With NullChildFloor 0, all 20 P rows matched Job 3’s ordinary PC20 ladder, including `f6h5`, cp 916 and 1,052,250 nodes at depth 20. All depth-12 rows matched Job 1’s PCA reference in FEN order, node count and best move. O had 200 rows, 8,315,168 nodes and first counts 21,812 / 26,844 / 35,173. G had 353 rows, 17,611,204 nodes and first counts 31,779 / 46,086 / 84,457. [Verification](astra5/job4/A/checks.txt)

The `NullChildFloor` spin option has default 0 and range 0–3. A positive value changes only the depth passed to the null child. Zero preserves the original depth, including negative values. The verification search still uses its original depth. [Build identity and UCI listing](astra5/job4/build-floor)

<details><summary>Output of diff -ruN and patch -p1 -F0 on a fresh PC tree</summary>

```diff
diff -ruN pc/include/forge/search.hpp floor-design/include/forge/search.hpp
--- pc/include/forge/search.hpp	2026-11-15 05:25:59.000000000 +0000
+++ floor-design/include/forge/search.hpp	2026-11-15 05:25:59.000000000 +0000
@@ -250,6 +250,7 @@
 extern int LmrNoisyDivisor;   // x0.01
 extern int NullMoveMinDepth;
 extern int NullMoveBase;
+extern int NullChildFloor;
 extern int NullMoveDepthDivisor;
 extern int NullMoveEvalDivisor;
 extern int RfpDepth;
diff -ruN pc/src/search.cpp floor-design/src/search.cpp
--- pc/src/search.cpp	2026-11-15 05:25:59.000000000 +0000
+++ floor-design/src/search.cpp	2026-11-15 05:25:59.000000000 +0000
@@ -101,6 +101,7 @@
 int LmrNoisyDivisor = 340;
 int NullMoveMinDepth = 3;
 int NullMoveBase = 3;
+int NullChildFloor = 0;
 int NullMoveDepthDivisor = 3;
 int NullMoveEvalDivisor = 200;
 int RfpDepth = 8;
@@ -188,6 +189,7 @@
         {"LmrQuietBase", &LmrQuietBase, 0, 300},         {"LmrQuietDivisor", &LmrQuietDivisor, 100, 500},
         {"LmrNoisyBase", &LmrNoisyBase, 0, 300},         {"LmrNoisyDivisor", &LmrNoisyDivisor, 100, 800},
         {"NullMoveMinDepth", &NullMoveMinDepth, 1, 10},  {"NullMoveBase", &NullMoveBase, 1, 6},
+        {"NullChildFloor", &NullChildFloor, 0, 3},
         {"NullMoveDepthDivisor", &NullMoveDepthDivisor, 1, 10},
         {"NullMoveEvalDivisor", &NullMoveEvalDivisor, 50, 1000},
         {"RfpDepth", &RfpDepth, 0, 15},                  {"RfpMargin", &RfpMargin, 10, 300},
@@ -1960,7 +1962,10 @@
 #if FORGE_SEARCH_SPEED2
             shared_.tt.prefetch(board.key());
 #endif
-            int null_score = -search_child(board, ss + 1, depth - reduction, -beta, -beta + 1, !cut_node);
+            const int reduced_depth = depth - reduction;
+            const int null_child_depth = tune::NullChildFloor > 0 ? std::max(reduced_depth, tune::NullChildFloor)
+                                                                  : reduced_depth;
+            int null_score = -search_child(board, ss + 1, null_child_depth, -beta, -beta + 1, !cut_node);
             board.unmake_null_move(undo);
             if (aborted_) return 0;
             if (null_score >= beta) {
```

```text
patching file include/forge/search.hpp
patching file src/search.cpp
```

</details>

## Prediction — all three ranges held, all three exact depths missed

Commit `669b8b0` contained `prediction.txt` alone and preceded A1. Base 3 was predicted at depth 13 [9, 17] and measured at 15. Base 4 was predicted at 15 [11, 19] and measured at 16. Floor 1 was predicted at 15 [10, 18] and measured at 10, exactly the lower bound. [Frozen prediction](astra5/job4/prediction.txt)

## Part B — HistRework isolates the difference on P

PC build on P, depth 1 through 20. Each result was reconstructed from raw UCI traffic.

| Arm | Settings | First mate depth | Score | Nodes there | D20 move / score / nodes |
| --- | --- | --- | --- | --- | --- |
| S14 | S14 | 16 | mate 2 | 240516 | g3g6 / mate 2 / 241,262 |
| PC20 | PC20 | not by 20 | — | — | f6h5 / cp 916 / 1,052,250 |
| B1 | PC20 + HistRework 0 | 13 | mate 2 | 75864 | g3g6 / mate 2 / 77,195 |
| B2 | PC20 + CorrHistV2 false | not by 20 | — | — | f6h5 / cp 865 / 930,407 |
| B3 | S14 + CuckooRep true | 15 | mate 2 | 138407 | g3g6 / mate 2 / 141,265 |
| B4 | S14 + HistRework 2 | not by 20 | — | — | f6h5 / cp 836 / 774,832 |
| B5 | S14 + TtPruneV2 true | 16 | mate 2 | 333499 | g3g6 / mate 2 / 334,278 |
| B6 | S14 + CorrHistV2 true | 15 | mate 2 | 135969 | g3g6 / mate 2 / 137,079 |
| B7 | S14 + MateAlphaGuard true | 16 | mate 2 | 240516 | g3g6 / mate 2 / 241,262 |

Both unchanged ladders matched job 3 on all 20 depths.

Of the five PC20 additions tested individually on S14, only `HistRework 2` suppressed the mate through depth 20. The complementary change in the full PC20 profile, `HistRework 0`, restored it at depth 13. `CorrHistV2 false` left PC20 missing the mate. This addresses the two settings omitted from Job 3’s one-switch tests. HistRework affects both quiet-move history and evaluation correction in the PC source (`src/search.cpp:1306–1315,1449–1450,1480–1493`). These comparisons isolate the option as a whole. They do not separate its components. [Part B raw evidence](astra5/job4/B)

## Part C — quiet mates at actual null cutoffs

The counter runs after an accepted immediate or verified null cutoff. It reconstructs the null-child position on a board copy, tries legal non-capturing, non-promoting checks and counts the cutoff once if any is checkmate. Hypothetical probes leave the search’s board and node counter untouched. Each `bestmove` was followed by one `NC0` line. With floor 0, all 200 O and 353 G search rows matched Part A. On P at depth 16 the observer reproduced the move `f6h5` and the count of 182,707 nodes, and slot [4] was 52, passing the required positive control. All 353 G floor-1 rows also matched Part D. [Text patch](astra5/job4/null_count.patch.txt) · [Counter totals and qualifying positions](astra5/job4/C/summary.txt)

For the instruction that [5]–[7] repeat [2]–[4] for child depth 1–2, I used [5] as the same all-cutoffs denominator as [2], [6] as its depth-1/2 subset and [7] as qualifying quiet mates within [6]. A separate per-position field preserves the number of depth-1/2 probes started, so starts and cutoffs can also be compared directly. The depth classifications use the actual depth after applying the floor.

| Suite, floor | NC0 lines read | Nodes | Searches with [4] | Searches with [7] | Starts at child depth 1–2 | Search rows equal reference |
|---|---:|---:|---:|---:|---:|---|
| O_F0 | 200 | 8,315,168 | 4 | 0 | 9,719 | all |
| G_F0 | 353 | 17,611,204 | 81 | 0 | 30,888 | all |
| P_F0 | 1 | 182,707 | 1 | 1 | 529 | all |
| G_F1 | 353 | 18,559,820 | 0 | 10 | 349,955 | all |

Each cell below gives the event total, followed in parentheses by events per 1,000 nodes.

| Slot | Event | O_F0 | G_F0 | P_F0 | G_F1 |
|---:|---|---:|---:|---:|---:|
| [0] | Null searches started | 123,578 (14.861756) | 357,628 (20.306846) | 6,204 (33.956006) | 351,588 (18.943503) |
| [1] | Starts at child depth ≤0 | 113,502 (13.649995) | 325,285 (18.470344) | 5,570 (30.485969) | 0 (0.000000) |
| [2] | All actual null cutoffs | 86,995 (10.462206) | 244,577 (13.887580) | 3,846 (21.050097) | 231,554 (12.476091) |
| [3] | Cutoffs at child depth ≤0 | 85,212 (10.247779) | 233,592 (13.263829) | 3,612 (19.769357) | 0 (0.000000) |
| [4] | Cutoffs at child depth ≤0 with a quiet mate in one | 5 (0.000601) | 513 (0.029129) | 52 (0.284609) | 0 (0.000000) |
| [5] | All actual null cutoffs (repeated denominator) | 86,995 (10.462206) | 244,577 (13.887580) | 3,846 (21.050097) | 231,554 (12.476091) |
| [6] | Cutoffs at child depth 1 or 2 | 1,763 (0.212022) | 10,704 (0.607795) | 203 (1.111069) | 231,117 (12.452545) |
| [7] | Cutoffs at child depth 1 or 2 with a quiet mate in one | 0 (0.000000) | 0 (0.000000) | 1 (0.005473) | 27 (0.001455) |


On G with floor 0, 513 of 233,592 depth-zero-or-lower null cutoffs had a quiet mate in one in the hypothetical null child (0.220%). They occurred in 81 of 353 root positions (22.95%) and at a rate of 0.029129 per 1,000 search nodes. Floor 1 eliminates that depth bucket by construction. At child depths 1–2 the floor-1 observer still found 27 qualifying cutoffs in 10 root positions (0.001455 per 1,000 nodes). The events may revisit a position in multiple iterations. They do not show that each affected root had a forced mate or chose a wrong move. The recount command reports the number of NC0 lines read per run. [Replay command and counter definitions](astra5/job4/C)

## Part D — depth-12 cost on O and G

PC with the floor patch, PC20, depth 12. Ratios use the same suite at floor 0.

| Suite | Rows per floor | Floor 0 nodes | Floor 1 nodes | Ratio | Floor 1 first three | Changed best moves |
| --- | --- | --- | --- | --- | --- | --- |
| O | 200 | 8,315,168 | 8,768,825 | 1.05455777 | 13712, 30033, 28584 | 46 |
| G | 353 | 17,611,204 | 18,559,820 | 1.05386435 | 41983, 65584, 80217 | 74 |

Floor 1 used 453,657 additional nodes on O (+5.46%) and 948,616 on G (+5.39%). [Paired rows](astra5/job4/D)

## Answer

**Yes, changing the null move alone removes the missed-mate symptom on P.** The Job 3 PC20 trace showed how an 11-ply reduction turned the null child into a quiescence search that could miss quiet `Qh7#`. All three interventions recovered the proven `g3g6` mate within depth 16. Floor 1 found it earliest, at depth 10. The two-way HistRework test identifies the PC20 setting that made the miss appear on the tested ladders. The counter measures how often the local quiet-mate pattern recurred on G, without classifying those root choices as mate failures. [Job 3 trace](REPORT_astra5_job3.md)

## Facts

The floor-0 patch reproduced the prior ladders and rows. The counting patch preserved every checked row. The null-only interventions changed the search outcome on P, and floor 1 increased both suite node totals at fixed depth. The strongest control for HistRework was adding it alone to S14 and removing it alone from PC20, with opposite results on the same P.

## Suspicions

Threat-keyed quiet history or the correction term may explain why `HistRework 2` changed the ordering of the queen sacrifice. The experiment changed both together. The [7] events at positive child depth may have different return paths from P’s depth-zero quiescence cutoff.

## What I did not do

I did not run games or change the repository’s engine source. I did not trace each of the 513 G events or solve those root positions for forced mate.

## What I am not sure about

The local event is a quiet mate after a hypothetical pass. The frequency with which it changes the root best move or costs a game remains unknown. The causal result on P depends on the settings and evaluation used here.

## What this cannot see

```text
the PC's own net (this is the built-in evaluation), other settings, games. A tree size or a count is not strength; the PC decides any change with games.
```

## Pre-commit working tree and evidence files

```text
$ git status --short && ls -R forge-combo29/astra5/job4
 A forge-combo29/REPORT_astra5_job4.md
M  forge-combo29/astra5/job4/stamps.txt
?? forge-combo29/astra5/job1/__pycache__/
forge-combo29/astra5/job4:
A
B
C
D
build-floor
measure.py
null_count.patch.txt
null_floor.patch.txt
part-a-readback.md
part-b-readback.md
part-d-readback.md
prediction.txt
readback4.py
stamps.txt
step0
step0-pc.txt
step0-pca.txt

forge-combo29/astra5/job4/A:
Base3.meta
Base3.raw.txt
Base3.tsv
Base4.meta
Base4.raw.txt
Base4.tsv
Floor0.meta
Floor0.raw.txt
Floor0.tsv
Floor1.meta
Floor1.raw.txt
Floor1.tsv
G_floor0.tsv
G_floor0.tsv.meta
O_floor0.tsv
O_floor0.tsv.meta
checks.txt

forge-combo29/astra5/job4/B:
B1.meta
B1.raw.txt
B1.tsv
B2.meta
B2.raw.txt
B2.tsv
B3.meta
B3.raw.txt
B3.tsv
B4.meta
B4.raw.txt
B4.tsv
B5.meta
B5.raw.txt
B5.tsv
B6.meta
B6.raw.txt
B6.tsv
B7.meta
B7.raw.txt
B7.tsv
PC20.meta
PC20.raw.txt
PC20.tsv
S14.meta
S14.raw.txt
S14.tsv
checks.txt

forge-combo29/astra5/job4/C:
build.txt
definitions.md
gate-G_F0.txt
gate-G_F1.txt
gate-O_F0.txt
gate-P_F0.txt
patch-apply.txt
read_null_counts.py
rows
run_nc.py
summary.txt

forge-combo29/astra5/job4/C/rows:
G_F0.tsv
G_F0.tsv.meta
G_F1.tsv
G_F1.tsv.meta
O_F0.tsv
O_F0.tsv.meta
P_F0.tsv
P_F0.tsv.meta

forge-combo29/astra5/job4/D:
G_floor1.tsv
G_floor1.tsv.meta
O_floor1.tsv
O_floor1.tsv.meta
checks.txt

forge-combo29/astra5/job4/build-floor:
floor-build.txt
floor-uci.txt
null-floor-apply.txt
pc-r15-apply.txt
source-provenance.txt

forge-combo29/astra5/job4/step0:
pc-PC20-bench-11.txt
pc-PC20-bench-13.txt
pc-S14-bench-11.txt
pc-S14-bench-13.txt
pc-no-setoption-bench-11.txt
pc-no-setoption-bench-13.txt
pc-no-setoption-go-perft-5.txt
pc-uci.txt
pca-PC20-bench-11.txt
pca-PC20-bench-13.txt
pca-no-setoption-bench-11.txt
pca-no-setoption-bench-13.txt
pca-no-setoption-go-perft-5.txt
pca-uci.txt
```
