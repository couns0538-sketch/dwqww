# sol2 — Job 11 consolidated Forge stack with concurrent fixed-node games

## Step 0 — frozen build checks and machine topology

| Frozen executable | SHA-256 | Fresh-process bench 11 | Bench 13 | Startpos perft 5 |
|---|---|---:|---:|---:|
| r15d-pgo | `96f50b3eb6d4f05cfa8291eaab56ea9c943a8e98fb3b248fff3b9138fcce6808` | 312,866 | 862,329 | 4,865,609 |
| kF-pgo | `90413337a79410b49b76cbec4b2e1a77344bcc2385fecd5950f1f2ababd1539a` | 312,866 | 862,329 | 4,865,609 |

Both archived Job 10 binaries passed with fresh processes and zero UCI option overrides. They use GCC 14.2.0, libstdc++ 6.0.33, glibc 2.41, CMake Release, `-march=x86-64-v4`, `-flto` and private profiles from the same 20-game training workload. [Frozen receipts](sol2/job11/step0-frozen-identities.raw.txt) · [r15d pins](sol2/job11/step0-r15d-pgo-pins.raw.txt) · [kF pins](sol2/job11/step0-kF-pgo-pins.raw.txt) · [Build recipe](REPORT_sol2_job9.md)

`nproc` returned five. The KVM guest reports AMD EPYC 9V74, five cores on one socket, one logical CPU per core and one 32 MiB L3 cache. The cgroup CPU capacity was four CPU equivalents. The brief's rule gave **N = 3**. I selected CPUs **1, 2, and 3**, leaving CPUs 0 and 4 out of the engine groups. Each worker's Linux thread-sibling list was a distinct singleton, so the selected CPUs shared no guest-reported core. [Machine commands and output](sol2/job11/step0-machine.txt) · [Worker placement](sol2/job11/step0-worker-selection.txt)

## Known answer — both three-engine groups matched

### Known-answer groups on logical CPUs 1, 2, 3

| Arm | CPU | Games | Searches | Last-info nodes | Trace | Engine exit | Worker exit |
|---|---:|---:|---:|---:|---|---:|---:|
| r15d-pgo | 1 | 12 | 1373 | 15527588 | `73ecbb5eedc59271` | 0 | 0 |
| r15d-pgo | 2 | 12 | 1373 | 15527588 | `73ecbb5eedc59271` | 0 | 0 |
| r15d-pgo | 3 | 12 | 1373 | 15527588 | `73ecbb5eedc59271` | 0 | 0 |
| kF-pgo | 1 | 12 | 1373 | 15527588 | `73ecbb5eedc59271` | 0 | 0 |
| kF-pgo | 2 | 12 | 1373 | 15527588 | `73ecbb5eedc59271` | 0 | 0 |
| kF-pgo | 3 | 12 | 1373 | 15527588 | `73ecbb5eedc59271` | 0 | 0 |

[Machine and CPU selection](sol2/job11/step0-worker-selection.txt) · [Raw worker receipts](sol2/job11/gate)

The Job 10 driver, saved opening histories, known-answer file and synthetic net768 all matched their pinned hashes. Each engine replayed the same first 12 eight-ply histories under PC20, Threads 1, Hash 16 MiB, OwnBook false, `go nodes 20000` on each move and a 300-ply ceiling. Each worker's captured per-search rows matched the Job 10 baseline in order on game, ply, move, last-info nodes and last-info score. The timed groups omit the gate-only per-search capture. [Workload pin check](sol2/job11/workload-pin-check.raw.txt) · [Gate commands and per-worker readback](sol2/job11/gate-command-and-readback.raw.txt) · [Saved workload](sol2/job10/fixed-openings.txt) · [r15d group](sol2/job11/gate/r15d-pgo.group.raw.txt) · [kF group](sol2/job11/gate/kF-pgo.group.raw.txt)

## Prediction graded

The prediction was published alone at `13571b23355d36369e077564c4890d9a4247d4a2` after both known-answer groups and before any timed run.

