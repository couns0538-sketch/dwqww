# sol2 — Job 9 alternating timing and consolidated Forge stack

## Step 0 — frozen identities and node gates passed

The saved GCC LTO+PGO executables matched the pinned SHA-256 values. r15d-pgo reproduced **312,866** for `bench 11`, **862,329** for `bench 13` and **4,865,609** for startpos `go perft 5` with a fresh process per command and zero UCI option overrides. [Frozen executable, compiler and library receipts](sol2/job9/step0-frozen-identities.raw.txt) · [Default pins](sol2/job9/step0-r15d-pgo-pins.raw.txt)

| Frozen PGO executable | SHA-256 |
|---|---|
| r15d-pgo | `96f50b3eb6d4f05cfa8291eaab56ea9c943a8e98fb3b248fff3b9138fcce6808` |
| k11v-pgo | `95980ac637b41376245996617d537fd38ef54f223cc93f13673915bfb6f3079c` |
| k13-pgo | `4d7b70e42fc0074ea40c6cf240ebef5701bdd49417d0b18a8e7bd5bf00cf177b` |

The binaries were built with GCC 14.2.0, libstdc++ 6.0.33 and glibc 2.41. The common CMake Release options include C++20, `-O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4`, `-flto` and a private profile for each tree generated from 20 games. The timing driver and synthetic net768 SHA-256 values were `c79b95bf45762fa9869d23140ed7f946cfaf0cb6bc4f74325a18d5f934bf1c45` and `c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7`. [Job 7 recipe and identities](REPORT_sol2_job7.md) · [Job 8 recipe and identities](REPORT_sol2_job8.md)

## Prediction graded

The prediction was published alone at `8951f59cd84b03f3df9eea6aca03825fd2a0ae69` after Step 0 and before any timed run.

| Quantity | Prediction | Observed | Observed minus predicted |
|---|---:|---:|---:|
| Balanced identical-binary CPU minimum | 0.966 | 0.9640 | -0.0020 |
| Balanced identical-binary CPU maximum | 1.044 | 1.0485 | +0.0045 |
| Pooled k13-pgo/k11v-pgo CPU | 0.985 | 0.9894 | +0.0044 |
| k13-pgo/k11v-pgo CPU blocks below 1 | 9/12 | 9/12 | +0 blocks |
| Pooled kF-pgo/r15d-pgo CPU | 0.928 | 0.9165 | -0.0115 |

[Original prediction](sol2/job9/prediction.txt) · [UTC checkpoints](sol2/job9/stamps.txt)

## Steps 1–3 — alternating design and timing

Odd blocks used A B B A and even blocks B A A B. Each block starts with a separate full warm-up run of its first arm. Every run starts a fresh engine pinned to logical CPU 2. The warm-up must pass the same exit and trace gates, is recorded with `warmup: true`, and is excluded from every ratio. The control uses two distinct executable paths with the same SHA-256 and a byte-identical `cmp`. [Control copy](sol2/job9/step1-copy.raw.txt) · [Timing harness](sol2/job9/balanced_timing.py.txt) · [Synthetic arithmetic check](sol2/job9/runner-fixture.raw.txt) · [Independent readback](sol2/job9/timing_readback.py.txt)

Engine CPU is the reaped process's user plus system time. Wall includes the full driver call, including setup, its internal warm-up, and teardown. Each block ratio uses its two timed B durations divided by its two timed A durations. The pooled ratio uses the summed timed durations by arm. The declared decision requires the candidate block median outside the twelve-block control range and at least 10 of 12 blocks on the same side of one. Position means normalize each timed leg by its own block mean before averaging within each parity cohort.

All tables use PC20, Threads 1, Hash 16 MiB, net768, seed 20261117 and `go softnodes 2000`. Each eligible run records 8,612 searches, 29,333,343 nodes and trace `5c705841c3ea17b4`.

### Step 1 — identical-binary alternating floor

B/A compares `copy` (`95980ac637b41376245996617d537fd38ef54f223cc93f13673915bfb6f3079c`) with `k11v-pgo` (`95980ac637b41376245996617d537fd38ef54f223cc93f13673915bfb6f3079c`).

