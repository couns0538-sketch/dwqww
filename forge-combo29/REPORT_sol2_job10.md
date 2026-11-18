# sol2 — Job 10 consolidated Forge stack at 20,000 nodes per move

## Step 0 — the frozen builds and default node gates passed

| Frozen executable | SHA-256 | Fresh-process bench 11 | Bench 13 | Startpos perft 5 |
|---|---|---:|---:|---:|
| r15d-pgo | `96f50b3eb6d4f05cfa8291eaab56ea9c943a8e98fb3b248fff3b9138fcce6808` | 312,866 | 862,329 | 4,865,609 |
| kF-pgo | `90413337a79410b49b76cbec4b2e1a77344bcc2385fecd5950f1f2ababd1539a` | 312,866 | 862,329 | 4,865,609 |

These checks used the saved Job 9 builds with zero UCI option overrides. The counts for all 20 startpos perft root moves also matched byte for byte. The toolchain was GCC 14.2.0, libstdc++ 6.0.33 and glibc 2.41, with CMake Release, C++20, `-O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4`, `-flto` and private profiles from the same 20-game training set. [Frozen receipts](sol2/job10/step0-frozen-identities.raw.txt) · [r15d raw pins](sol2/job10/step0-r15d-pgo-pins.raw.txt) · [kF raw pins](sol2/job10/step0-kF-pgo-pins.raw.txt) · [Earlier build evidence](REPORT_sol2_job9.md)

## Known answer — both engines matched per search

| Fixed-node gate | Games | Searches | Last-info nodes | Trace |
|---|---:|---:|---:|---|
| r15d-pgo | 12 | 1,373 | 15,527,588 | `73ecbb5eedc59271` |
| kF-pgo | 12 | 1,373 | 15,527,588 | `73ecbb5eedc59271` |

The two fresh single-threaded engine processes each used one pinned logical CPU, PC20, Hash 16 MiB, OwnBook false and synthetic v3 net768 SHA-256 `c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7`. Both drivers replayed the first 12 saved eight-ply histories from Job 9 in their original order, with a 300-ply ceiling. The selected opening file SHA-256 was `d07657cf96b59bde3303ed8aa0950dea55c91c64082c3b80e599295c60a6ed9d`. The original turn, board and castling keys were checked by replay. [Saved Job 9 openings](sol2/job9/kF-timing-openings.txt) · [Selected openings](sol2/job10/fixed-openings.txt) · [Workload hashes](sol2/job10/workload-pins.raw.txt)

The derived fixed-node driver SHA-256 was `662799e637da4c5d44dde7a8f846396fbacb7f208da62e6f3cddd268f3c9a022`. The wire readback found 1,374 exact `go nodes 20000` commands per process, including the single internal driver warm-up. It checked every sent move history and the net activation. The per-search records agreed on game, ply, best move, last-info nodes and last-info score in order. The node total comes from the last reported completed iteration of each search. The known answer was pinned before the timed campaigns, which omitted the gate-only wire and per-search recording. [Derivation](sol2/job10/derive_fixed_driver.py.txt) · [Fixed-node driver](sol2/job10/fixed_nodes_driver.py.txt) · [Known answer](sol2/job10/known-answer.txt) · [Gate verification](sol2/job10/gate-readback.raw.txt) · [Gate commands](sol2/job10/gate-commands.raw.txt)

## Prediction graded

The prediction was published alone at `73ca579757411fa652f49d5d7cc5edd57a31d07b` after the two-engine known answer and before any timed run.

| Quantity | Prediction | Observed | Observed minus predicted |
|---|---:|---:|---:|
| Identical-binary CPU minimum | 0.960 | 0.9309 | -0.0291 |
| Identical-binary CPU maximum | 1.052 | 1.0353 | -0.0167 |
| Pooled kF-pgo/r15d-pgo CPU | 0.917 | 0.9224 | +0.0054 |
| CPU blocks below one | 12/12 | 12/12 | +0 blocks |

[Original prediction](sol2/job10/prediction.txt) · [UTC checkpoints](sol2/job10/stamps.txt)

## Steps 1–2 — balanced timing and decision