| Quantity | Prediction | Observed | Difference |
|---|---:|---:|---:|
| Identical-binary run CPU minimum | 0.957 | 0.9138 | -0.0432 |
| Identical-binary run CPU maximum | 1.038 | 1.0998 | +0.0618 |
| Pooled kF-pgo/r15d-pgo CPU | 0.940 | 0.9265 | -0.0135 |
| Run CPU blocks below one | 11/12 | 12/12 | +1 blocks |
| CPU ratio relative to Job 10 | Higher than 0.9224 | higher | Observed difference +0.0041 |

The prediction attributed a possible higher ratio to cache and memory contention across the three engines. The timing results show the direction of the ratio. The hardware cause remains unmeasured. [Original prediction](sol2/job11/prediction.txt) · [UTC checkpoints](sol2/job11/stamps.txt)

## Steps 1–2 — balanced three-engine timing

Each group used three fresh Python driver processes running the same arm and three fresh Forge processes, one inherited pinned CPU per engine. The drivers waited at a common pipe barrier before their calls. Run CPU is the sum of the three reaped Forge processes' user plus system time. Run wall is the interval from the earliest worker start to the latest worker end on a shared monotonic clock. It covers the driver calls, including their internal warm-ups. [Concurrency runner](sol2/job11/concurrent_measure.py.txt) · [Worker tests](sol2/job11/concurrent-measure-tests.raw.txt) · [Job 10 driver](sol2/job10/fixed_nodes_driver.py.txt)

Odd blocks used A B B A, even blocks B A A B. Each block began with a full recorded warm-up group of its first arm. The warm-up passed the same identity gates and was excluded from all ratios. The control used r15d at two paths and `cmp` verified identical bytes. Block ratios divide summed timed B durations by summed timed A durations within that block. The pooled ratio uses summed timed durations across complete blocks. The decision requires the median outside the twelve-block control range and at least 10 of 12 blocks on the same side of one. The order-position means divide each timed leg by its block's mean before averaging by block parity. [Copy receipt](sol2/job11/step1-copy.raw.txt) · [Balanced harness](sol2/job11/balanced_timing.py.txt) · [Independent readback](sol2/job11/timing_readback.py.txt)

Each worker uses PC20, Threads 1, Hash 16 MiB, net768 and `go nodes 20000`. The pinned 12-game workload gives 1,373 searches, 15,527,588 last-info nodes and `73ecbb5eedc59271`.

### Step 1 — identical-binary concurrent floor

B/A compares `copy` (`96f50b3eb6d4f05cfa8291eaab56ea9c943a8e98fb3b248fff3b9138fcce6808`) with `r15d-pgo` (`96f50b3eb6d4f05cfa8291eaab56ea9c943a8e98fb3b248fff3b9138fcce6808`).