| Block | Leg | Engine | CPU (s) | Wall (s) | Trace | Exit | In ratios |
|---:|---|---|---:|---:|---|---:|---|
| 1 | Warm-up | k11v-pgo | 19.738 | 20.592 | `5c705841c3ea17b4` | 0 | no |
| 1 | 1 | k11v-pgo | 19.158 | 19.991 | `5c705841c3ea17b4` | 0 | yes |
| 1 | 2 | copy | 20.054 | 20.966 | `5c705841c3ea17b4` | 0 | yes |
| 1 | 3 | copy | 18.468 | 19.271 | `5c705841c3ea17b4` | 0 | yes |
| 1 | 4 | k11v-pgo | 18.090 | 18.853 | `5c705841c3ea17b4` | 0 | yes |
| 2 | Warm-up | copy | 17.728 | 18.481 | `5c705841c3ea17b4` | 0 | no |
| 2 | 1 | copy | 17.851 | 18.614 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 2 | k11v-pgo | 18.347 | 19.152 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 3 | k11v-pgo | 18.153 | 18.936 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 4 | copy | 17.364 | 18.100 | `5c705841c3ea17b4` | 0 | yes |
| 3 | Warm-up | k11v-pgo | 18.405 | 19.200 | `5c705841c3ea17b4` | 0 | no |
| 3 | 1 | k11v-pgo | 17.589 | 18.342 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 2 | copy | 18.196 | 18.973 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 3 | copy | 18.650 | 19.492 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 4 | k11v-pgo | 19.295 | 20.128 | `5c705841c3ea17b4` | 0 | yes |
| 4 | Warm-up | copy | 18.255 | 19.026 | `5c705841c3ea17b4` | 0 | no |
| 4 | 1 | copy | 18.383 | 19.147 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 2 | k11v-pgo | 18.270 | 19.038 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 3 | k11v-pgo | 17.560 | 18.276 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 4 | copy | 18.259 | 19.052 | `5c705841c3ea17b4` | 0 | yes |
| 5 | Warm-up | k11v-pgo | 18.288 | 19.053 | `5c705841c3ea17b4` | 0 | no |
| 5 | 1 | k11v-pgo | 19.115 | 19.964 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 2 | copy | 18.782 | 19.603 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 3 | copy | 18.903 | 19.732 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 4 | k11v-pgo | 18.368 | 19.162 | `5c705841c3ea17b4` | 0 | yes |
| 6 | Warm-up | copy | 17.363 | 18.087 | `5c705841c3ea17b4` | 0 | no |
| 6 | 1 | copy | 18.097 | 18.891 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 2 | k11v-pgo | 17.897 | 18.667 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 3 | k11v-pgo | 17.658 | 18.391 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 4 | copy | 17.841 | 18.595 | `5c705841c3ea17b4` | 0 | yes |
| 7 | Warm-up | k11v-pgo | 18.128 | 18.876 | `5c705841c3ea17b4` | 0 | no |
| 7 | 1 | k11v-pgo | 18.350 | 19.120 | `5c705841c3ea17b4` | 0 | yes |
| 7 | 2 | copy | 18.729 | 19.543 | `5c705841c3ea17b4` | 0 | yes |
| 7 | 3 | copy | 18.403 | 19.198 | `5c705841c3ea17b4` | 0 | yes |
| 7 | 4 | k11v-pgo | 20.167 | 21.069 | `5c705841c3ea17b4` | 0 | yes |
| 8 | Warm-up | copy | 20.082 | 20.979 | `5c705841c3ea17b4` | 0 | no |
| 8 | 1 | copy | 18.356 | 19.144 | `5c705841c3ea17b4` | 0 | yes |
| 8 | 2 | k11v-pgo | 17.742 | 18.487 | `5c705841c3ea17b4` | 0 | yes |
| 8 | 3 | k11v-pgo | 17.253 | 17.987 | `5c705841c3ea17b4` | 0 | yes |
| 8 | 4 | copy | 18.335 | 19.133 | `5c705841c3ea17b4` | 0 | yes |
| 9 | Warm-up | k11v-pgo | 18.383 | 19.181 | `5c705841c3ea17b4` | 0 | no |
| 9 | 1 | k11v-pgo | 18.366 | 19.164 | `5c705841c3ea17b4` | 0 | yes |
| 9 | 2 | copy | 17.958 | 18.704 | `5c705841c3ea17b4` | 0 | yes |
| 9 | 3 | copy | 17.823 | 18.589 | `5c705841c3ea17b4` | 0 | yes |
| 9 | 4 | k11v-pgo | 17.482 | 18.222 | `5c705841c3ea17b4` | 0 | yes |
| 10 | Warm-up | copy | 17.653 | 18.360 | `5c705841c3ea17b4` | 0 | no |
| 10 | 1 | copy | 18.064 | 18.800 | `5c705841c3ea17b4` | 0 | yes |
| 10 | 2 | k11v-pgo | 17.655 | 18.392 | `5c705841c3ea17b4` | 0 | yes |
| 10 | 3 | k11v-pgo | 17.590 | 18.332 | `5c705841c3ea17b4` | 0 | yes |
| 10 | 4 | copy | 17.861 | 18.607 | `5c705841c3ea17b4` | 0 | yes |
| 11 | Warm-up | k11v-pgo | 18.157 | 18.933 | `5c705841c3ea17b4` | 0 | no |
| 11 | 1 | k11v-pgo | 19.272 | 20.088 | `5c705841c3ea17b4` | 0 | yes |
| 11 | 2 | copy | 18.576 | 19.382 | `5c705841c3ea17b4` | 0 | yes |
| 11 | 3 | copy | 18.601 | 19.407 | `5c705841c3ea17b4` | 0 | yes |
| 11 | 4 | k11v-pgo | 18.221 | 19.020 | `5c705841c3ea17b4` | 0 | yes |
| 12 | Warm-up | copy | 20.068 | 20.958 | `5c705841c3ea17b4` | 0 | no |
| 12 | 1 | copy | 19.072 | 19.914 | `5c705841c3ea17b4` | 0 | yes |
| 12 | 2 | k11v-pgo | 19.225 | 20.031 | `5c705841c3ea17b4` | 0 | yes |
| 12 | 3 | k11v-pgo | 18.646 | 19.442 | `5c705841c3ea17b4` | 0 | yes |
| 12 | 4 | copy | 18.107 | 18.882 | `5c705841c3ea17b4` | 0 | yes |

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 1.0342 | 1.0359 |
| 2 | BAAB | 0.9648 | 0.9639 |
| 3 | ABBA | 0.9990 | 0.9999 |
| 4 | BAAB | 1.0227 | 1.0237 |
| 5 | ABBA | 1.0054 | 1.0053 |
| 6 | BAAB | 1.0107 | 1.0115 |
| 7 | ABBA | 0.9640 | 0.9640 |
| 8 | BAAB | 1.0485 | 1.0494 |
| 9 | ABBA | 0.9981 | 0.9975 |
| 10 | BAAB | 1.0193 | 1.0186 |
| 11 | ABBA | 0.9916 | 0.9919 |
| 12 | BAAB | 0.9817 | 0.9828 |

