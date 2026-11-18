# sol2 — Job 5 twelve-piece stack on warm self-play

## Step 0 — pinned r15d passed

The r15d executable SHA-256 remained `bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6`. Fresh processes reproduced **312,866** for `bench 11`, **862,329** for `bench 13` and **4,865,609** for startpos `go perft 5`, with embedded AL1 s198, Threads 1, Hash 16 MiB, MultiPV 1 and OwnBook false. [Identity](sol2/job5/step0-identity.raw.txt) · [Raw pins](sol2/job5/step0-pins.raw.txt)

## Step 1 — all patches and warm traces passed

I read and verified all twelve patches from Carbon2's commit `ba2de7672095eb0306b3d8d9a7d1bc1b15cae32c`. Each SHA prefix matched. Every patch applied to a separate r15d working tree with `patch -p1 -F0`, zero fuzz and zero offsets. The rebuilds used the same GCC 14.2.0, libstdc++ 6.0.33, glibc 2.41, CMake Release, x86-64-v4, strict FP and v3 AVX-512 flags as r15d. These builds use neither LTO nor PGO. [Source hashes and paths](sol2/job5/step1-source-receipt.raw.txt) · [Patch and build commands](sol2/job5/step1-patch-build-gate.raw.txt) · [k10 compile/link](sol2/job5/k10-build.raw.txt) · [k11 compile/link](sol2/job5/k11-build.raw.txt) · [k12 compile/link](sol2/job5/k12-build.raw.txt)

| Build | SHA-256 | Sol3 hash |
|---|---|---|
| k10 | `55fed57fadf76d5e861da3f9bf3601b43c6bf67e6d152d87edfcf648e26207ae` | Matches |
| k11 | `a7a34a148b40c14e5ea960dd2d3182fceef7023a38d12db47c2521a430fc1ea5` | Matches |
| k12 | `9b50324e42ea8fe42f3246149d7389726f8994650080790349018e956d60eca7` | New reference |

All three builds returned **8,612 searches, 29,333,343 last-info nodes and trace `5c705841c3ea17b4`**. This is the common workload for the timing and profile tables below. It uses Carbon2's driver, 60 startpos games with eight random plies, seed `20261117`, a 300-ply cap, PC20, Threads 1, Hash 16 MiB and `go softnodes 2000`. The synthetic standalone net768 checksum is `30ab43b4ba5db5f3` (SHA-256 `c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7`). Engine and driver used logical CPU 2 of the cloud AMD EPYC 9V74 VM. [Hash and trace readback](sol2/job5/step1-readback.raw.txt) · [k10 warm output](sol2/job5/k10-identity.raw.txt) · [k11 warm output](sol2/job5/k11-identity.raw.txt) · [k12 warm output](sol2/job5/k12-identity.raw.txt)

## Prediction grade

The standalone commit `e023d0f` preceded all ABBA passes and sampled runs. Pooled k12/r15d engine CPU was **0.9524** against **0.9400** predicted. All three predicted k12 hotspots appeared in the top three. Two of the three predicted declines appeared among the largest exclusive decreases by exact symbol. The third predicted function, `Worker::corrected_eval`, moved from **4.32% to 4.13%**. The raw ranking lists the old `Board::make_move`, `MovePicker::next` and old `MovePicker::pick_best` symbols largest first. `Board::make_move` now takes precomputed move data and appears at **2.12%** under its new signature, versus **4.33%** for the old one. `pick_best_scored` appears at **3.53%**, versus **3.52%** for its `pick_best` predecessor. Changes to symbol boundaries matter when grading these shares. [Prediction](sol2/job5/prediction.txt) · [Exact-symbol comparison](sol2/job5/step3/all-symbol-deltas.raw.tsv.txt)

## Step 2 — balanced timing and same-build spread

All 24 fresh-process runs completed with the pinned warm trace. Engine CPU is reaped Forge user plus system time. Wall covers the full driver and includes opening generation, engine setup and exit. Within each ABBA block, the k12/r15d ratio divides the mean of both k12 legs by the mean of both r15d legs. The same-build ratio divides the first r15d leg by the last. [Executed command and prediction checkpoint](sol2/job5/step2-command.raw.txt) · [All raw timing rows](sol2/job5/step2/runs.jsonl.txt) · [Block statistics](sol2/job5/step2/summary.txt) · [Independent timing arithmetic](sol2/job5/abba-readback.raw.txt)

