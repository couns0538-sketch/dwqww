# sol2 — Job 6 matched ABBA floor, k11 timing and profile

## Step 0 — all frozen identities passed

Fresh-process r15d pins matched **312,866** for `bench 11`, **862,329** for `bench 13` and **4,865,609** for startpos perft 5 with embedded AL1 s198, Threads 1, Hash 16 MiB, MultiPV 1 and OwnBook false. r15d, k10, k11 and k12 matched their Job 5 hashes. A distinct r15d copy path had the same SHA-256 and `cmp` returned zero with an empty difference stream. [Exact hashes and cmp](sol2/job6/step0-identity.raw.txt) · [Raw pins](sol2/job6/step0-pins.raw.txt)

| Build | SHA-256 |
|---|---|
| r15d and copy | `bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6` |
| k10 | `55fed57fadf76d5e861da3f9bf3601b43c6bf67e6d152d87edfcf648e26207ae` |
| k11 | `a7a34a148b40c14e5ea960dd2d3182fceef7023a38d12db47c2521a430fc1ea5` |
| k12 | `9b50324e42ea8fe42f3246149d7389726f8994650080790349018e956d60eca7` |

All timing rows use the Job 5 GCC 14.2.0, libstdc++ 6.0.33, glibc 2.41 Release builds with x86-64-v4, strict FP, v3 AVX-512 and no LTO or PGO. The engine and driver were pinned to logical CPU 2 of the AMD EPYC 9V74 cloud VM. Every run used the Carbon2 driver, 60 startpos games, eight random plies, seed `20261117`, maximum 300 plies, PC20, Threads 1, Hash 16 MiB, `go softnodes 2000`, and synthetic net768 checksum `30ab43b4ba5db5f3`. The exact common result was **8,612 searches, 29,333,343 last-info nodes, trace `5c705841c3ea17b4`**. [Net and driver identity](sol2/job6/step0-identity.raw.txt) · [Build recipe](REPORT_sol2_job5.md#step-1--all-patches-and-warm-traces-passed)

## Prediction grade and reading rule

The prediction was pushed alone at `86d8993f7368229564218c7e0bf61fd17b341188` before any timings. The control's observed CPU range was **0.9699–1.0523** versus **0.972–1.025** predicted. Wall was **0.9681–1.0539** versus **0.970–1.030**. Both lower limits were close, and both upper limits exceeded the prediction. Pooled k11/r15d CPU was **0.9457** versus **0.950** predicted. Pooled k11/k10 CPU was **0.9992** versus **0.985** predicted. Move generation and legality had the largest profile-derived CPU reduction as predicted, **0.681 s per run**. [Prediction](sol2/job6/prediction.txt) · [Publication order](sol2/job6/prediction-order.raw.txt) · [Timing readback](sol2/job6/abba-readback.raw.txt) · [Subsystem CPU](sol2/job6/step4/compare/subsystems.tsv.txt)

Each ABBA ratio divides the sum of the two inner B times by the sum of the two outer A times. The pooled ratio uses all the times in each arm. The decision compares the candidate median against the whole identical-binary ABBA range and requires at least 10 of 12 blocks on the same side of one. CPU is the reaped Forge process's user plus system time. Wall is the full driver call with setup, warm-up, and teardown. Each run started a fresh engine. All 120 runs exited zero and reproduced the pinned trace. [Timing harness](sol2/job6/abba_timing_steps2_3.py.txt) · [Independent timing arithmetic](sol2/job6/abba-readback.raw.txt)

The scratch timing script was revised during Step 1 after its launch. The revision tightened complete-run and floor validation. Driver execution, clock boundaries and complete-block arithmetic are identical across the two versions. I preserved both scripts and independently reproduced the summaries and decisions from the 120 raw rows. [Step 1 harness](sol2/job6/abba_timing.py.txt) · [Revision diff and hash receipt](sol2/job6/abba-harness-revision.raw.txt)

## Step 1 — identical-binary ABBA floor

| Block | Leg | Engine | CPU (s) | Wall (s) | Trace |
|---:|---:|---|---:|---:|---|
| 1 | 1 | r15d | 19.455 | 20.184 | `5c705841c3ea17b4` |
| 1 | 2 | copy | 19.828 | 20.592 | `5c705841c3ea17b4` |
| 1 | 3 | copy | 19.314 | 20.066 | `5c705841c3ea17b4` |
| 1 | 4 | r15d | 18.591 | 19.303 | `5c705841c3ea17b4` |
| 2 | 1 | r15d | 18.417 | 19.133 | `5c705841c3ea17b4` |
| 2 | 2 | copy | 19.118 | 19.832 | `5c705841c3ea17b4` |
| 2 | 3 | copy | 19.091 | 19.830 | `5c705841c3ea17b4` |
| 2 | 4 | r15d | 20.975 | 21.837 | `5c705841c3ea17b4` |
| 3 | 1 | r15d | 20.076 | 20.867 | `5c705841c3ea17b4` |
| 3 | 2 | copy | 20.298 | 21.132 | `5c705841c3ea17b4` |
| 3 | 3 | copy | 21.235 | 22.128 | `5c705841c3ea17b4` |
| 3 | 4 | r15d | 19.392 | 20.182 | `5c705841c3ea17b4` |
| 4 | 1 | r15d | 19.164 | 19.899 | `5c705841c3ea17b4` |
| 4 | 2 | copy | 18.806 | 19.526 | `5c705841c3ea17b4` |
| 4 | 3 | copy | 18.640 | 19.340 | `5c705841c3ea17b4` |
| 4 | 4 | r15d | 18.358 | 19.051 | `5c705841c3ea17b4` |
| 5 | 1 | r15d | 18.715 | 19.435 | `5c705841c3ea17b4` |
| 5 | 2 | copy | 18.860 | 19.576 | `5c705841c3ea17b4` |
| 5 | 3 | copy | 19.204 | 19.964 | `5c705841c3ea17b4` |
| 5 | 4 | r15d | 19.254 | 19.999 | `5c705841c3ea17b4` |
| 6 | 1 | r15d | 20.015 | 20.800 | `5c705841c3ea17b4` |
| 6 | 2 | copy | 19.727 | 20.523 | `5c705841c3ea17b4` |
| 6 | 3 | copy | 19.270 | 20.030 | `5c705841c3ea17b4` |
| 6 | 4 | r15d | 19.139 | 19.887 | `5c705841c3ea17b4` |

| Block | B/A CPU | B/A wall |
|---:|---:|---:|
| 1 | 1.0288 | 1.0296 |
| 2 | 0.9699 | 0.9681 |
| 3 | 1.0523 | 1.0539 |
| 4 | 0.9980 | 0.9978 |
| 5 | 1.0025 | 1.0027 |
| 6 | 0.9960 | 0.9967 |

| Metric | Median | Pooled | Block range | Blocks below 1 | Decision |
|---|---:|---:|---:|---:|---|
| Engine CPU | 1.0002 | 1.0079 | 0.9699–1.0523 | 3/6 | Identical-binary floor |
| Wall | 1.0003 | 1.0082 | 0.9681–1.0539 | 3/6 | Identical-binary floor |

[Raw runs](sol2/job6/step1/runs.jsonl.txt) · [Summary](sol2/job6/step1/summary.txt) · [Command](sol2/job6/step1-command.raw.txt)

## Step 2 — k11 against r15d

| Block | Leg | Engine | CPU (s) | Wall (s) | Trace |
|---:|---:|---|---:|---:|---|
| 1 | 1 | r15d | 20.342 | 21.124 | `5c705841c3ea17b4` |
| 1 | 2 | k11 | 18.985 | 19.765 | `5c705841c3ea17b4` |
| 1 | 3 | k11 | 19.362 | 20.132 | `5c705841c3ea17b4` |
| 1 | 4 | r15d | 20.105 | 20.873 | `5c705841c3ea17b4` |
| 2 | 1 | r15d | 18.966 | 19.697 | `5c705841c3ea17b4` |
| 2 | 2 | k11 | 17.836 | 18.558 | `5c705841c3ea17b4` |
| 2 | 3 | k11 | 17.960 | 18.670 | `5c705841c3ea17b4` |
| 2 | 4 | r15d | 18.547 | 19.250 | `5c705841c3ea17b4` |
| 3 | 1 | r15d | 18.854 | 19.574 | `5c705841c3ea17b4` |
| 3 | 2 | k11 | 18.446 | 19.182 | `5c705841c3ea17b4` |
| 3 | 3 | k11 | 17.997 | 18.706 | `5c705841c3ea17b4` |
| 3 | 4 | r15d | 19.286 | 20.020 | `5c705841c3ea17b4` |
| 4 | 1 | r15d | 19.781 | 20.563 | `5c705841c3ea17b4` |
| 4 | 2 | k11 | 19.264 | 20.048 | `5c705841c3ea17b4` |
| 4 | 3 | k11 | 18.804 | 19.608 | `5c705841c3ea17b4` |
| 4 | 4 | r15d | 19.611 | 20.389 | `5c705841c3ea17b4` |
| 5 | 1 | r15d | 20.092 | 20.878 | `5c705841c3ea17b4` |
| 5 | 2 | k11 | 18.736 | 19.496 | `5c705841c3ea17b4` |
| 5 | 3 | k11 | 18.823 | 19.583 | `5c705841c3ea17b4` |
| 5 | 4 | r15d | 20.392 | 21.207 | `5c705841c3ea17b4` |
| 6 | 1 | r15d | 19.023 | 19.747 | `5c705841c3ea17b4` |
| 6 | 2 | k11 | 17.940 | 18.658 | `5c705841c3ea17b4` |
| 6 | 3 | k11 | 18.779 | 19.560 | `5c705841c3ea17b4` |
| 6 | 4 | r15d | 19.791 | 20.558 | `5c705841c3ea17b4` |
| 7 | 1 | r15d | 21.123 | 21.994 | `5c705841c3ea17b4` |
| 7 | 2 | k11 | 19.760 | 20.568 | `5c705841c3ea17b4` |
| 7 | 3 | k11 | 21.729 | 22.663 | `5c705841c3ea17b4` |
| 7 | 4 | r15d | 21.314 | 22.209 | `5c705841c3ea17b4` |
| 8 | 1 | r15d | 20.020 | 20.813 | `5c705841c3ea17b4` |
| 8 | 2 | k11 | 18.288 | 19.023 | `5c705841c3ea17b4` |
| 8 | 3 | k11 | 18.541 | 19.274 | `5c705841c3ea17b4` |
| 8 | 4 | r15d | 19.115 | 19.840 | `5c705841c3ea17b4` |
| 9 | 1 | r15d | 18.894 | 19.617 | `5c705841c3ea17b4` |
| 9 | 2 | k11 | 17.397 | 18.085 | `5c705841c3ea17b4` |
| 9 | 3 | k11 | 19.052 | 19.835 | `5c705841c3ea17b4` |
| 9 | 4 | r15d | 19.985 | 20.773 | `5c705841c3ea17b4` |
| 10 | 1 | r15d | 19.592 | 20.341 | `5c705841c3ea17b4` |
| 10 | 2 | k11 | 17.847 | 18.557 | `5c705841c3ea17b4` |
| 10 | 3 | k11 | 18.179 | 18.905 | `5c705841c3ea17b4` |
| 10 | 4 | r15d | 18.334 | 19.018 | `5c705841c3ea17b4` |
| 11 | 1 | r15d | 19.333 | 20.095 | `5c705841c3ea17b4` |
| 11 | 2 | k11 | 17.619 | 18.297 | `5c705841c3ea17b4` |
| 11 | 3 | k11 | 18.297 | 19.019 | `5c705841c3ea17b4` |
| 11 | 4 | r15d | 19.669 | 20.430 | `5c705841c3ea17b4` |
| 12 | 1 | r15d | 21.438 | 22.332 | `5c705841c3ea17b4` |
| 12 | 2 | k11 | 19.415 | 20.226 | `5c705841c3ea17b4` |
| 12 | 3 | k11 | 18.451 | 19.196 | `5c705841c3ea17b4` |
| 12 | 4 | r15d | 19.586 | 20.363 | `5c705841c3ea17b4` |

| Block | B/A CPU | B/A wall |
|---:|---:|---:|
| 1 | 0.9481 | 0.9500 |
| 2 | 0.9543 | 0.9559 |
| 3 | 0.9555 | 0.9569 |
| 4 | 0.9664 | 0.9684 |
| 5 | 0.9277 | 0.9286 |
| 6 | 0.9460 | 0.9482 |
| 7 | 0.9777 | 0.9780 |
| 8 | 0.9411 | 0.9420 |
| 9 | 0.9375 | 0.9388 |
| 10 | 0.9499 | 0.9518 |
| 11 | 0.9209 | 0.9208 |
| 12 | 0.9230 | 0.9233 |

| Metric | Median | Pooled | Block range | Blocks below 1 | Decision |
|---|---:|---:|---:|---:|---|
| Engine CPU | 0.9470 | 0.9457 | 0.9209–0.9777 | 12/12 | MEASURED |
| Wall | 0.9491 | 0.9469 | 0.9208–0.9780 | 12/12 | MEASURED |

[Raw runs](sol2/job6/step2/runs.jsonl.txt) · [Summary](sol2/job6/step2/summary.txt) · [Command](sol2/job6/step2-command.raw.txt)

## Step 3 — k11 against k10, piece 11 alone

| Block | Leg | Engine | CPU (s) | Wall (s) | Trace |
|---:|---:|---|---:|---:|---|
| 1 | 1 | k10 | 19.212 | 19.992 | `5c705841c3ea17b4` |
| 1 | 2 | k11 | 18.443 | 19.185 | `5c705841c3ea17b4` |
| 1 | 3 | k11 | 18.006 | 18.721 | `5c705841c3ea17b4` |
| 1 | 4 | k10 | 18.783 | 19.546 | `5c705841c3ea17b4` |
| 2 | 1 | k10 | 17.967 | 18.665 | `5c705841c3ea17b4` |
| 2 | 2 | k11 | 18.878 | 19.650 | `5c705841c3ea17b4` |
| 2 | 3 | k11 | 18.104 | 18.842 | `5c705841c3ea17b4` |
| 2 | 4 | k10 | 18.187 | 18.907 | `5c705841c3ea17b4` |
| 3 | 1 | k10 | 18.742 | 19.500 | `5c705841c3ea17b4` |
| 3 | 2 | k11 | 18.770 | 19.555 | `5c705841c3ea17b4` |
| 3 | 3 | k11 | 20.264 | 21.126 | `5c705841c3ea17b4` |
| 3 | 4 | k10 | 19.821 | 20.651 | `5c705841c3ea17b4` |
| 4 | 1 | k10 | 18.580 | 19.335 | `5c705841c3ea17b4` |
| 4 | 2 | k11 | 18.994 | 19.774 | `5c705841c3ea17b4` |
| 4 | 3 | k11 | 18.267 | 18.987 | `5c705841c3ea17b4` |
| 4 | 4 | k10 | 18.251 | 18.971 | `5c705841c3ea17b4` |
| 5 | 1 | k10 | 18.040 | 18.753 | `5c705841c3ea17b4` |
| 5 | 2 | k11 | 18.239 | 18.967 | `5c705841c3ea17b4` |
| 5 | 3 | k11 | 18.904 | 19.687 | `5c705841c3ea17b4` |
| 5 | 4 | k10 | 18.611 | 19.364 | `5c705841c3ea17b4` |
| 6 | 1 | k10 | 17.989 | 18.717 | `5c705841c3ea17b4` |
| 6 | 2 | k11 | 18.401 | 19.151 | `5c705841c3ea17b4` |
| 6 | 3 | k11 | 17.895 | 18.608 | `5c705841c3ea17b4` |
| 6 | 4 | k10 | 18.403 | 19.122 | `5c705841c3ea17b4` |
| 7 | 1 | k10 | 18.751 | 19.504 | `5c705841c3ea17b4` |
| 7 | 2 | k11 | 19.358 | 20.171 | `5c705841c3ea17b4` |
| 7 | 3 | k11 | 19.552 | 20.368 | `5c705841c3ea17b4` |
| 7 | 4 | k10 | 18.140 | 18.886 | `5c705841c3ea17b4` |
| 8 | 1 | k10 | 19.558 | 20.352 | `5c705841c3ea17b4` |
| 8 | 2 | k11 | 19.166 | 19.944 | `5c705841c3ea17b4` |
| 8 | 3 | k11 | 18.302 | 19.043 | `5c705841c3ea17b4` |
| 8 | 4 | k10 | 17.957 | 18.664 | `5c705841c3ea17b4` |
| 9 | 1 | k10 | 18.094 | 18.805 | `5c705841c3ea17b4` |
| 9 | 2 | k11 | 17.814 | 18.525 | `5c705841c3ea17b4` |
| 9 | 3 | k11 | 17.782 | 18.481 | `5c705841c3ea17b4` |
| 9 | 4 | k10 | 17.839 | 18.526 | `5c705841c3ea17b4` |
| 10 | 1 | k10 | 18.735 | 19.472 | `5c705841c3ea17b4` |
| 10 | 2 | k11 | 18.213 | 18.941 | `5c705841c3ea17b4` |
| 10 | 3 | k11 | 18.459 | 19.206 | `5c705841c3ea17b4` |
| 10 | 4 | k10 | 18.724 | 19.456 | `5c705841c3ea17b4` |
| 11 | 1 | k10 | 19.312 | 20.093 | `5c705841c3ea17b4` |
| 11 | 2 | k11 | 18.462 | 19.185 | `5c705841c3ea17b4` |
| 11 | 3 | k11 | 19.872 | 20.730 | `5c705841c3ea17b4` |
| 11 | 4 | k10 | 20.531 | 21.396 | `5c705841c3ea17b4` |
| 12 | 1 | k10 | 18.181 | 18.902 | `5c705841c3ea17b4` |
| 12 | 2 | k11 | 17.417 | 18.099 | `5c705841c3ea17b4` |
| 12 | 3 | k11 | 18.482 | 19.231 | `5c705841c3ea17b4` |
| 12 | 4 | k10 | 17.974 | 18.671 | `5c705841c3ea17b4` |

| Block | B/A CPU | B/A wall |
|---:|---:|---:|
| 1 | 0.9593 | 0.9587 |
| 2 | 1.0229 | 1.0245 |
| 3 | 1.0122 | 1.0132 |
| 4 | 1.0117 | 1.0119 |
| 5 | 1.0134 | 1.0141 |
| 6 | 0.9974 | 0.9979 |
| 7 | 1.0547 | 1.0560 |
| 8 | 0.9987 | 0.9992 |
| 9 | 0.9906 | 0.9913 |
| 10 | 0.9790 | 0.9799 |
| 11 | 0.9621 | 0.9620 |
| 12 | 0.9929 | 0.9935 |

| Metric | Median | Pooled | Block range | Blocks below 1 | Decision |
|---|---:|---:|---:|---:|---|
| Engine CPU | 0.9981 | 0.9992 | 0.9593–1.0547 | 7/12 | not measurable here |
| Wall | 0.9986 | 0.9998 | 0.9587–1.0560 | 7/12 | not measurable here |

[Raw runs](sol2/job6/step3/runs.jsonl.txt) · [Summary](sol2/job6/step3/summary.txt) · [Command](sol2/job6/step3-command.raw.txt)

## Step 4 — same-session profile and function matching

The k11 frame-pointer build added `-g -fno-omit-frame-pointer`, SHA-256 `e33832c00230cb4a9de213a8ed5701ed59173eabc493fb11c041c7e96992eb2d`. The r15d profile build retained Job 3's SHA-256 `cba0bf8997b51422fd1e26ad13789d8d244a995adc1c03c88095459024c1743f`. The new k11 build passed the unprofiled identity check. Job 3's SEE control applied to k11 with zero fuzz at a **60-line offset**. The patched k11 moved `Board::see_ge` from **7th, 155 samples (3.45%)** in the first clean profile to **1st, 15,379 samples (71.43%)**, with the exact warm trace. The clean passes were interleaved, three per build, and all matched that trace. [Commands and binary identities](sol2/job6/step4/step4-command.raw.txt) · [Positive control diff](sol2/job6/step4/see-spin.patch.txt) · [Control readback](sol2/job6/step4/positive-control.raw.txt)

The function table pools each build's exclusive samples after applying the three prescribed symbol groups. A missing symbol row records zero observed samples. The subsystem CPU table multiplies each run's exclusive sample share by that run's reaped engine CPU, then averages the three estimates per build. The profile has instruction sampling and caller overhead. The ABBA times above come from clean unprofiled runs. The named subsystem estimates can move with inlining and attribution changes. [Source-grounded merge map](sol2/job6/step4/profile-merge-map.md) · [Matched top 15](sol2/job6/step4/compare/top15-mapped.tsv.txt) · [Per-run subsystem CPU](sol2/job6/step4/compare/subsystems-per-run.tsv.txt)

| Rank | Matched function or family | k11 line | r15d share | k11 share |
|---:|---|---|---:|---:|
| 1 | `Worker::search` | `search.cpp:2750` | 13.75% | 14.38% |
| 2 | `TranspositionTable::probe_body<false>` | `search.cpp:492` | 8.29% | 9.93% |
| 3 | `MovePicker::next and capture/quiet generation` | `search.cpp:1360` | 8.96% | 9.29% |
| 4 | `nnue::v3::apply_pair_and_evaluate` | `nnue_v3.cpp:890` | 8.41% | 8.32% |
| 5 | `nnue::v3::refresh_from_pieces` | `nnue_v3.cpp:954` | 6.26% | 6.38% |
| 6 | `Worker::corrected_eval` | `search.cpp:1805` | 4.66% | 4.77% |
| 7 | `nnue::v3::apply_changes_pair` | `nnue_v3.cpp:855` | 4.14% | 3.95% |
| 8 | `Board::see_ge` | `board.cpp:1553` | 4.04% | 3.55% |
| 9 | `MovePicker::pick_best / pick_best_scored` | `search.cpp:1075` | 3.55% | 3.34% |
| 10 | `Worker::qsearch` | `search.cpp:2232` | 2.94% | 3.04% |
| 11 | `Worker::static_evaluate_v3` | `search.cpp:3794` | 3.08% | 2.74% |
| 12 | `Board::make_move` | `board.cpp:1287` | 4.19% | 2.59% |
| 13 | `nnue::v3::apply_changes` | `nnue_v3.cpp:841` | 2.03% | 1.97% |
| 14 | `Board::unmake_move` | `board.cpp:1312` | 1.69% | 1.91% |
| 15 | `Board::has_legal_move` | `board.cpp:857` | 1.40% | 1.78% |

| Subsystem | r15d CPU s/run | k11 CPU s/run | k11 minus r15d |
|---|---:|---:|---:|
| Evaluation (NNUE v3) | 5.454 | 4.906 | -0.548 |
| Search control | 4.039 | 3.901 | -0.139 |
| Move ordering and picking | 2.988 | 3.292 | +0.304 |
| Hash table | 1.997 | 2.296 | +0.299 |
| Move generation and legality | 2.000 | 1.319 | -0.681 |
| Board updates and position keys | 1.389 | 1.071 | -0.318 |
| Draw and repetition checks | 0.607 | 0.665 | +0.058 |
| Other runtime and libraries | 0.662 | 0.596 | -0.065 |
| Static exchange evaluation | 0.635 | 0.596 | -0.039 |
| Other engine work | 0.078 | 0.087 | +0.008 |
| UCI and input/output | 0.022 | 0.007 | -0.015 |
| Unresolved | 0.006 | 0.007 | +0.001 |

[Matched profile summary](sol2/job6/step4/compare/subsystems.tsv.txt) · [Raw symbol family members](sol2/job6/step4/compare/merged-symbol-members.tsv.txt)

## Facts

- The identical-binary ABBA medians were close to one, and the observed floor was substantially narrower than Job 5's first-versus-last single-run ratios. Job 6 uses the matched estimator declared in its brief.
- k11 against r15d was **MEASURED** for both CPU and wall under that rule. All 12 blocks favored k11, and pooled CPU was **5.43% lower**. Piece 11 against k10 was **not measurable here** under the same rule.
- The main sampled reductions in estimated CPU seconds per profiled run were move generation and legality, NNUE evaluation, and board updates. Search trace identity held throughout the timings, control and clean profiles.

## Suspicions

- The stack's move-generation and board-update work is consistent with the direction of the matched profiles. The function families and subsystem totals reflect the rewritten call structure. The timings establish the overall result, and the profiles estimate its distribution.

## What I did not do

All executions used cloud scratch trees. Owner-PC profiling, Clang PGO measurements and strength testing were outside this run.

## What I am not sure about

The identical-binary floor measures this session's cloud noise. The owner-PC magnitude with its Clang PGO build and training net remains unverified. Sampling and symbol matching can move apparent subsystem CPU between adjacent stages.

GPT-6 (Codex), Case A. [Clock stamps](sol2/job6/stamps.txt) · [Publication status and file layout](sol2/job6/publication-layout.raw.txt)