| Metric | Median | Pooled | Block range | Below 1 | Above 1 | Reading |
|---|---:|---:|---:|---:|---:|---|
| Engine CPU | 1.0022 | 1.0029 | 0.9640–1.0485 | 6/12 | 6/12 | Identical-binary floor |
| Wall | 1.0026 | 1.0032 | 0.9639–1.0494 | 6/12 | 6/12 | Identical-binary floor |

| Block cohort | Metric | Timed leg 1 | Leg 2 | Leg 3 | Leg 4 |
|---|---|---:|---:|---:|---:|
| Odd (ABBA) | Engine CPU | 1.00184 | 1.00559 | 0.99291 | 0.99966 |
| Odd (ABBA) | Wall | 1.00158 | 1.00564 | 0.99321 | 0.99957 |
| Even (BAAB) | Engine CPU | 1.01313 | 1.00666 | 0.98580 | 0.99441 |
| Even (BAAB) | Wall | 1.01331 | 1.00660 | 0.98548 | 0.99462 |

Each position is divided by the mean of the four timed legs in its block before averaging by cohort.

[Inputs](sol2/job9/step1/inputs.txt) · [Raw runs](sol2/job9/step1/runs.jsonl.txt) · [Summary](sol2/job9/step1/summary.txt) · [Command](sol2/job9/step1-command.raw.txt)

### Step 2 — k13-pgo against k11v-pgo

B/A compares `k13-pgo` (`4d7b70e42fc0074ea40c6cf240ebef5701bdd49417d0b18a8e7bd5bf00cf177b`) with `k11v-pgo` (`95980ac637b41376245996617d537fd38ef54f223cc93f13673915bfb6f3079c`).

