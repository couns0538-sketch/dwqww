# Astra5 job 10 — where the quiet-mate guard acts

## 1. Step 0

The job 7 r15d guard executable matched SHA-256 `ca7ef24ddd1cc80216712646bf71beaa9eacf1ac2184e0e0f11d078b10ff4f2e`. With the built-in evaluation and default options, fresh processes returned 312,866 nodes on bench 11, 862,329 on bench 13 and 4,865,609 on starting-position perft 5. [Pins and UCI transcripts](astra5/job10/step0)

## 2. C10 counting build

C10 adds diagnostic counters to the job 7 Part A guard tree. The patch changes only `src/search.cpp` and has SHA-256 `988e3b83abb65392f9dd8d33184c41b7f2c5fc5754170ae75f7e175288480e82`. The resulting executable has SHA-256 `ee571ad39229b59fa26c9c1567c34b185a6a64d654f2e7ebe67a10479f305f9c`. [Counter patch](astra5/job10/guard10_counts.patch.txt) · [Hashes and build](astra5/job10/step1)

At the ordinary null-move pruning probe, **N** counts searches started, including interrupted probes. **F** counts completed results at or above beta, at any null-child depth. **M** counts those F results whose score passes the engine’s mate-score predicate, before any clamp to beta. **A** and **B** count positive quiet-mate tests on completed fail-highs with null-child depth at or below zero. Thus M and A measure different events, both with denominator F.

C10 evaluates both predicates on every eligible visit regardless of the selected option. The fast diagnostic checks a copy of the still-null child. The reference diagnostic reconstructs that null child from a by-value copy of the restored parent. Their counters never feed the search. The original option still determines which predicate can refuse a cutoff. Each search starts with cleared counters and reports them at its end. [Patched source locations](astra5/job10/step1/locations.txt)

## 3. Fixed-depth known answers

Three fresh C10 processes reproduced bench 11 (312,866 nodes), bench 13 (862,329) and starting-position perft 5 (4,865,609). [C10 pins](astra5/job10/step2/pins/pins.txt)

Every depth-12 row matched its job 7 counterpart by FEN, best move and nodes. These runs used PC20, the built-in evaluation, Threads 1 and Hash 16. The last column counts positions where the two TRUE counters differed within the same search. [Job 7 reference rows](astra5/job7/A)

| Suite | NullMateGuard | Rows equal | Node sum | A ≠ B positions |
| --- | --- | --- | --- | --- |
| O | 0 | 200/200 | 8,315,168 | 0 |
| O | 1 | 200/200 | 8,315,218 | 0 |
| O | 2 | 200/200 | 8,315,218 | 0 |
| G | 0 | 353/353 | 17,611,204 | 0 |
| G | 1 | 353/353 | 17,848,355 | 0 |
| G | 2 | 353/353 | 17,848,355 | 0 |

The columns compare nodes under values 0 and 1 at the same FEN. The row classification uses A on the value-0 tree.

| Suite | Value-0 classification | Nodes equal | Nodes differ |
| --- | --- | --- | --- |
| O | A = 0 | 196 | 0 |
| O | A > 0 | 0 | 4 |
| G | A = 0 | 272 | 0 |
| G | A > 0 | 3 | 78 |

In both suites, every position with zero reference positives on the untreated tree retained its node count. O gained 50 nodes across 4 positions with both a positive exact test and a changed total. G gained 237,151 nodes across 78 positions with both a positive exact test and a changed total. [Suite readback](astra5/job10/step2)

<details><summary>Fixed-depth counter totals for all six suite runs</summary>

| Suite | Guard | N | F | M | A | B | M / F | A / F | A by piece count (2–5 / 6–9 / 10–15 / 16–32) | A by depth (1–6 / 7–10 / 11+) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O | 0 | 123,578 | 86,995 | 0 | 5 | 5 | 0.000000% | 0.005747% | 0 / 0 / 0 / 5 | 5 / 0 / 0 |
| O | 1 | 123,578 | 86,995 | 0 | 5 | 5 | 0.000000% | 0.005747% | 0 / 0 / 0 / 5 | 5 / 0 / 0 |
| O | 2 | 123,578 | 86,995 | 0 | 5 | 5 | 0.000000% | 0.005747% | 0 / 0 / 0 / 5 | 5 / 0 / 0 |
| G | 0 | 357,628 | 244,577 | 15 | 513 | 513 | 0.006133% | 0.209750% | 18 / 125 / 277 / 93 | 444 / 69 / 0 |
| G | 1 | 369,197 | 252,613 | 15 | 465 | 465 | 0.005938% | 0.184076% | 22 / 159 / 220 / 64 | 404 / 61 / 0 |
| G | 2 | 369,197 | 252,613 | 15 | 465 | 465 | 0.005938% | 0.184076% | 22 / 159 / 220 / 64 | 404 / 61 / 0 |