| Block | Leg | Arm | Group CPU (s) | Group wall (s) | Workers matching | Engine exits | In ratios |
|---:|---|---|---:|---:|---:|---|---|
| 1 | Warm-up | r15d-pgo | 56.675 | 19.290 | 3/3 | 0, 0, 0 | no |
| 1 | 1 | r15d-pgo | 50.777 | 17.282 | 3/3 | 0, 0, 0 | yes |
| 1 | 2 | copy | 51.546 | 17.556 | 3/3 | 0, 0, 0 | yes |
| 1 | 3 | copy | 52.724 | 18.254 | 3/3 | 0, 0, 0 | yes |
| 1 | 4 | r15d-pgo | 51.988 | 17.745 | 3/3 | 0, 0, 0 | yes |
| 2 | Warm-up | copy | 50.181 | 17.062 | 3/3 | 0, 0, 0 | no |
| 2 | 1 | copy | 51.108 | 17.599 | 3/3 | 0, 0, 0 | yes |
| 2 | 2 | r15d-pgo | 51.527 | 17.653 | 3/3 | 0, 0, 0 | yes |
| 2 | 3 | r15d-pgo | 51.978 | 17.982 | 3/3 | 0, 0, 0 | yes |
| 2 | 4 | copy | 49.407 | 16.862 | 3/3 | 0, 0, 0 | yes |
| 3 | Warm-up | r15d-pgo | 56.093 | 19.120 | 3/3 | 0, 0, 0 | no |
| 3 | 1 | r15d-pgo | 52.699 | 18.145 | 3/3 | 0, 0, 0 | yes |
| 3 | 2 | copy | 50.489 | 17.323 | 3/3 | 0, 0, 0 | yes |
| 3 | 3 | copy | 49.437 | 16.983 | 3/3 | 0, 0, 0 | yes |
| 3 | 4 | r15d-pgo | 52.752 | 18.083 | 3/3 | 0, 0, 0 | yes |
| 4 | Warm-up | copy | 52.000 | 17.736 | 3/3 | 0, 0, 0 | no |
| 4 | 1 | copy | 51.316 | 17.412 | 3/3 | 0, 0, 0 | yes |
| 4 | 2 | r15d-pgo | 54.153 | 18.379 | 3/3 | 0, 0, 0 | yes |
| 4 | 3 | r15d-pgo | 50.859 | 17.605 | 3/3 | 0, 0, 0 | yes |
| 4 | 4 | copy | 52.643 | 18.075 | 3/3 | 0, 0, 0 | yes |
| 5 | Warm-up | r15d-pgo | 53.295 | 18.221 | 3/3 | 0, 0, 0 | no |
| 5 | 1 | r15d-pgo | 52.385 | 18.172 | 3/3 | 0, 0, 0 | yes |
| 5 | 2 | copy | 62.790 | 21.517 | 3/3 | 0, 0, 0 | yes |
| 5 | 3 | copy | 60.379 | 20.701 | 3/3 | 0, 0, 0 | yes |
| 5 | 4 | r15d-pgo | 59.609 | 20.493 | 3/3 | 0, 0, 0 | yes |
| 6 | Warm-up | copy | 57.143 | 19.689 | 3/3 | 0, 0, 0 | no |
| 6 | 1 | copy | 55.875 | 19.109 | 3/3 | 0, 0, 0 | yes |
| 6 | 2 | r15d-pgo | 52.853 | 18.355 | 3/3 | 0, 0, 0 | yes |
| 6 | 3 | r15d-pgo | 56.426 | 19.597 | 3/3 | 0, 0, 0 | yes |
| 6 | 4 | copy | 50.720 | 17.382 | 3/3 | 0, 0, 0 | yes |
| 7 | Warm-up | r15d-pgo | 50.810 | 17.385 | 3/3 | 0, 0, 0 | no |
| 7 | 1 | r15d-pgo | 54.252 | 18.834 | 3/3 | 0, 0, 0 | yes |
| 7 | 2 | copy | 51.603 | 17.761 | 3/3 | 0, 0, 0 | yes |
| 7 | 3 | copy | 52.305 | 18.013 | 3/3 | 0, 0, 0 | yes |
| 7 | 4 | r15d-pgo | 59.458 | 20.373 | 3/3 | 0, 0, 0 | yes |
| 8 | Warm-up | copy | 52.624 | 18.000 | 3/3 | 0, 0, 0 | no |
| 8 | 1 | copy | 48.453 | 16.757 | 3/3 | 0, 0, 0 | yes |
| 8 | 2 | r15d-pgo | 47.955 | 16.369 | 3/3 | 0, 0, 0 | yes |
| 8 | 3 | r15d-pgo | 49.040 | 16.813 | 3/3 | 0, 0, 0 | yes |
| 8 | 4 | copy | 49.058 | 16.822 | 3/3 | 0, 0, 0 | yes |
| 9 | Warm-up | r15d-pgo | 48.990 | 16.801 | 3/3 | 0, 0, 0 | no |
| 9 | 1 | r15d-pgo | 50.786 | 17.233 | 3/3 | 0, 0, 0 | yes |
| 9 | 2 | copy | 51.137 | 17.653 | 3/3 | 0, 0, 0 | yes |
| 9 | 3 | copy | 50.029 | 17.253 | 3/3 | 0, 0, 0 | yes |
| 9 | 4 | r15d-pgo | 49.569 | 16.900 | 3/3 | 0, 0, 0 | yes |
| 10 | Warm-up | copy | 51.019 | 17.568 | 3/3 | 0, 0, 0 | no |
| 10 | 1 | copy | 49.509 | 16.945 | 3/3 | 0, 0, 0 | yes |
| 10 | 2 | r15d-pgo | 50.578 | 17.234 | 3/3 | 0, 0, 0 | yes |
| 10 | 3 | r15d-pgo | 53.847 | 18.493 | 3/3 | 0, 0, 0 | yes |
| 10 | 4 | copy | 51.381 | 17.445 | 3/3 | 0, 0, 0 | yes |
| 11 | Warm-up | r15d-pgo | 54.976 | 18.735 | 3/3 | 0, 0, 0 | no |
| 11 | 1 | r15d-pgo | 49.939 | 16.992 | 3/3 | 0, 0, 0 | yes |
| 11 | 2 | copy | 48.915 | 16.815 | 3/3 | 0, 0, 0 | yes |
| 11 | 3 | copy | 49.812 | 17.318 | 3/3 | 0, 0, 0 | yes |
| 11 | 4 | r15d-pgo | 48.862 | 16.604 | 3/3 | 0, 0, 0 | yes |
| 12 | Warm-up | copy | 49.772 | 17.141 | 3/3 | 0, 0, 0 | no |
| 12 | 1 | copy | 51.214 | 17.583 | 3/3 | 0, 0, 0 | yes |
| 12 | 2 | r15d-pgo | 51.835 | 17.849 | 3/3 | 0, 0, 0 | yes |
| 12 | 3 | r15d-pgo | 50.770 | 17.278 | 3/3 | 0, 0, 0 | yes |
| 12 | 4 | copy | 55.176 | 18.729 | 3/3 | 0, 0, 0 | yes |

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 1.0146 | 1.0224 |
| 2 | BAAB | 0.9711 | 0.9670 |
| 3 | ABBA | 0.9476 | 0.9470 |
| 4 | BAAB | 0.9900 | 0.9862 |
| 5 | ABBA | 1.0998 | 1.0919 |
| 6 | BAAB | 0.9754 | 0.9615 |
| 7 | ABBA | 0.9138 | 0.9124 |
| 8 | BAAB | 1.0053 | 1.0120 |
| 9 | ABBA | 1.0081 | 1.0227 |
| 10 | BAAB | 0.9661 | 0.9626 |
| 11 | ABBA | 0.9992 | 1.0160 |
| 12 | BAAB | 1.0369 | 1.0337 |