| Block | Leg | Engine | CPU (s) | Wall (s) | Trace | Exit | In ratios |
|---:|---|---|---:|---:|---|---:|---|
| 1 | Warm-up | k11v-pgo | 17.779 | 18.543 | `5c705841c3ea17b4` | 0 | no |
| 1 | 1 | k11v-pgo | 19.080 | 19.908 | `5c705841c3ea17b4` | 0 | yes |
| 1 | 2 | k13-pgo | 17.963 | 18.714 | `5c705841c3ea17b4` | 0 | yes |
| 1 | 3 | k13-pgo | 18.369 | 19.185 | `5c705841c3ea17b4` | 0 | yes |
| 1 | 4 | k11v-pgo | 17.841 | 18.580 | `5c705841c3ea17b4` | 0 | yes |
| 2 | Warm-up | k13-pgo | 17.080 | 17.805 | `5c705841c3ea17b4` | 0 | no |
| 2 | 1 | k13-pgo | 17.685 | 18.436 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 2 | k11v-pgo | 17.753 | 18.482 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 3 | k11v-pgo | 17.765 | 18.519 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 4 | k13-pgo | 17.461 | 18.222 | `5c705841c3ea17b4` | 0 | yes |
| 3 | Warm-up | k11v-pgo | 18.155 | 18.926 | `5c705841c3ea17b4` | 0 | no |
| 3 | 1 | k11v-pgo | 18.947 | 19.765 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 2 | k13-pgo | 18.406 | 19.195 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 3 | k13-pgo | 17.090 | 17.803 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 4 | k11v-pgo | 18.961 | 19.781 | `5c705841c3ea17b4` | 0 | yes |
| 4 | Warm-up | k13-pgo | 18.522 | 19.328 | `5c705841c3ea17b4` | 0 | no |
| 4 | 1 | k13-pgo | 17.751 | 18.491 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 2 | k11v-pgo | 18.544 | 19.318 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 3 | k11v-pgo | 17.700 | 18.455 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 4 | k13-pgo | 17.399 | 18.124 | `5c705841c3ea17b4` | 0 | yes |
| 5 | Warm-up | k11v-pgo | 17.841 | 18.595 | `5c705841c3ea17b4` | 0 | no |
| 5 | 1 | k11v-pgo | 18.197 | 18.977 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 2 | k13-pgo | 18.681 | 19.491 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 3 | k13-pgo | 19.094 | 19.941 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 4 | k11v-pgo | 18.405 | 19.203 | `5c705841c3ea17b4` | 0 | yes |
| 6 | Warm-up | k13-pgo | 17.117 | 17.881 | `5c705841c3ea17b4` | 0 | no |
| 6 | 1 | k13-pgo | 17.336 | 18.052 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 2 | k11v-pgo | 18.358 | 19.134 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 3 | k11v-pgo | 16.971 | 17.661 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 4 | k13-pgo | 17.710 | 18.447 | `5c705841c3ea17b4` | 0 | yes |
| 7 | Warm-up | k11v-pgo | 17.858 | 18.612 | `5c705841c3ea17b4` | 0 | no |
| 7 | 1 | k11v-pgo | 18.369 | 19.149 | `5c705841c3ea17b4` | 0 | yes |
| 7 | 2 | k13-pgo | 17.539 | 18.282 | `5c705841c3ea17b4` | 0 | yes |
| 7 | 3 | k13-pgo | 17.782 | 18.543 | `5c705841c3ea17b4` | 0 | yes |
| 7 | 4 | k11v-pgo | 17.834 | 18.619 | `5c705841c3ea17b4` | 0 | yes |
| 8 | Warm-up | k13-pgo | 18.038 | 18.800 | `5c705841c3ea17b4` | 0 | no |
| 8 | 1 | k13-pgo | 16.669 | 17.367 | `5c705841c3ea17b4` | 0 | yes |
| 8 | 2 | k11v-pgo | 17.061 | 17.761 | `5c705841c3ea17b4` | 0 | yes |
| 8 | 3 | k11v-pgo | 18.260 | 19.044 | `5c705841c3ea17b4` | 0 | yes |
| 8 | 4 | k13-pgo | 17.237 | 17.948 | `5c705841c3ea17b4` | 0 | yes |
| 9 | Warm-up | k11v-pgo | 17.684 | 18.425 | `5c705841c3ea17b4` | 0 | no |
| 9 | 1 | k11v-pgo | 19.006 | 19.828 | `5c705841c3ea17b4` | 0 | yes |
| 9 | 2 | k13-pgo | 19.437 | 20.278 | `5c705841c3ea17b4` | 0 | yes |
| 9 | 3 | k13-pgo | 17.140 | 17.873 | `5c705841c3ea17b4` | 0 | yes |
| 9 | 4 | k11v-pgo | 18.195 | 18.956 | `5c705841c3ea17b4` | 0 | yes |
| 10 | Warm-up | k13-pgo | 17.062 | 17.792 | `5c705841c3ea17b4` | 0 | no |
| 10 | 1 | k13-pgo | 17.628 | 18.380 | `5c705841c3ea17b4` | 0 | yes |
| 10 | 2 | k11v-pgo | 17.562 | 18.310 | `5c705841c3ea17b4` | 0 | yes |
| 10 | 3 | k11v-pgo | 17.852 | 18.614 | `5c705841c3ea17b4` | 0 | yes |
| 10 | 4 | k13-pgo | 19.354 | 20.207 | `5c705841c3ea17b4` | 0 | yes |
| 11 | Warm-up | k11v-pgo | 17.773 | 18.531 | `5c705841c3ea17b4` | 0 | no |
| 11 | 1 | k11v-pgo | 18.003 | 18.751 | `5c705841c3ea17b4` | 0 | yes |
| 11 | 2 | k13-pgo | 18.216 | 19.022 | `5c705841c3ea17b4` | 0 | yes |
| 11 | 3 | k13-pgo | 19.317 | 20.156 | `5c705841c3ea17b4` | 0 | yes |
| 11 | 4 | k11v-pgo | 18.881 | 19.677 | `5c705841c3ea17b4` | 0 | yes |
| 12 | Warm-up | k13-pgo | 17.965 | 18.744 | `5c705841c3ea17b4` | 0 | no |
| 12 | 1 | k13-pgo | 18.014 | 18.775 | `5c705841c3ea17b4` | 0 | yes |
| 12 | 2 | k11v-pgo | 18.550 | 19.330 | `5c705841c3ea17b4` | 0 | yes |
| 12 | 3 | k11v-pgo | 18.943 | 19.759 | `5c705841c3ea17b4` | 0 | yes |
| 12 | 4 | k13-pgo | 19.112 | 19.940 | `5c705841c3ea17b4` | 0 | yes |

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9841 | 0.9847 |
| 2 | BAAB | 0.9895 | 0.9907 |
| 3 | ABBA | 0.9364 | 0.9356 |
| 4 | BAAB | 0.9699 | 0.9693 |
| 5 | ABBA | 1.0320 | 1.0328 |
| 6 | BAAB | 0.9920 | 0.9920 |
| 7 | ABBA | 0.9756 | 0.9750 |
| 8 | BAAB | 0.9600 | 0.9595 |
| 9 | ABBA | 0.9832 | 0.9837 |
| 10 | BAAB | 1.0443 | 1.0451 |
| 11 | ABBA | 1.0176 | 1.0195 |
| 12 | BAAB | 0.9902 | 0.9904 |