</details>

## 4. Frozen prediction

Commit `640b50324c50fc4d601cc05f17a1e5809cb741b6` contained only `prediction.txt`. The share forecasts are fractions of F. The same ranges and piece class apply separately to each game-position run. [Frozen prediction](astra5/job10/prediction.txt) · [Step stamps](astra5/job10/stamps.txt)

| Guard | Quantity | Forecast | Inclusive range | Observed | Grade |
| --- | --- | --- | --- | --- | --- |
| 0 | M/F | 0.00010 | 0.00002 to 0.00018 | 0.00011062 | Inside range, point missed |
| 0 | A/F | 0.00150 | 0.00080 to 0.00250 | 0.00304582 | Outside range, point missed |
| 0 | Largest A piece class | 10–15 | — | 10–15 | Matched |
| 2 | M/F | 0.00010 | 0.00002 to 0.00018 | 0.00010067 | Inside range, point missed |
| 2 | A/F | 0.00150 | 0.00080 to 0.00250 | 0.00255550 | Outside range, point missed |
| 2 | Largest A piece class | 10–15 | — | 10–15 | Matched |

## 5. Game-position results

I sampled after every tenth played half-move from each game’s supplied opening FEN, in the physical record order of the committed job 8 M1 PGN. Sampling stopped at 2,000 positions, spanning 152 game records and 1,199 distinct six-field FENs. Repeated and terminal positions remained in the sample. The map preserves both physical PGN record and scheduled game ID. The sampled FEN file has SHA-256 `6eeb847e6f18b1936b5858e42dd211c9cbd18034b0baac07961ee9ac4a6f2fab`. [M1 PGN](astra5/job8/M1.pgn) · [FENs](astra5/job10/step3/corpus/game_positions.fen) · [Extraction record](astra5/job10/step3/corpus/extraction.txt) · [Game and ply map](astra5/job10/step3/corpus/source-map.tsv)

C10 used PC20, the built-in evaluation, Threads 1 and Hash 16 on both runs. A single process handled each guard value, first 0 and then 2. Each position used `ucinewgame`, waited for `readyok`, and then searched with `go nodes 20000`.

| Guard | Positions | N null searches | F fail-highs | M mate-score fail-highs | A exact positives | B fast positives | M / F | A / F |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 2,000 | 539,260 | 388,730 | 43 | 1,184 | 1,184 | 0.011062% | 0.304582% |
| 2 | 2,000 | 537,345 | 387,400 | 39 | 990 | 990 | 0.010067% | 0.255550% |

The piece count includes both kings. The depth class uses the remaining depth of the parent at the null probe. Each set of class counts sums to A.

| Guard | 2–5 pieces | 6–9 pieces | 10–15 pieces | 16–32 pieces | Depth 1–6 | Depth 7–10 | Depth 11+ |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 19 | 355 | 531 | 279 | 998 | 186 | 0 |
| 2 | 24 | 289 | 405 | 272 | 860 | 130 | 0 |

Guard 2 changed the best move in **17 of 2,000 positions** relative to guard 0. For each listed FEN, “nodes” is the worker-total node count returned for the search, including work in an unfinished final iteration. Searches that end early can finish below the cap. The input included 14 positions with no legal move.

### Twenty positions with the largest A on guard 0

The ranking uses descending A on the untreated tree, then ascending one-based input index. The same input row supplies the value-2 comparison. A FEN can occur more than once in the corpus.