Odd blocks used A B B A and even blocks B A A B. Each block started with a recorded full run of its first arm as a warm-up. All runs used a fresh engine pinned to logical CPU 2. The warm-up passed the same identity gates and was excluded from the ratios. The separate internal driver warm-up was part of every full invocation. The control used r15d at two distinct paths, with matching hashes and a byte-identical `cmp`. [Control copy](sol2/job10/step1-copy.raw.txt) · [Harness](sol2/job10/balanced_timing.py.txt) · [Arithmetic fixture](sol2/job10/runner-fixture.raw.txt) · [Independent readback](sol2/job10/timing_readback.py.txt)

Each block ratio divides summed B times by summed A times for its four timed runs. The pooled ratio uses summed durations by arm across complete blocks. Engine CPU is a reaped child's user plus system time. Wall covers the full driver call. The declared decision requires the candidate median outside the entire 12-block control range and at least 10 of 12 blocks on the same side of one. Position means normalize each timed leg by its block mean before averaging within each parity cohort.

Job 10 uses PC20, Threads 1, Hash 16 MiB, net768 and `go nodes 20000`. Each eligible run uses 12 openings and records 1,373 searches, 15,527,588 last-iteration nodes and trace `73ecbb5eedc59271`. [Known answer](sol2/job10/known-answer.txt) · [Openings](sol2/job10/fixed-openings.txt)

### Step 1 — identical-binary fixed-node floor

B/A compares `copy` (`96f50b3eb6d4f05cfa8291eaab56ea9c943a8e98fb3b248fff3b9138fcce6808`) with `r15d-pgo` (`96f50b3eb6d4f05cfa8291eaab56ea9c943a8e98fb3b248fff3b9138fcce6808`).