| Metric | Median | Pooled | Block range | Below 1 | Above 1 | Reading |
|---|---:|---:|---:|---:|---:|---|
| Engine CPU | 0.9868 | 0.9894 | 0.9364–1.0443 | 9/12 | 3/12 | not measurable here |
| Wall | 0.9876 | 0.9897 | 0.9356–1.0451 | 9/12 | 3/12 | not measurable here |

| Block cohort | Metric | Timed leg 1 | Leg 2 | Leg 3 | Leg 4 |
|---|---|---:|---:|---:|---:|
| Odd (ABBA) | Engine CPU | 1.01307 | 1.00039 | 0.98721 | 0.99933 |
| Odd (ABBA) | Wall | 1.01294 | 1.00044 | 0.98753 | 0.99909 |
| Even (BAAB) | Engine CPU | 0.98063 | 1.00630 | 1.00313 | 1.00994 |
| Even (BAAB) | Wall | 0.98046 | 1.00591 | 1.00333 | 1.01031 |

Each position is divided by the mean of the four timed legs in its block before averaging by cohort.

[Inputs](sol2/job9/step2/inputs.txt) · [Raw runs](sol2/job9/step2/runs.jsonl.txt) · [Summary](sol2/job9/step2/summary.txt) · [Command](sol2/job9/step2-command.raw.txt)

### Step 3 source, build and known answers

At minute 45 the read of Carbon2's pinned tip `dfb88772b71ea25b81988030c0953a8a32fa581a` found the consolidated diff. Its exact SHA-256 was **`3d2ce085a8b76478942d4e29d7a74512eb3ecd2d328d224e27f711a48e46cb30`**. GNU `sha256sum -c --strict` returned zero for the 29-file plain r15d manifest from the pinned handoff. [Diff source](sol2/job9/step3-patch-source.raw.txt) · [Exact diff](sol2/job9/stack_r15d_to_final.patch.txt) · [Manifest source](sol2/job9/carbon2-17-source-receipt.raw.txt) · [29-file check](sol2/job9/step3-base29-check.raw.txt)

```text
+ cd /workspace/work/sol2-job2/r15d
+ sha256sum -c --strict /workspace/work/sol2-job9/r15d-pc-29.sha256
CMakeLists.txt: OK
include/forge/b4.hpp: OK
include/forge/bitboard.hpp: OK
include/forge/board.hpp: OK
include/forge/book.hpp: OK
include/forge/clock_plan.hpp: OK
include/forge/eval.hpp: OK
include/forge/eval_params.hpp: OK
include/forge/nnue.hpp: OK
include/forge/nnue_v3.hpp: OK
include/forge/search.hpp: OK
include/forge/tm_finish.hpp: OK
include/forge/tm_node_share.hpp: OK
include/forge/uci.hpp: OK
include/forge/uci_clock.hpp: OK
include/forge/uci_output.hpp: OK
src/bitboard.cpp: OK
src/board.cpp: OK
src/book.cpp: OK
src/book_data.inc: OK
src/eval.cpp: OK
src/eval_params.cpp: OK
src/eval_params_table.inc: OK
src/nnue.cpp: OK
src/nnue_v3.cpp: OK
src/nnue_weights.inc: OK
src/polyglot_keys.inc: OK
src/search.cpp: OK
src/uci.cpp: OK
```