| Rank | Input row | FEN | A on 0 | A on 2 | Nodes 0 / 2 | Best move 0 / 2 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 1871 | `8/2Q2k2/4p1p1/5pP1/3q1P1K/7P/8/8 b - - 7 75` | 59 | 32 | 20000 / 20000 | `f7f8` / `f7f8` |
| 2 | 26 | `3Q4/5k2/6p1/5b1p/5P2/1p3Pq1/3P4/5R1K w - - 10 65` | 23 | 15 | 20000 / 20000 | `d8c7` / `d8c7` |
| 3 | 1523 | `2k4r/R7/p1p2N2/2B5/4P3/8/6P1/5RK1 b - - 2 37` | 22 | 1 | 20000 / 20000 | `h8h4` / `h8d8` |
| 4 | 1376 | `6R1/1p3r2/p1p4k/6R1/3P1pp1/2P2r2/PP4K1/8 b - - 9 46` | 21 | 17 | 20000 / 20000 | `f3g3` / `f3g3` |
| 5 | 818 | `8/1p3r1k/2p4p/pr3p2/8/P1Q3RP/3N1PP1/1B2R1K1 b - - 6 37` | 20 | 22 | 20000 / 20000 | `b5b1` / `b5b1` |
| 6 | 824 | `8/1p3r1k/2p4p/pr3p2/8/P1Q3RP/3N1PP1/1B2R1K1 b - - 6 37` | 20 | 22 | 20000 / 20000 | `b5b1` / `b5b1` |
| 7 | 1897 | `5k2/3q2p1/p1rP1p2/1p5p/1P1RP3/7P/B4PP1/3Q2K1 b - - 1 32` | 19 | 10 | 20000 / 20000 | `g7g5` / `g7g5` |
| 8 | 1924 | `5k2/3q2p1/p1rP1p2/1p5p/1P1RP3/7P/B4PP1/3Q2K1 b - - 1 32` | 19 | 10 | 20000 / 20000 | `g7g5` / `g7g5` |
| 9 | 1546 | `8/8/8/p4B2/P2k4/3P4/1Kp3r1/8 w - - 2 59` | 18 | 15 | 20000 / 20000 | `f5h7` / `f5h7` |
| 10 | 1559 | `8/8/8/p4B2/P2k4/3P4/1Kp3r1/8 w - - 2 59` | 18 | 15 | 20000 / 20000 | `f5h7` / `f5h7` |
| 11 | 1867 | `4Q3/2q2pk1/6p1/3pNpP1/3P1P2/b5KP/8/8 b - - 25 55` | 18 | 7 | 20000 / 20000 | `c7c3` / `a3b4` |
| 12 | 1179 | `5k2/R7/R7/2r2pp1/6P1/7P/p4PK1/r7 w - - 4 44` | 15 | 15 | 20000 / 20000 | `a6f6` / `a6h6` |
| 13 | 1213 | `5k2/R7/R7/2r2pp1/6P1/7P/p4PK1/r7 w - - 4 44` | 15 | 15 | 20000 / 20000 | `a6f6` / `a6h6` |
| 14 | 1545 | `8/8/B7/p7/P2k4/2pP4/1r6/1K6 w - - 10 54` | 15 | 10 | 20000 / 20000 | `b1c1` / `b1c1` |
| 15 | 1547 | `8/8/8/p1r5/P2kB3/3P4/1Kp5/8 w - - 12 64` | 15 | 4 | 20000 / 20000 | `b2c1` / `b2c1` |
| 16 | 1558 | `8/8/B7/p7/P2k4/2pP4/1r6/1K6 w - - 10 54` | 15 | 10 | 20000 / 20000 | `b1c1` / `b1c1` |
| 17 | 1560 | `8/8/8/p1r5/P2kB3/3P4/1Kp5/8 w - - 12 64` | 15 | 4 | 20000 / 20000 | `b2c1` / `b2c1` |
| 18 | 1870 | `8/5p1k/6p1/4PpP1/5P1K/4Q2P/8/7q b - - 2 70` | 15 | 17 | 20000 / 20000 | `h1d5` / `h1d5` |
| 19 | 25 | `8/5k2/4b1p1/7p/3Q1P2/1p3Pq1/3P4/5R1K w - - 0 60` | 14 | 13 | 20000 / 20000 | `d4a7` / `d4a7` |
| 20 | 457 | `8/3B4/8/6k1/4b3/5p2/7r/4K3 w - - 0 63` | 14 | 6 | 20000 / 20000 | `d7b5` / `e1f1` |