| Block | Leg | Engine | CPU (s) | Wall (s) | Trace | Exit | In ratios |
|---:|---|---|---:|---:|---|---:|---|
| 1 | Warm-up | r15d-pgo | 17.198 | 17.531 | `73ecbb5eedc59271` | 0 | no |
| 1 | 1 | r15d-pgo | 17.102 | 17.444 | `73ecbb5eedc59271` | 0 | yes |
| 1 | 2 | copy | 15.158 | 15.438 | `73ecbb5eedc59271` | 0 | yes |
| 1 | 3 | copy | 16.052 | 16.343 | `73ecbb5eedc59271` | 0 | yes |
| 1 | 4 | r15d-pgo | 16.424 | 16.734 | `73ecbb5eedc59271` | 0 | yes |
| 2 | Warm-up | copy | 16.696 | 17.001 | `73ecbb5eedc59271` | 0 | no |
| 2 | 1 | copy | 16.550 | 16.854 | `73ecbb5eedc59271` | 0 | yes |
| 2 | 2 | r15d-pgo | 17.239 | 17.563 | `73ecbb5eedc59271` | 0 | yes |
| 2 | 3 | r15d-pgo | 15.920 | 16.208 | `73ecbb5eedc59271` | 0 | yes |
| 2 | 4 | copy | 15.768 | 16.039 | `73ecbb5eedc59271` | 0 | yes |
| 3 | Warm-up | r15d-pgo | 15.675 | 15.958 | `73ecbb5eedc59271` | 0 | no |
| 3 | 1 | r15d-pgo | 16.471 | 16.765 | `73ecbb5eedc59271` | 0 | yes |
| 3 | 2 | copy | 17.012 | 17.320 | `73ecbb5eedc59271` | 0 | yes |
| 3 | 3 | copy | 16.543 | 16.861 | `73ecbb5eedc59271` | 0 | yes |
| 3 | 4 | r15d-pgo | 16.471 | 16.769 | `73ecbb5eedc59271` | 0 | yes |
| 4 | Warm-up | copy | 17.348 | 17.650 | `73ecbb5eedc59271` | 0 | no |
| 4 | 1 | copy | 15.846 | 16.118 | `73ecbb5eedc59271` | 0 | yes |
| 4 | 2 | r15d-pgo | 16.432 | 16.718 | `73ecbb5eedc59271` | 0 | yes |
| 4 | 3 | r15d-pgo | 15.749 | 16.014 | `73ecbb5eedc59271` | 0 | yes |
| 4 | 4 | copy | 16.789 | 17.094 | `73ecbb5eedc59271` | 0 | yes |
| 5 | Warm-up | r15d-pgo | 16.293 | 16.589 | `73ecbb5eedc59271` | 0 | no |
| 5 | 1 | r15d-pgo | 16.235 | 16.511 | `73ecbb5eedc59271` | 0 | yes |
| 5 | 2 | copy | 15.704 | 15.981 | `73ecbb5eedc59271` | 0 | yes |
| 5 | 3 | copy | 16.469 | 16.774 | `73ecbb5eedc59271` | 0 | yes |
| 5 | 4 | r15d-pgo | 16.072 | 16.348 | `73ecbb5eedc59271` | 0 | yes |
| 6 | Warm-up | copy | 16.850 | 17.165 | `73ecbb5eedc59271` | 0 | no |
| 6 | 1 | copy | 15.523 | 15.783 | `73ecbb5eedc59271` | 0 | yes |
| 6 | 2 | r15d-pgo | 17.171 | 17.484 | `73ecbb5eedc59271` | 0 | yes |
| 6 | 3 | r15d-pgo | 15.867 | 16.132 | `73ecbb5eedc59271` | 0 | yes |
| 6 | 4 | copy | 15.978 | 16.245 | `73ecbb5eedc59271` | 0 | yes |
| 7 | Warm-up | r15d-pgo | 16.180 | 16.446 | `73ecbb5eedc59271` | 0 | no |
| 7 | 1 | r15d-pgo | 15.606 | 15.863 | `73ecbb5eedc59271` | 0 | yes |
| 7 | 2 | copy | 15.786 | 16.064 | `73ecbb5eedc59271` | 0 | yes |
| 7 | 3 | copy | 16.324 | 16.611 | `73ecbb5eedc59271` | 0 | yes |
| 7 | 4 | r15d-pgo | 16.916 | 17.218 | `73ecbb5eedc59271` | 0 | yes |
| 8 | Warm-up | copy | 16.085 | 16.347 | `73ecbb5eedc59271` | 0 | no |
| 8 | 1 | copy | 16.138 | 16.411 | `73ecbb5eedc59271` | 0 | yes |
| 8 | 2 | r15d-pgo | 16.162 | 16.448 | `73ecbb5eedc59271` | 0 | yes |
| 8 | 3 | r15d-pgo | 15.746 | 16.003 | `73ecbb5eedc59271` | 0 | yes |
| 8 | 4 | copy | 15.468 | 15.727 | `73ecbb5eedc59271` | 0 | yes |
| 9 | Warm-up | r15d-pgo | 16.173 | 16.471 | `73ecbb5eedc59271` | 0 | no |
| 9 | 1 | r15d-pgo | 16.431 | 16.705 | `73ecbb5eedc59271` | 0 | yes |
| 9 | 2 | copy | 15.780 | 16.055 | `73ecbb5eedc59271` | 0 | yes |
| 9 | 3 | copy | 15.645 | 15.935 | `73ecbb5eedc59271` | 0 | yes |
| 9 | 4 | r15d-pgo | 15.785 | 16.066 | `73ecbb5eedc59271` | 0 | yes |
| 10 | Warm-up | copy | 16.002 | 16.273 | `73ecbb5eedc59271` | 0 | no |
| 10 | 1 | copy | 15.818 | 16.108 | `73ecbb5eedc59271` | 0 | yes |
| 10 | 2 | r15d-pgo | 16.739 | 17.043 | `73ecbb5eedc59271` | 0 | yes |
| 10 | 3 | r15d-pgo | 15.757 | 16.024 | `73ecbb5eedc59271` | 0 | yes |
| 10 | 4 | copy | 15.097 | 15.350 | `73ecbb5eedc59271` | 0 | yes |
| 11 | Warm-up | r15d-pgo | 15.819 | 16.083 | `73ecbb5eedc59271` | 0 | no |
| 11 | 1 | r15d-pgo | 15.667 | 15.938 | `73ecbb5eedc59271` | 0 | yes |
| 11 | 2 | copy | 15.879 | 16.165 | `73ecbb5eedc59271` | 0 | yes |
| 11 | 3 | copy | 15.528 | 15.783 | `73ecbb5eedc59271` | 0 | yes |
| 11 | 4 | r15d-pgo | 16.285 | 16.564 | `73ecbb5eedc59271` | 0 | yes |
| 12 | Warm-up | copy | 15.269 | 15.535 | `73ecbb5eedc59271` | 0 | no |
| 12 | 1 | copy | 15.520 | 15.788 | `73ecbb5eedc59271` | 0 | yes |
| 12 | 2 | r15d-pgo | 15.210 | 15.457 | `73ecbb5eedc59271` | 0 | yes |
| 12 | 3 | r15d-pgo | 15.571 | 15.871 | `73ecbb5eedc59271` | 0 | yes |
| 12 | 4 | copy | 16.348 | 16.627 | `73ecbb5eedc59271` | 0 | yes |

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9309 | 0.9299 |
| 2 | BAAB | 0.9746 | 0.9740 |
| 3 | ABBA | 1.0186 | 1.0193 |
| 4 | BAAB | 1.0141 | 1.0147 |
| 5 | ABBA | 0.9959 | 0.9968 |
| 6 | BAAB | 0.9535 | 0.9528 |
| 7 | ABBA | 0.9873 | 0.9877 |
| 8 | BAAB | 0.9905 | 0.9904 |
| 9 | ABBA | 0.9755 | 0.9761 |
| 10 | BAAB | 0.9514 | 0.9513 |
| 11 | ABBA | 0.9830 | 0.9830 |
| 12 | BAAB | 1.0353 | 1.0347 |