The patch applied to a new scratch copy using `patch --batch -p1 -F0` and exited zero with exact context and zero rejects. [Commands](sol2/job9/step3-build-command.raw.txt) · [Patch output](sol2/job9/step3-patch.raw.txt)

```text
patching file include/forge/b4.hpp
patching file include/forge/board.hpp
patching file include/forge/eval.hpp
patching file include/forge/nnue_v3.hpp
patching file include/forge/search.hpp
patching file src/board.cpp
patching file src/nnue_v3.cpp
patching file src/search.cpp
patching file src/uci.cpp
```

The kF-pgo executable SHA-256 was `90413337a79410b49b76cbec4b2e1a77344bcc2385fecd5950f1f2ababd1539a`. The build used the same GCC LTO+PGO recipe as k13 and a new `pgo-data-kF` folder with the same 20 PC20/net768 training games, seed `20261118`. Its held-out timing games used seed `20261117`. The pinned net, driver, options and both opening lists matched Job 8. All nine profile counters reported one run, and their hashes stayed fixed through the rebuild and the held-out workload. [Build command](sol2/job9/kF-step1-command.raw.txt) · [Generate lines](sol2/job9/kF-pgo-generate-build.raw.txt) · [Use lines](sol2/job9/kF-pgo-use-build.raw.txt) · [Counter inventory](sol2/job9/kF-gcda-inventory.raw.txt) · [Openings](sol2/job9/step3-opening-independence.raw.txt)

| kF-pgo gate | Observed |
|---|---|
| Fresh processes without option overrides | bench 11 312,866 / bench 13 862,329 / startpos perft 5 4,865,609 |
| Profile workload | 2,482 searches / 8,391,013 last-info nodes / `c7d9520ffe04deda` |
| Held-out timing workload | 8,612 searches / 29,333,343 last-info nodes / `5c705841c3ea17b4` |

All 20 startpos perft root-move counts also matched r15d-pgo byte for byte. [Default pins](sol2/job9/step3-kF-pgo-pins.raw.txt) · [Training raw](sol2/job9/kF-training.raw.txt) · [Timing identity raw](sol2/job9/kF-identity.raw.txt)

### Step 3 — kF-pgo against r15d-pgo

B/A compares `kF-pgo` (`90413337a79410b49b76cbec4b2e1a77344bcc2385fecd5950f1f2ababd1539a`) with `r15d-pgo` (`96f50b3eb6d4f05cfa8291eaab56ea9c943a8e98fb3b248fff3b9138fcce6808`).