<details><summary>Twenty positions with the largest A on guard 2</summary>

| Rank | Input row | FEN | A on 0 | A on 2 | Nodes 0 / 2 | Best move 0 / 2 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 1871 | `8/2Q2k2/4p1p1/5pP1/3q1P1K/7P/8/8 b - - 7 75` | 59 | 32 | 20000 / 20000 | `f7f8` / `f7f8` |
| 2 | 818 | `8/1p3r1k/2p4p/pr3p2/8/P1Q3RP/3N1PP1/1B2R1K1 b - - 6 37` | 20 | 22 | 20000 / 20000 | `b5b1` / `b5b1` |
| 3 | 824 | `8/1p3r1k/2p4p/pr3p2/8/P1Q3RP/3N1PP1/1B2R1K1 b - - 6 37` | 20 | 22 | 20000 / 20000 | `b5b1` / `b5b1` |
| 4 | 1404 | `2r1k2r/1pp1P1pp/p7/7q/2BpR3/3P1p1b/P1P2P1P/R2Q3K w k - 4 19` | 14 | 20 | 20000 / 20000 | `e4d4` / `e4d4` |
| 5 | 1344 | `5k2/6R1/1p1N1p2/p1nPp3/2P1Pn1p/1P6/P1B2q2/4R2K b - - 2 37` | 11 | 18 | 20000 / 20000 | `f2e1` / `f2e1` |
| 6 | 1351 | `5k2/6R1/1p1N1p2/p1nPp3/2P1Pn1p/1P6/P1B2q2/4R2K b - - 2 37` | 11 | 18 | 20000 / 20000 | `f2e1` / `f2e1` |
| 7 | 1376 | `6R1/1p3r2/p1p4k/6R1/3P1pp1/2P2r2/PP4K1/8 b - - 9 46` | 21 | 17 | 20000 / 20000 | `f3g3` / `f3g3` |
| 8 | 1870 | `8/5p1k/6p1/4PpP1/5P1K/4Q2P/8/7q b - - 2 70` | 15 | 17 | 20000 / 20000 | `h1d5` / `h1d5` |
| 9 | 26 | `3Q4/5k2/6p1/5b1p/5P2/1p3Pq1/3P4/5R1K w - - 10 65` | 23 | 15 | 20000 / 20000 | `d8c7` / `d8c7` |
| 10 | 1179 | `5k2/R7/R7/2r2pp1/6P1/7P/p4PK1/r7 w - - 4 44` | 15 | 15 | 20000 / 20000 | `a6f6` / `a6h6` |
| 11 | 1213 | `5k2/R7/R7/2r2pp1/6P1/7P/p4PK1/r7 w - - 4 44` | 15 | 15 | 20000 / 20000 | `a6f6` / `a6h6` |
| 12 | 1546 | `8/8/8/p4B2/P2k4/3P4/1Kp3r1/8 w - - 2 59` | 18 | 15 | 20000 / 20000 | `f5h7` / `f5h7` |
| 13 | 1559 | `8/8/8/p4B2/P2k4/3P4/1Kp3r1/8 w - - 2 59` | 18 | 15 | 20000 / 20000 | `f5h7` / `f5h7` |
| 14 | 1510 | `4R3/q6n/2r1p2k/3pP3/3P2QP/7P/6P1/7K w - - 3 52` | 13 | 14 | 20000 / 20000 | `e8e6` / `e8e6` |
| 15 | 1532 | `4R3/q6n/2r1p2k/3pP3/3P2QP/7P/6P1/7K w - - 3 52` | 13 | 14 | 20000 / 20000 | `e8e6` / `e8e6` |
| 16 | 1972 | `5r1k/ppQ3pp/3P4/5p2/2N3nP/8/q5P1/4K2R b - - 1 28` | 9 | 14 | 20000 / 20000 | `f8e8` / `f8e8` |
| 17 | 1981 | `5r1k/ppQ3pp/3P4/5p2/2N3nP/8/q5P1/4K2R b - - 1 28` | 9 | 14 | 20000 / 20000 | `f8e8` / `f8e8` |
| 18 | 25 | `8/5k2/4b1p1/7p/3Q1P2/1p3Pq1/3P4/5R1K w - - 0 60` | 14 | 13 | 20000 / 20000 | `d4a7` / `d4a7` |
| 19 | 1561 | `8/5r2/8/p7/P7/3k3B/2p5/2K5 w - - 0 69` | 6 | 13 | 20000 / 20000 | `h3g2` / `h3g2` |
| 20 | 1354 | `r3k2r/2p1P1pp/p7/1p5q/2BpR3/3P1p1b/P1P2P1P/R2Q3K w kq b6 0 19` | 12 | 12 | 20000 / 20000 | `c4b3` / `c4b3` |