| Metric | Median | Pooled | Block range | Below 1 | Above 1 | Reading |
|---|---:|---:|---:|---:|---:|---|
| Engine CPU | 0.9851 | 0.9838 | 0.9309–1.0353 | 9/12 | 3/12 | Identical-binary floor |
| Wall | 0.9854 | 0.9838 | 0.9299–1.0347 | 9/12 | 3/12 | Identical-binary floor |

| Block cohort | Metric | Timed leg 1 | Leg 2 | Leg 3 | Leg 4 |
|---|---|---:|---:|---:|---:|
| Odd (ABBA) | Engine CPU | 1.00704 | 0.98424 | 0.99709 | 1.01163 |
| Odd (ABBA) | Wall | 1.00678 | 0.98428 | 0.99732 | 1.01161 |
| Even (BAAB) | Engine CPU | 0.99268 | 1.02939 | 0.98460 | 0.99333 |
| Even (BAAB) | Wall | 0.99272 | 1.02972 | 0.98455 | 0.99301 |

Each position is divided by the mean of the four timed legs in its block before averaging by cohort.

[Inputs](sol2/job10/step1/inputs.txt) · [Raw runs](sol2/job10/step1/runs.jsonl.txt) · [Summary](sol2/job10/step1/summary.txt) · [Command](sol2/job10/step1-command.raw.txt)

### Step 2 — kF-pgo against r15d-pgo at 20,000 nodes

B/A compares `kF-pgo` (`90413337a79410b49b76cbec4b2e1a77344bcc2385fecd5950f1f2ababd1539a`) with `r15d-pgo` (`96f50b3eb6d4f05cfa8291eaab56ea9c943a8e98fb3b248fff3b9138fcce6808`).