| Block | Leg | Build | Engine CPU (s) | Wall (s) | Trace |
|---:|---:|---|---:|---:|---|
| 1 | 1 | r15d | 22.367 | 23.296 | `5c705841c3ea17b4` |
| 1 | 2 | k12 | 21.158 | 22.097 | `5c705841c3ea17b4` |
| 1 | 3 | k12 | 19.087 | 19.886 | `5c705841c3ea17b4` |
| 1 | 4 | r15d | 19.097 | 19.855 | `5c705841c3ea17b4` |
| 2 | 1 | r15d | 19.899 | 20.701 | `5c705841c3ea17b4` |
| 2 | 2 | k12 | 18.904 | 19.716 | `5c705841c3ea17b4` |
| 2 | 3 | k12 | 18.720 | 19.500 | `5c705841c3ea17b4` |
| 2 | 4 | r15d | 19.464 | 20.243 | `5c705841c3ea17b4` |
| 3 | 1 | r15d | 19.627 | 20.407 | `5c705841c3ea17b4` |
| 3 | 2 | k12 | 18.488 | 19.242 | `5c705841c3ea17b4` |
| 3 | 3 | k12 | 17.993 | 18.725 | `5c705841c3ea17b4` |
| 3 | 4 | r15d | 19.019 | 19.769 | `5c705841c3ea17b4` |
| 4 | 1 | r15d | 19.431 | 20.208 | `5c705841c3ea17b4` |
| 4 | 2 | k12 | 19.112 | 19.903 | `5c705841c3ea17b4` |
| 4 | 3 | k12 | 18.146 | 18.880 | `5c705841c3ea17b4` |
| 4 | 4 | r15d | 20.017 | 20.821 | `5c705841c3ea17b4` |
| 5 | 1 | r15d | 19.522 | 20.304 | `5c705841c3ea17b4` |
| 5 | 2 | k12 | 19.066 | 19.849 | `5c705841c3ea17b4` |
| 5 | 3 | k12 | 20.002 | 20.875 | `5c705841c3ea17b4` |
| 5 | 4 | r15d | 20.930 | 21.780 | `5c705841c3ea17b4` |
| 6 | 1 | r15d | 20.570 | 21.425 | `5c705841c3ea17b4` |
| 6 | 2 | k12 | 18.377 | 19.139 | `5c705841c3ea17b4` |
| 6 | 3 | k12 | 18.202 | 18.961 | `5c705841c3ea17b4` |
| 6 | 4 | r15d | 18.674 | 19.400 | `5c705841c3ea17b4` |

| Block | k12/r15d CPU | r15d A/A CPU | k12/r15d wall | r15d A/A wall |
|---:|---:|---:|---:|---:|
| 1 | 0.9706 | 1.1712 | 0.9729 | 1.1733 |
| 2 | 0.9558 | 1.0224 | 0.9578 | 1.0226 |
| 3 | 0.9440 | 1.0319 | 0.9450 | 1.0323 |
| 4 | 0.9445 | 0.9708 | 0.9453 | 0.9706 |
| 5 | 0.9658 | 0.9327 | 0.9677 | 0.9323 |
| 6 | 0.9321 | 1.1015 | 0.9332 | 1.1044 |

| Metric | Pooled k12/r15d | Six-block spread | Same-build spread |
|---|---:|---:|---:|
| Engine CPU | 0.9524 | 0.9321–0.9706 | 0.9327–1.1712 |
| Wall | 0.9539 | 0.9332–0.9729 | 0.9323–1.1733 |

All six block estimates point toward lower CPU and wall time for k12. Both pooled ratios fall inside the same-build ranges. A speed effect is **not measurable here** under the brief’s noise rule.

## Step 3 — k12 profile and SEE control

The k12 frame-pointer build uses the same Release flags plus `-g -fno-omit-frame-pointer`, SHA-256 `fb4d1d655663b5ee375d3a4c3ab4c8087426ba6caa112ff9874fe40c58d5cde9`. It reproduced the Step 1 pin before sampling. Job 3's SEE spin applied with zero fuzz and a **93-line offset** to `src/board.cpp`. I saved the rebased text diff. The control moved `Board::see_ge` from **5th, 183 samples (4.27%)** in the first clean run to **1st, 15,129 (72.18%)**, preserving the exact warm trace. [Build and profile commands](sol2/job5/step3/step3-command.raw.txt) · [Frame pointer gate](sol2/job5/step3/frame-pointer-gate.stdout.txt) · [SEE patch](sol2/job5/step3/see-spin.patch.txt) · [Positive control](sol2/job5/step3/positive-control.raw.txt)