| Metric | Median | Pooled | Block range | Below 1 | Above 1 | Reading |
|---|---:|---:|---|---:|---:|---|
| Engine CPU | 0.9946 | 0.9937 | 0.9138–1.0998 | 7/12 | 5/12 | Identical-binary floor |
| Wall | 0.9991 | 0.9940 | 0.9124–1.0919 | 6/12 | 6/12 | Identical-binary floor |

| Block cohort | Metric | Leg 1 | Leg 2 | Leg 3 | Leg 4 |
|---|---|---:|---:|---:|---:|
| Odd | Engine CPU | 0.98583 | 1.00022 | 0.99527 | 1.01867 |
| Odd | Wall | 0.98504 | 1.00021 | 1.00016 | 1.01459 |
| Even | Engine CPU | 0.99347 | 0.99829 | 1.01123 | 0.99701 |
| Even | Wall | 0.99345 | 0.99759 | 1.01570 | 0.99326 |

The position means divide each timed leg by its block's four-leg mean before averaging by cohort.

[Inputs](sol2/job11/step1/inputs.txt) · [Raw groups and workers](sol2/job11/step1) · [Summary](sol2/job11/step1/summary.txt)

### Step 2 — kF-pgo against r15d-pgo

B/A compares `kF-pgo` (`90413337a79410b49b76cbec4b2e1a77344bcc2385fecd5950f1f2ababd1539a`) with `r15d-pgo` (`96f50b3eb6d4f05cfa8291eaab56ea9c943a8e98fb3b248fff3b9138fcce6808`).