| Block | Leg | Engine | CPU (s) | Wall (s) | Trace | Exit | In ratios |
|---:|---|---|---:|---:|---|---:|---|
| 1 | Warm-up | r15d-pgo | 16.316 | 16.577 | `73ecbb5eedc59271` | 0 | no |
| 1 | 1 | r15d-pgo | 16.184 | 16.458 | `73ecbb5eedc59271` | 0 | yes |
| 1 | 2 | kF-pgo | 14.835 | 15.095 | `73ecbb5eedc59271` | 0 | yes |
| 1 | 3 | kF-pgo | 14.378 | 14.627 | `73ecbb5eedc59271` | 0 | yes |
| 1 | 4 | r15d-pgo | 17.801 | 18.143 | `73ecbb5eedc59271` | 0 | yes |
| 2 | Warm-up | kF-pgo | 15.287 | 15.566 | `73ecbb5eedc59271` | 0 | no |
| 2 | 1 | kF-pgo | 14.946 | 15.211 | `73ecbb5eedc59271` | 0 | yes |
| 2 | 2 | r15d-pgo | 16.313 | 16.586 | `73ecbb5eedc59271` | 0 | yes |
| 2 | 3 | r15d-pgo | 17.894 | 18.232 | `73ecbb5eedc59271` | 0 | yes |
| 2 | 4 | kF-pgo | 16.191 | 16.505 | `73ecbb5eedc59271` | 0 | yes |
| 3 | Warm-up | r15d-pgo | 18.334 | 18.696 | `73ecbb5eedc59271` | 0 | no |
| 3 | 1 | r15d-pgo | 16.163 | 16.415 | `73ecbb5eedc59271` | 0 | yes |
| 3 | 2 | kF-pgo | 14.305 | 14.546 | `73ecbb5eedc59271` | 0 | yes |
| 3 | 3 | kF-pgo | 15.339 | 15.643 | `73ecbb5eedc59271` | 0 | yes |
| 3 | 4 | r15d-pgo | 15.188 | 15.425 | `73ecbb5eedc59271` | 0 | yes |
| 4 | Warm-up | kF-pgo | 13.769 | 13.989 | `73ecbb5eedc59271` | 0 | no |
| 4 | 1 | kF-pgo | 14.556 | 14.806 | `73ecbb5eedc59271` | 0 | yes |
| 4 | 2 | r15d-pgo | 16.667 | 16.983 | `73ecbb5eedc59271` | 0 | yes |
| 4 | 3 | r15d-pgo | 16.791 | 17.081 | `73ecbb5eedc59271` | 0 | yes |
| 4 | 4 | kF-pgo | 14.135 | 14.384 | `73ecbb5eedc59271` | 0 | yes |
| 5 | Warm-up | r15d-pgo | 15.956 | 16.238 | `73ecbb5eedc59271` | 0 | no |
| 5 | 1 | r15d-pgo | 15.580 | 15.829 | `73ecbb5eedc59271` | 0 | yes |
| 5 | 2 | kF-pgo | 14.576 | 14.823 | `73ecbb5eedc59271` | 0 | yes |
| 5 | 3 | kF-pgo | 14.905 | 15.182 | `73ecbb5eedc59271` | 0 | yes |
| 5 | 4 | r15d-pgo | 16.669 | 16.961 | `73ecbb5eedc59271` | 0 | yes |
| 6 | Warm-up | kF-pgo | 14.080 | 14.314 | `73ecbb5eedc59271` | 0 | no |
| 6 | 1 | kF-pgo | 14.457 | 14.710 | `73ecbb5eedc59271` | 0 | yes |
| 6 | 2 | r15d-pgo | 15.439 | 15.694 | `73ecbb5eedc59271` | 0 | yes |
| 6 | 3 | r15d-pgo | 15.274 | 15.535 | `73ecbb5eedc59271` | 0 | yes |
| 6 | 4 | kF-pgo | 14.107 | 14.348 | `73ecbb5eedc59271` | 0 | yes |
| 7 | Warm-up | r15d-pgo | 15.496 | 15.765 | `73ecbb5eedc59271` | 0 | no |
| 7 | 1 | r15d-pgo | 15.849 | 16.128 | `73ecbb5eedc59271` | 0 | yes |
| 7 | 2 | kF-pgo | 14.629 | 14.886 | `73ecbb5eedc59271` | 0 | yes |
| 7 | 3 | kF-pgo | 14.569 | 14.829 | `73ecbb5eedc59271` | 0 | yes |
| 7 | 4 | r15d-pgo | 15.866 | 16.135 | `73ecbb5eedc59271` | 0 | yes |
| 8 | Warm-up | kF-pgo | 13.913 | 14.154 | `73ecbb5eedc59271` | 0 | no |
| 8 | 1 | kF-pgo | 14.867 | 15.133 | `73ecbb5eedc59271` | 0 | yes |
| 8 | 2 | r15d-pgo | 15.888 | 16.149 | `73ecbb5eedc59271` | 0 | yes |
| 8 | 3 | r15d-pgo | 16.466 | 16.763 | `73ecbb5eedc59271` | 0 | yes |
| 8 | 4 | kF-pgo | 15.754 | 16.078 | `73ecbb5eedc59271` | 0 | yes |
| 9 | Warm-up | r15d-pgo | 16.727 | 17.034 | `73ecbb5eedc59271` | 0 | no |
| 9 | 1 | r15d-pgo | 15.472 | 15.724 | `73ecbb5eedc59271` | 0 | yes |
| 9 | 2 | kF-pgo | 14.835 | 15.101 | `73ecbb5eedc59271` | 0 | yes |
| 9 | 3 | kF-pgo | 15.084 | 15.353 | `73ecbb5eedc59271` | 0 | yes |
| 9 | 4 | r15d-pgo | 16.456 | 16.756 | `73ecbb5eedc59271` | 0 | yes |
| 10 | Warm-up | kF-pgo | 14.615 | 14.862 | `73ecbb5eedc59271` | 0 | no |
| 10 | 1 | kF-pgo | 13.922 | 14.149 | `73ecbb5eedc59271` | 0 | yes |
| 10 | 2 | r15d-pgo | 15.194 | 15.441 | `73ecbb5eedc59271` | 0 | yes |
| 10 | 3 | r15d-pgo | 15.799 | 16.069 | `73ecbb5eedc59271` | 0 | yes |
| 10 | 4 | kF-pgo | 15.759 | 16.051 | `73ecbb5eedc59271` | 0 | yes |
| 11 | Warm-up | r15d-pgo | 18.873 | 19.251 | `73ecbb5eedc59271` | 0 | no |
| 11 | 1 | r15d-pgo | 16.391 | 16.676 | `73ecbb5eedc59271` | 0 | yes |
| 11 | 2 | kF-pgo | 14.817 | 15.093 | `73ecbb5eedc59271` | 0 | yes |
| 11 | 3 | kF-pgo | 15.586 | 15.892 | `73ecbb5eedc59271` | 0 | yes |
| 11 | 4 | r15d-pgo | 16.384 | 16.673 | `73ecbb5eedc59271` | 0 | yes |
| 12 | Warm-up | kF-pgo | 14.875 | 15.145 | `73ecbb5eedc59271` | 0 | no |
| 12 | 1 | kF-pgo | 15.611 | 15.902 | `73ecbb5eedc59271` | 0 | yes |
| 12 | 2 | r15d-pgo | 16.028 | 16.313 | `73ecbb5eedc59271` | 0 | yes |
| 12 | 3 | r15d-pgo | 14.995 | 15.228 | `73ecbb5eedc59271` | 0 | yes |
| 12 | 4 | kF-pgo | 14.595 | 14.855 | `73ecbb5eedc59271` | 0 | yes |

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.8596 | 0.8590 |
| 2 | BAAB | 0.9102 | 0.9109 |
| 3 | ABBA | 0.9455 | 0.9481 |
| 4 | BAAB | 0.8575 | 0.8569 |
| 5 | ABBA | 0.9142 | 0.9151 |
| 6 | BAAB | 0.9300 | 0.9305 |
| 7 | ABBA | 0.9207 | 0.9210 |
| 8 | BAAB | 0.9464 | 0.9483 |
| 9 | ABBA | 0.9371 | 0.9376 |
| 10 | BAAB | 0.9577 | 0.9584 |
| 11 | ABBA | 0.9276 | 0.9291 |
| 12 | BAAB | 0.9737 | 0.9751 |