I pooled three exact-trace k12 runs with the Job 3 per-thread CPU timer and six-frame sampling method. k12 delivered **13,094** samples and reported **627** timer overruns. The r15d reference uses Job 3's **14,389** samples. Function shares use identical demangled symbols, with a zero where that symbol had no observed samples. Source lines are the modal sampled k12 lines. These are exclusive shares within each profile. They can move with refactoring, compiler inlining and the changed denominator. [k12 raw functions](sol2/job5/step3/pooled.top15.tsv.txt) · [r15d all-function baseline](sol2/job5/step3/r15d-pooled-functions.raw.tsv.txt) · [Job 3 sampling method](REPORT_sol2_job3.md#step-3--warm-profile-and-verified-callers)

| Rank | k12 function | k12 line | k12 samples | r15d share | k12 share |
|---:|---|---|---:|---:|---:|
| 1 | `Worker::search` | `search.cpp:2750` | 1,954 | 14.18% | 14.92% |
| 2 | `TranspositionTable::probe_body<false>` | `search.cpp:492` | 1,233 | 8.29% | 9.42% |
| 3 | `nnue::v3::apply_pair_and_evaluate` | `nnue_v3.cpp:890` | 1,144 | 8.12% | 8.74% |
| 4 | `nnue::v3::refresh_from_pieces` | `nnue_v3.cpp:954` | 807 | 6.19% | 6.16% |
| 5 | `nnue::v3::apply_changes_pair` | `nnue_v3.cpp:855` | 544 | 4.32% | 4.15% |
| 6 | `Worker::corrected_eval` | `search.cpp:1805` | 541 | 4.32% | 4.13% |
| 7 | `Board::see_ge` | `board.cpp:1586` | 517 | 4.33% | 3.95% |
| 8 | `MovePicker::pick_best_scored` | `search.cpp:1075` | 462 | 0.00% | 3.53% |
| 9 | `MovePicker::generate_captures` | `search.cpp:1189` | 439 | 0.00% | 3.35% |
| 10 | `Worker::qsearch` | `search.cpp:2232` | 431 | 3.16% | 3.29% |
| 11 | `MovePicker::generate_quiets` | `search.cpp:1373` | 421 | 0.00% | 3.22% |
| 12 | `Worker::static_evaluate_v3` | `search.cpp:3794` | 385 | 3.13% | 2.94% |
| 13 | `MovePicker::next` | `search.cpp:709` | 341 | 6.24% | 2.60% |
| 14 | `nnue::v3::apply_changes` | `nnue_v3.cpp:841` | 291 | 2.13% | 2.22% |
| 15 | `Board::unmake_move` | `board.cpp:1342` | 278 | 1.66% | 2.12% |

| Subsystem | r15d share | k12 share |
|---|---:|---:|
| Evaluation (NNUE v3) | 27.26% | 27.04% |
| Search control | 20.51% | 20.97% |
| Move ordering and picking | 14.89% | 17.96% |
| Hash table | 10.32% | 11.53% |
| Move generation and legality | 9.84% | 6.97% |
| Board updates and position keys | 7.00% | 5.49% |
| Static exchange evaluation | 3.34% | 3.58% |
| Other runtime and libraries | 3.27% | 2.86% |
| Draw and repetition checks | 3.02% | 2.83% |
| Other engine work | 0.42% | 0.70% |
| UCI and input/output | 0.10% | 0.04% |
| Unresolved | 0.05% | 0.02% |

[Function comparison](sol2/job5/step3/top15-comparison.raw.tsv.txt) · [Subsystem comparison](sol2/job5/step3/subsystem-comparison.raw.tsv.txt)

## Facts

- k10 and k11 reproduced Sol3's binary hashes. All three stack stages, all 24 timed runs, the profile build, the SEE control and all three clean profiles reproduced the pinned warm trace.
- k12 used less CPU and wall time in all six block ratios. The pooled ratios were inside the same-build spread. This cloud experiment therefore leaves the speed effect unresolved under the stated rule.

## Suspicions

- The smaller exclusive shares for move generation and legality and board updates are consistent with the stack targeting that work. Move ordering attribution grew as work shifted across picker functions. Share changes alone cannot establish absolute savings per subsystem.

## What I did not do

The builds, patch application and measurements were confined to cloud scratch space. The owner-PC Clang and self-play PGO build, owner weights, and strength matches were outside this experiment.

## What I am not sure about

The cloud A/A spread is wide and the two warm profiles have timer overruns. GCC and Clang can allocate work differently among inlined and out-of-line symbols. The recorded identity contract uses last-info nodes and best moves for the pinned synthetic-net workload. Its transfer to the owner's full profile and net remains unmeasured.

GPT-6 (Codex), Case A. [Clock stamps](sol2/job5/stamps.txt) · [Publication status and file layout](sol2/job5/publication-layout.raw.txt)