| Block | Leg | Engine | CPU (s) | Wall (s) | Trace | Exit | In ratios |
|---:|---|---|---:|---:|---|---:|---|
| 1 | Warm-up | r15d-pgo | 20.108 | 20.916 | `5c705841c3ea17b4` | 0 | no |
| 1 | 1 | r15d-pgo | 20.677 | 21.562 | `5c705841c3ea17b4` | 0 | yes |
| 1 | 2 | kF-pgo | 18.324 | 19.113 | `5c705841c3ea17b4` | 0 | yes |
| 1 | 3 | kF-pgo | 18.766 | 19.597 | `5c705841c3ea17b4` | 0 | yes |
| 1 | 4 | r15d-pgo | 19.226 | 20.009 | `5c705841c3ea17b4` | 0 | yes |
| 2 | Warm-up | kF-pgo | 18.034 | 18.822 | `5c705841c3ea17b4` | 0 | no |
| 2 | 1 | kF-pgo | 18.936 | 19.771 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 2 | r15d-pgo | 20.209 | 21.057 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 3 | r15d-pgo | 19.783 | 20.599 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 4 | kF-pgo | 17.807 | 18.570 | `5c705841c3ea17b4` | 0 | yes |
| 3 | Warm-up | r15d-pgo | 19.566 | 20.368 | `5c705841c3ea17b4` | 0 | no |
| 3 | 1 | r15d-pgo | 20.027 | 20.862 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 2 | kF-pgo | 18.030 | 18.800 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 3 | kF-pgo | 18.828 | 19.654 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 4 | r15d-pgo | 20.948 | 21.826 | `5c705841c3ea17b4` | 0 | yes |
| 4 | Warm-up | kF-pgo | 18.581 | 19.390 | `5c705841c3ea17b4` | 0 | no |
| 4 | 1 | kF-pgo | 19.132 | 19.987 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 2 | r15d-pgo | 22.540 | 23.509 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 3 | r15d-pgo | 20.403 | 21.246 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 4 | kF-pgo | 18.401 | 19.203 | `5c705841c3ea17b4` | 0 | yes |
| 5 | Warm-up | r15d-pgo | 20.506 | 21.335 | `5c705841c3ea17b4` | 0 | no |
| 5 | 1 | r15d-pgo | 19.766 | 20.583 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 2 | kF-pgo | 18.978 | 19.809 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 3 | kF-pgo | 19.201 | 20.068 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 4 | r15d-pgo | 19.950 | 20.771 | `5c705841c3ea17b4` | 0 | yes |
| 6 | Warm-up | kF-pgo | 18.731 | 19.561 | `5c705841c3ea17b4` | 0 | no |
| 6 | 1 | kF-pgo | 18.751 | 19.600 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 2 | r15d-pgo | 19.743 | 20.557 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 3 | r15d-pgo | 20.818 | 21.729 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 4 | kF-pgo | 19.225 | 20.055 | `5c705841c3ea17b4` | 0 | yes |
| 7 | Warm-up | r15d-pgo | 20.801 | 21.659 | `5c705841c3ea17b4` | 0 | no |
| 7 | 1 | r15d-pgo | 20.309 | 21.177 | `5c705841c3ea17b4` | 0 | yes |
| 7 | 2 | kF-pgo | 20.208 | 21.168 | `5c705841c3ea17b4` | 0 | yes |
| 7 | 3 | kF-pgo | 20.285 | 21.234 | `5c705841c3ea17b4` | 0 | yes |
| 7 | 4 | r15d-pgo | 21.705 | 22.639 | `5c705841c3ea17b4` | 0 | yes |
| 8 | Warm-up | kF-pgo | 18.021 | 18.812 | `5c705841c3ea17b4` | 0 | no |
| 8 | 1 | kF-pgo | 19.127 | 19.977 | `5c705841c3ea17b4` | 0 | yes |
| 8 | 2 | r15d-pgo | 21.363 | 22.310 | `5c705841c3ea17b4` | 0 | yes |
| 8 | 3 | r15d-pgo | 21.343 | 22.258 | `5c705841c3ea17b4` | 0 | yes |
| 8 | 4 | kF-pgo | 19.529 | 20.405 | `5c705841c3ea17b4` | 0 | yes |
| 9 | Warm-up | r15d-pgo | 20.478 | 21.357 | `5c705841c3ea17b4` | 0 | no |
| 9 | 1 | r15d-pgo | 20.394 | 21.222 | `5c705841c3ea17b4` | 0 | yes |
| 9 | 2 | kF-pgo | 18.270 | 19.055 | `5c705841c3ea17b4` | 0 | yes |
| 9 | 3 | kF-pgo | 18.846 | 19.679 | `5c705841c3ea17b4` | 0 | yes |
| 9 | 4 | r15d-pgo | 21.108 | 22.008 | `5c705841c3ea17b4` | 0 | yes |
| 10 | Warm-up | kF-pgo | 17.934 | 18.715 | `5c705841c3ea17b4` | 0 | no |
| 10 | 1 | kF-pgo | 18.077 | 18.864 | `5c705841c3ea17b4` | 0 | yes |
| 10 | 2 | r15d-pgo | 19.332 | 20.128 | `5c705841c3ea17b4` | 0 | yes |
| 10 | 3 | r15d-pgo | 20.474 | 21.360 | `5c705841c3ea17b4` | 0 | yes |
| 10 | 4 | kF-pgo | 18.143 | 18.942 | `5c705841c3ea17b4` | 0 | yes |
| 11 | Warm-up | r15d-pgo | 19.656 | 20.456 | `5c705841c3ea17b4` | 0 | no |
| 11 | 1 | r15d-pgo | 19.359 | 20.155 | `5c705841c3ea17b4` | 0 | yes |
| 11 | 2 | kF-pgo | 18.522 | 19.331 | `5c705841c3ea17b4` | 0 | yes |
| 11 | 3 | kF-pgo | 18.375 | 19.167 | `5c705841c3ea17b4` | 0 | yes |
| 11 | 4 | r15d-pgo | 20.811 | 21.693 | `5c705841c3ea17b4` | 0 | yes |
| 12 | Warm-up | kF-pgo | 18.493 | 19.302 | `5c705841c3ea17b4` | 0 | no |
| 12 | 1 | kF-pgo | 20.569 | 21.520 | `5c705841c3ea17b4` | 0 | yes |
| 12 | 2 | r15d-pgo | 22.744 | 23.760 | `5c705841c3ea17b4` | 0 | yes |
| 12 | 3 | r15d-pgo | 22.071 | 23.022 | `5c705841c3ea17b4` | 0 | yes |
| 12 | 4 | kF-pgo | 19.442 | 20.336 | `5c705841c3ea17b4` | 0 | yes |

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9295 | 0.9312 |
| 2 | BAAB | 0.9188 | 0.9204 |
| 3 | ABBA | 0.8995 | 0.9008 |
| 4 | BAAB | 0.8740 | 0.8757 |
| 5 | ABBA | 0.9613 | 0.9643 |
| 6 | BAAB | 0.9363 | 0.9378 |
| 7 | ABBA | 0.9638 | 0.9677 |
| 8 | BAAB | 0.9052 | 0.9061 |
| 9 | ABBA | 0.8943 | 0.8960 |
| 10 | BAAB | 0.9099 | 0.9113 |
| 11 | ABBA | 0.9185 | 0.9200 |
| 12 | BAAB | 0.8928 | 0.8947 |