</details>

## 6. Reading

**Description only, no verdict.** These classes contained the most positive exact tests in each run.

| Guard | Piece class | A in class / all A | Remaining depth | A in class / all A |
| --- | --- | --- | --- | --- |
| 0 | 10–15 | 531 / 1,184 | 1–6 | 998 / 1,184 |
| 2 | 10–15 | 405 / 990 | 1–6 | 860 / 990 |

## Facts

The number of positions with different A and B totals was 0 under guard 0 and 0 under guard 2. On the untreated tree, 271 positions had at least one positive exact test. With guard 2 acting, 271 positions had a positive exact test. Of the 1,729 positions with A = 0 on the untreated tree, 0 changed best move. Of the 271 with A > 0, 17 changed best move.

The counters record how often each predicate succeeded. Equal position totals do not identify the particular visits at which they succeeded. The same position can contribute more than once. A positive predicate on the guard-0 tree is an opportunity to refuse a cutoff. On guard 2, that predicate can change subsequent searches and the opportunities counted later.

## Suspicions

A class can lead because the sampled search visited it more often, because its fail-highs more often exposed a quiet mate, or both. The class counters split the positives, without counting a fail-high denominator for each class.

## What I did not do

I did not play games or measure CPU time with this counting build.

**What this cannot see**, in the job’s words

> the PC's net, compiler and processor; positions other than these; whether a changed return wins or loses games (that is jobs 8, 9 and 11).

## What I am not sure about

These counts do not establish that the class with the most guard activations accounted for the most additional search nodes. That attribution would require measuring the descendant work after each veto and handling nested descendants.

## Pre-commit inventory

Output from `git status --short` followed by `ls -R forge-combo29/astra5/job10`.

```text
A  forge-combo29/REPORT_astra5_job10.md
M  forge-combo29/astra5/job10/stamps.txt
forge-combo29/astra5/job10:
counters.py
depth_rows.py
guard10_counts.patch.txt
prediction.txt
stamps.txt
step0
step1
step2
step3
step3.py
table2.py

forge-combo29/astra5/job10/step0:
bench-11.txt
bench-13.txt
go-perft-5.txt
pins.txt

forge-combo29/astra5/job10/step1:
build-provenance.txt
build.txt
hashes.txt
locations.txt
patch-apply.txt

forge-combo29/astra5/job10/step2:
2x2.tsv
G
O
pins
references.txt
source-review.txt
step2-runs.tsv
step2.tsv
summary.txt

forge-combo29/astra5/job10/step2/G:
Guard0
Guard1
Guard2

forge-combo29/astra5/job10/step2/G/Guard0:
checks.txt
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job10/step2/G/Guard1:
checks.txt
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job10/step2/G/Guard2:
checks.txt
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job10/step2/O:
Guard0
Guard1
Guard2

forge-combo29/astra5/job10/step2/O/Guard0:
checks.txt
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job10/step2/O/Guard1:
checks.txt
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job10/step2/O/Guard2:
checks.txt
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job10/step2/pins:
bench-11.txt
bench-13.txt
go-perft-5.txt
pins.txt

forge-combo29/astra5/job10/step3:
Guard0
Guard2
audit
comparisons.txt
corpus
step3-changes.txt
step3.tsv
sums.tsv
top20-guard0.tsv
top20-guard2.tsv

forge-combo29/astra5/job10/step3/Guard0:
checks.txt
rows.tsv
settings.txt
uci.log

forge-combo29/astra5/job10/step3/Guard2:
checks.txt
rows.tsv
settings.txt
uci.log

forge-combo29/astra5/job10/step3/audit:
top20-0.tsv
top20-2.tsv

forge-combo29/astra5/job10/step3/corpus:
extract_fens.py
extraction.txt
game_positions.fen
game_positions.sha256
source-identity.txt
source-map.tsv
```