| Metric | Median | Pooled | Block range | Below 1 | Above 1 | Reading |
|---|---:|---:|---:|---:|---:|---|
| Engine CPU | 0.9288 | 0.9224 | 0.8575–0.9737 | 12/12 | 0/12 | MEASURED |
| Wall | 0.9298 | 0.9232 | 0.8569–0.9751 | 12/12 | 0/12 | MEASURED |

| Block cohort | Metric | Timed leg 1 | Leg 2 | Leg 3 | Leg 4 |
|---|---|---:|---:|---:|---:|
| Odd (ABBA) | Engine CPU | 1.02883 | 0.94663 | 0.96681 | 1.05772 |
| Odd (ABBA) | Wall | 1.02792 | 0.94664 | 0.96772 | 1.05772 |
| Even (BAAB) | Engine CPU | 0.95155 | 1.02851 | 1.04564 | 0.97430 |
| Even (BAAB) | Wall | 0.95148 | 1.02800 | 1.04534 | 0.97518 |

Each position is divided by the mean of the four timed legs in its block before averaging by cohort.

[Inputs](sol2/job10/step2/inputs.txt) · [Raw runs](sol2/job10/step2/runs.jsonl.txt) · [Summary](sol2/job10/step2/summary.txt) · [Command](sol2/job10/step2-command.raw.txt)