| Block | Leg | Arm | Group CPU (s) | Group wall (s) | Workers matching | Engine exits | In ratios |
|---:|---|---|---:|---:|---:|---|---|
| 1 | Warm-up | r15d-pgo | 49.456 | 16.884 | 3/3 | 0, 0, 0 | no |
| 1 | 1 | r15d-pgo | 50.161 | 17.213 | 3/3 | 0, 0, 0 | yes |
| 1 | 2 | kF-pgo | 45.964 | 15.684 | 3/3 | 0, 0, 0 | yes |
| 1 | 3 | kF-pgo | 48.528 | 16.713 | 3/3 | 0, 0, 0 | yes |
| 1 | 4 | r15d-pgo | 50.683 | 17.639 | 3/3 | 0, 0, 0 | yes |
| 2 | Warm-up | kF-pgo | 46.590 | 16.011 | 3/3 | 0, 0, 0 | no |
| 2 | 1 | kF-pgo | 49.655 | 17.154 | 3/3 | 0, 0, 0 | yes |
| 2 | 2 | r15d-pgo | 59.342 | 20.308 | 3/3 | 0, 0, 0 | yes |
| 2 | 3 | r15d-pgo | 56.769 | 19.623 | 3/3 | 0, 0, 0 | yes |
| 2 | 4 | kF-pgo | 52.561 | 18.178 | 3/3 | 0, 0, 0 | yes |
| 3 | Warm-up | r15d-pgo | 53.794 | 18.289 | 3/3 | 0, 0, 0 | no |
| 3 | 1 | r15d-pgo | 50.324 | 17.263 | 3/3 | 0, 0, 0 | yes |
| 3 | 2 | kF-pgo | 49.154 | 16.888 | 3/3 | 0, 0, 0 | yes |
| 3 | 3 | kF-pgo | 46.402 | 15.973 | 3/3 | 0, 0, 0 | yes |
| 3 | 4 | r15d-pgo | 49.578 | 16.940 | 3/3 | 0, 0, 0 | yes |
| 4 | Warm-up | kF-pgo | 48.768 | 16.698 | 3/3 | 0, 0, 0 | no |
| 4 | 1 | kF-pgo | 46.906 | 16.028 | 3/3 | 0, 0, 0 | yes |
| 4 | 2 | r15d-pgo | 51.970 | 18.030 | 3/3 | 0, 0, 0 | yes |
| 4 | 3 | r15d-pgo | 53.916 | 18.488 | 3/3 | 0, 0, 0 | yes |
| 4 | 4 | kF-pgo | 46.843 | 15.906 | 3/3 | 0, 0, 0 | yes |
| 5 | Warm-up | r15d-pgo | 48.799 | 16.630 | 3/3 | 0, 0, 0 | no |
| 5 | 1 | r15d-pgo | 48.484 | 16.459 | 3/3 | 0, 0, 0 | yes |
| 5 | 2 | kF-pgo | 46.195 | 15.768 | 3/3 | 0, 0, 0 | yes |
| 5 | 3 | kF-pgo | 51.164 | 17.528 | 3/3 | 0, 0, 0 | yes |
| 5 | 4 | r15d-pgo | 51.923 | 17.743 | 3/3 | 0, 0, 0 | yes |
| 6 | Warm-up | kF-pgo | 46.030 | 15.856 | 3/3 | 0, 0, 0 | no |
| 6 | 1 | kF-pgo | 45.418 | 15.761 | 3/3 | 0, 0, 0 | yes |
| 6 | 2 | r15d-pgo | 52.242 | 18.060 | 3/3 | 0, 0, 0 | yes |
| 6 | 3 | r15d-pgo | 51.595 | 17.677 | 3/3 | 0, 0, 0 | yes |
| 6 | 4 | kF-pgo | 46.365 | 16.008 | 3/3 | 0, 0, 0 | yes |
| 7 | Warm-up | r15d-pgo | 47.938 | 16.266 | 3/3 | 0, 0, 0 | no |
| 7 | 1 | r15d-pgo | 48.414 | 16.713 | 3/3 | 0, 0, 0 | yes |
| 7 | 2 | kF-pgo | 51.911 | 18.023 | 3/3 | 0, 0, 0 | yes |
| 7 | 3 | kF-pgo | 44.480 | 15.500 | 3/3 | 0, 0, 0 | yes |
| 7 | 4 | r15d-pgo | 50.953 | 17.489 | 3/3 | 0, 0, 0 | yes |
| 8 | Warm-up | kF-pgo | 46.669 | 15.936 | 3/3 | 0, 0, 0 | no |
| 8 | 1 | kF-pgo | 46.334 | 15.903 | 3/3 | 0, 0, 0 | yes |
| 8 | 2 | r15d-pgo | 52.672 | 17.932 | 3/3 | 0, 0, 0 | yes |
| 8 | 3 | r15d-pgo | 52.386 | 17.988 | 3/3 | 0, 0, 0 | yes |
| 8 | 4 | kF-pgo | 51.968 | 17.747 | 3/3 | 0, 0, 0 | yes |
| 9 | Warm-up | r15d-pgo | 49.739 | 16.914 | 3/3 | 0, 0, 0 | no |
| 9 | 1 | r15d-pgo | 48.134 | 16.562 | 3/3 | 0, 0, 0 | yes |
| 9 | 2 | kF-pgo | 46.274 | 16.121 | 3/3 | 0, 0, 0 | yes |
| 9 | 3 | kF-pgo | 48.298 | 16.421 | 3/3 | 0, 0, 0 | yes |
| 9 | 4 | r15d-pgo | 49.871 | 17.169 | 3/3 | 0, 0, 0 | yes |
| 10 | Warm-up | kF-pgo | 46.441 | 15.973 | 3/3 | 0, 0, 0 | no |
| 10 | 1 | kF-pgo | 51.723 | 18.013 | 3/3 | 0, 0, 0 | yes |
| 10 | 2 | r15d-pgo | 62.049 | 21.240 | 3/3 | 0, 0, 0 | yes |
| 10 | 3 | r15d-pgo | 59.967 | 20.470 | 3/3 | 0, 0, 0 | yes |
| 10 | 4 | kF-pgo | 54.670 | 18.985 | 3/3 | 0, 0, 0 | yes |
| 11 | Warm-up | r15d-pgo | 58.081 | 19.887 | 3/3 | 0, 0, 0 | no |
| 11 | 1 | r15d-pgo | 58.628 | 19.993 | 3/3 | 0, 0, 0 | yes |
| 11 | 2 | kF-pgo | 52.076 | 17.702 | 3/3 | 0, 0, 0 | yes |
| 11 | 3 | kF-pgo | 49.080 | 16.845 | 3/3 | 0, 0, 0 | yes |
| 11 | 4 | r15d-pgo | 51.941 | 17.818 | 3/3 | 0, 0, 0 | yes |
| 12 | Warm-up | kF-pgo | 49.071 | 16.810 | 3/3 | 0, 0, 0 | no |
| 12 | 1 | kF-pgo | 48.767 | 16.834 | 3/3 | 0, 0, 0 | yes |
| 12 | 2 | r15d-pgo | 51.061 | 17.367 | 3/3 | 0, 0, 0 | yes |
| 12 | 3 | r15d-pgo | 56.348 | 19.575 | 3/3 | 0, 0, 0 | yes |
| 12 | 4 | kF-pgo | 55.373 | 19.297 | 3/3 | 0, 0, 0 | yes |

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9370 | 0.9295 |
| 2 | BAAB | 0.8803 | 0.8848 |
| 3 | ABBA | 0.9565 | 0.9608 |
| 4 | BAAB | 0.8854 | 0.8745 |
| 5 | ABBA | 0.9696 | 0.9735 |
| 6 | BAAB | 0.8839 | 0.8890 |
| 7 | ABBA | 0.9701 | 0.9802 |
| 8 | BAAB | 0.9357 | 0.9368 |
| 9 | ABBA | 0.9650 | 0.9648 |
| 10 | BAAB | 0.8720 | 0.8870 |
| 11 | ABBA | 0.9149 | 0.9137 |
| 12 | BAAB | 0.9696 | 0.9781 |