| Metric | Median | Pooled | Block range | Below 1 | Above 1 | Reading |
|---|---:|---:|---:|---:|---:|---|
| Engine CPU | 0.9142 | 0.9165 | 0.8740–0.9638 | 12/12 | 0/12 | MEASURED |
| Wall | 0.9156 | 0.9184 | 0.8757–0.9677 | 12/12 | 0/12 | MEASURED |

| Block cohort | Metric | Timed leg 1 | Leg 2 | Leg 3 | Leg 4 |
|---|---|---:|---:|---:|---:|
| Odd (ABBA) | Engine CPU | 1.02424 | 0.95395 | 0.97077 | 1.05104 |
| Odd (ABBA) | Wall | 1.02298 | 0.95481 | 0.97221 | 1.05000 |
| Even (BAAB) | Engine CPU | 0.95907 | 1.05321 | 1.04548 | 0.94224 |
| Even (BAAB) | Wall | 0.96020 | 1.05244 | 1.04459 | 0.94277 |

Each position is divided by the mean of the four timed legs in its block before averaging by cohort.

[Inputs](sol2/job9/step3/inputs.txt) · [Raw runs](sol2/job9/step3/runs.jsonl.txt) · [Summary](sol2/job9/step3/summary.txt) · [Command](sol2/job9/step3-command.raw.txt)


## Facts

- The independent readback reconciled 144 eligible timed runs and 36 corresponding warm-ups from complete blocks. Those runs matched the pinned 60-game PC20/net768 signature of 8,612 searches, 29,333,343 last-info nodes and trace `5c705841c3ea17b4`. [Readback script](sol2/job9/timing_readback.py.txt)
- The identical-binary control spanned 0.9640–1.0485 for CPU, with a 1.0022 median, 1.0029 pooled and 6/12 blocks below one. Job 8's identical-binary control had all six blocks below one. [Job 9 floor](sol2/job9/step1/summary.txt) · [Job 8 floor](sol2/job8/step2/summary.txt)
- The k13-pgo/k11v-pgo comparison gave **0.9894** pooled engine CPU and **0.9897** pooled wall. CPU had 9/12 blocks below one. The readings were **not measurable here** for CPU and **not measurable here** for wall. [Raw summary](sol2/job9/step2/summary.txt)
- The kF-pgo/r15d-pgo comparison gave **0.9165** pooled engine CPU and **0.9184** pooled wall. CPU had 12/12 blocks below one. The readings were **MEASURED** for CPU and **MEASURED** for wall. [Raw summary](sol2/job9/step3/summary.txt)


## Suspicions

The alternating design balances which arm occupies the first and last positions. The position means show any residual order pattern separately for ABBA and BAAB. Alternation and the outer warm-up changed together, so this session leaves their individual effects unresolved. [Timing summary](sol2/job9/step1/summary.txt)

## What this check cannot see

More than one thread, Hash sizes other than 16, a game clock, the PC's own net, compiler (clang with ThinLTO and a
profile from self-play) and processor.

## What I did not do

The work used scratch cloud builds and one pinned single-threaded workload. The branch holds text receipts, including the archived consolidated diff. [Publication layout](sol2/job9/publication-layout.raw.txt)

## What I am not sure about

The owner-PC gain remains unknown. The timing signature covers the driver's game and ply indices, best moves, last-info nodes and last-info scores. Internal node visitation order is beyond that signature's coverage.