### kF-pgo against r15d-pgo on both workloads

| Metric | Job 9 Step 3, softnodes 2000 | Job 10 Step 2, nodes 20000 |
|---|---:|---:|
| Games per run | 60 | 12 |
| Searches per run | 8,612 | 1,373 |
| Last-iteration nodes per run | 29,333,343 | 15,527,588 |
| Trace | `5c705841c3ea17b4` | `73ecbb5eedc59271` |
| Engine CPU floor range | 0.9640–1.0485 | 0.9309–1.0353 |
| Engine CPU block median | 0.9142 | 0.9288 |
| Engine CPU pooled B/A | 0.9165 | 0.9224 |
| Engine CPU blocks below 1 | 12/12 | 12/12 |
| Engine CPU reading | MEASURED | MEASURED |
| Wall floor range | 0.9639–1.0494 | 0.9299–1.0347 |
| Wall block median | 0.9156 | 0.9298 |
| Wall pooled B/A | 0.9184 | 0.9232 |
| Wall blocks below 1 | 12/12 | 12/12 |
| Wall reading | MEASURED | MEASURED |

Both sessions used the same two executable hashes and workload-specific floors. The fixed-node session uses the first 12 of the 60 openings from Job 9. [Job 9 raw comparison](sol2/job9/step3/runs.jsonl.txt) · [Job 10 raw comparison](sol2/job10/step2/runs.jsonl.txt)


## Facts

- The readback reconciled 96 eligible timed runs and 24 first-arm warm-ups from complete blocks. Every eligible run matched 1,373 searches, 15,527,588 last-info nodes and trace `73ecbb5eedc59271`. [Readback script](sol2/job10/timing_readback.py.txt)
- The fixed-node r15d copy control had a CPU block range of 0.9309–1.0353, a median of 0.9851, a pooled ratio of 0.9838, and 9/12 blocks below one. [Control summary](sol2/job10/step1/summary.txt)
- The consolidated stack used **7.76% less engine CPU** and **7.68% less wall time** pooled. It used less CPU in 12 of 12 blocks. The readings were **MEASURED** for CPU and **MEASURED** for wall. The medians were 0.00209 CPU and 0.00009 wall below their lower control endpoints. [Comparison summary](sol2/job10/step2/summary.txt)


## Suspicions

The two workloads differ in node command, opening count, and which games run. The side-by-side table gives the observed stack effect on each workload. It leaves the separate effects of node command and opening mix unresolved.

## What this check cannot see

More than one thread, Hash sizes other than 16, a game clock, the PC's own net, compiler (clang with ThinLTO and a
profile from self-play) and processor, and two games played at once on one machine (the PC plays 8 at once).

## What I did not do

The experiment used the two existing cloud executables, synthetic net768, and one engine process at a time. The archived evidence is text. [Publication layout](sol2/job10/publication-layout.raw.txt)

## What I am not sure about

The gain in the owner's eight-game training loop remains unknown. The trace covers game, ply, best move, last-info nodes and last-info score. The engine's internal node visitation order is beyond that signature's coverage.