| Metric | Median | Pooled | Block range | Below 1 | Above 1 | Reading |
|---|---:|---:|---|---:|---:|---|
| Engine CPU | 0.9364 | 0.9265 | 0.8720–0.9701 | 12/12 | 0/12 | not measurable here |
| Wall | 0.9332 | 0.9294 | 0.8745–0.9802 | 12/12 | 0/12 | not measurable here |

| Block cohort | Metric | Leg 1 | Leg 2 | Leg 3 | Leg 4 |
|---|---|---:|---:|---:|---:|
| Odd | Engine CPU | 1.02239 | 0.98120 | 0.96958 | 1.02683 |
| Odd | Wall | 1.02013 | 0.98177 | 0.97055 | 1.02754 |
| Even | Engine CPU | 0.91959 | 1.04748 | 1.05357 | 0.97937 |
| Even | Wall | 0.92225 | 1.04402 | 1.05279 | 0.98094 |

The position means divide each timed leg by its block's four-leg mean before averaging by cohort.

[Inputs](sol2/job11/step2/inputs.txt) · [Raw groups and workers](sol2/job11/step2) · [Summary](sol2/job11/step2/summary.txt)

### kF-pgo against r15d-pgo at both engine counts

| Metric | Job 10 Step 2, one engine | Job 11 Step 2, 3 engines |
|---|---:|---:|
| Engine CPU floor range | 0.9309–1.0353 | 0.9138–1.0998 |
| Engine CPU block median | 0.9288 | 0.9364 |
| Engine CPU pooled B/A | 0.9224 | 0.9265 |
| Engine CPU blocks below 1 | 12/12 | 12/12 |
| Engine CPU reading | MEASURED | not measurable here |
| Wall floor range | 0.9299–1.0347 | 0.9124–1.0919 |
| Wall block median | 0.9298 | 0.9332 |
| Wall pooled B/A | 0.9232 | 0.9294 |
| Wall blocks below 1 | 12/12 | 12/12 |
| Wall reading | MEASURED | not measurable here |

Both sessions used the same two executable hashes and identical fixed-node workloads per engine. The concurrent session sums engine CPU and uses the enclosing monotonic wall interval. [Job 10 raw comparison](sol2/job10/step2/runs.jsonl.txt) · [Job 11 raw comparison](sol2/job11/step2/runs.jsonl.txt)


## Facts

- The readback reconciled 96 timed groups and 24 group warm-ups from complete blocks. That is 360 engine executions. Each retained the pinned 1,373 searches, 15,527,588 last-info nodes and trace `73ecbb5eedc59271`. [Independent reader](sol2/job11/timing_readback.py.txt)
- Across eligible groups, the three worker starts were separated by 0.061 ms median and 2.806 ms maximum. The raw groups include each worker's timestamps and verified CPU affinity. [Step 1 raw groups](sol2/job11/step1/runs.jsonl.txt) · [Step 2 raw groups](sol2/job11/step2/runs.jsonl.txt)
- The identical-binary run CPU ranged from 0.9138 to 1.0998, with a 0.9946 block median and 0.9937 pooled ratio. [Control summary](sol2/job11/step1/summary.txt)
- The consolidated stack pooled at **0.9265** run CPU and **0.9294** enclosing wall time. CPU was lower in 12 of 12 blocks. The readings were **not measurable here** for CPU and **not measurable here** for wall. [Candidate summary](sol2/job11/step2/summary.txt)


## Suspicions

The engines occupied separate guest cores and shared the reported L3. Cache or memory contention may affect the ratio. Host variation also differs between the one-engine and three-engine sessions, and each session has its own floor. The measurements leave those contributions unresolved.

## What this check cannot see

The PC's own net (larger: more memory traffic per node), compiler (clang with ThinLTO and a profile from self-play)
and processor (16 logical CPUs on 8 cores; the PC's games and its self-play share them), Hash sizes other than 16,
a game clock.

## What I did not do

The experiment used three cloud engines at a time, the frozen GCC executables and synthetic net768. The published evidence is text. [Publication layout](sol2/job11/publication-layout.raw.txt)

## What I am not sure about

The gain for the owner's eight games alongside self-play remains unknown. The timing signature covers game, ply, best moves, last-info nodes and last-info scores. Internal node visitation order is beyond its coverage.
