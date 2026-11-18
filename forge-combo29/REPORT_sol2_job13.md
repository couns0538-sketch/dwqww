# sol2 — Job 13 Clang self-play PGO and held-out self-play timing

## Step 0 — compiler, machine and frozen source checks

The workspace-local compiler reports Debian Clang 19.1.7. LLVM and LLD are also 19.1.7. The VM reports AMD EPYC 9V74, five logical CPUs on five guest cores, one thread per core and 32 MiB L3. Timed engine and driver processes used logical CPU 2. The frozen GCC LTO+PGO r15d and kF executable hashes matched Job 12. The pinned UHO book SHA-256 was `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. [Machine, compiler and pinned inputs](sol2/job13/step0-machine-and-pins.raw.txt) · [GCC hashes](sol2/job13/gcc-executables.raw.txt)

I recorded new Job 13 source snapshots containing every file under `src`. There was no separate Job 12 per-file list in the archived job area. The current r15d and kF trees reconciled with their earlier pinned Job 9 and Carbon2 manifests, 29 files each including all 13 source files. [Source provenance](sol2/job13/source-manifests-receipt.raw.txt) · [Both checks](sol2/job13/source-manifests-check.raw.txt) · [r15d snapshot](sol2/job13/step0-r15d-src.sha256.txt) · [kF snapshot](sol2/job13/step0-kF-src.sha256.txt)

## Step 1 — independent bench and self-play profiles

Both builds used Clang 19.1.7, CMake Release, C++20, system libstdc++ 6.0.33 and glibc 2.41. The build lines include `-O3 -DNDEBUG -ffp-contract=off -fno-fast-math -march=x86-64-v4 -flto=thin`, the original Forge defines and the workspace LLD. Each arm used `-fprofile-instr-generate`, merged its own bench and self-play profiles with `llvm-profdata merge -sparse`, and rebuilt cleanly with `-fprofile-instr-use` and `-Werror=profile-instr-out-of-date`. [r15d build commands](sol2/job13/r15d-step1-command.raw.txt) · [kF build commands](sol2/job13/kF-step1-command.raw.txt) · [r15d profile receipt](sol2/job13/r15d-profile-receipt.raw.txt) · [kF profile receipt](sol2/job13/kF-profile-receipt.raw.txt)

Each profile's bench process loaded net768 and ran bench 11, 13 and 16 in sequence. The only search option overrides were `CuckooRep=true`, `HistRework=2`, `TtPruneV2=true` and `CorrHistV2=true`. Both generated builds returned 1,261,644, 6,312,262 and 74,843,992 nodes under those bench-profile settings. The other profile process covered 60 original book FENs, physical lines 1001–1060, using PC20, Threads 1, Hash 16 MiB and `go softnodes 2000`. Each arm recorded 7,422 searches, 25,760,574 last-info nodes, 31,332,431 final nodes and trace `8f9ead372cabda98`. The driver used python-chess 1.11.2 with `claim_draw=True` and a 300-ply cap. [Bench instructions](sol2/job13/r15d-profile-bench.stdin.txt) · [r15d bench output](sol2/job13/r15d-profile-bench.stdout.txt) · [kF bench output](sol2/job13/kF-profile-bench.stdout.txt) · [r15d self-play raw](sol2/job13/r15d-profile-selfplay.raw.txt) · [kF self-play raw](sol2/job13/kF-profile-selfplay.raw.txt)

| Clang profile-use build | SHA-256 | Default bench 11 / bench 13 / perft 5 | PC20/net768 bench 11 / bench 13 | Job 10 fixed-node gate |
|---|---|---|---|---|
| r15d | `540e63c0b7cf2512f1716657aded48b0558022b49c0fe8489596195cf2035834` | 312,866 / 862,329 / 4,865,609 | 882,074 / 4,275,906 | 1,373 searches / 15,527,588 last-info nodes / `73ecbb5eedc59271` |
| kF | `da5df215a6aa255261d4e5574474da7c82aad1a9e95df83e15d5b38963ef439d` | 312,866 / 862,329 / 4,865,609 | 882,074 / 4,275,906 | 1,373 searches / 15,527,588 last-info nodes / `73ecbb5eedc59271` |

Every default pin used a fresh process with no option overrides. The PC20/net768 fresh-process pins and the Job 10 replay used one thread and Hash 16 MiB. The fixed-node replay used 12 saved startpos move histories at `go nodes 20000`. [r15d default pins](sol2/job13/r15d-default.raw.txt) · [kF default pins](sol2/job13/kF-default.raw.txt) · [r15d PC20 pins](sol2/job13/r15d-net768.raw.txt) · [kF PC20 pins](sol2/job13/kF-net768.raw.txt) · [r15d replay](sol2/job13/r15d-identity.raw.txt) · [kF replay](sol2/job13/kF-identity.raw.txt)

## Step 2 — held-out W and complete soft-node telemetry

W uses physical UHO book lines 7001–7020, PC20, synthetic net768, one thread, Hash 16 MiB, OwnBook false and `go softnodes 2000`. Each original FEN starts one game, with a reset and `isready` before play. Python-chess checks `claim_draw=True` and the cap is 300 plies. The profile's book lines were 1001–1060. [Workload pins](sol2/job13/workload-pins.raw.txt) · [Gate commands and readback](sol2/job13/step2-command-and-readback.raw.txt)

| New Clang build | Games | Searches | Last-info nodes | Final nodes | Trace | Engine CPU (s) | Wall (s) |
|---|---:|---:|---:|---:|---|---:|---:|
| r15d | 20 | 2,247 | 7,905,938 | 9,189,426 | `7f78d3aec021ab01` | 4.9780 | 5.8550 |
| kF | 20 | 2,247 | 7,905,938 | 9,189,426 | `7f78d3aec021ab01` | 4.5472 | 5.2288 |

Every captured search agreed on book line, ply, best move, last-info nodes and final nodes. The difference between the final and last-info totals was 1,283,488 nodes per run, 13.97% of final nodes. The gate timing includes per-search receipt writing, which the timing campaigns omit. [r15d result](sol2/job13/step2/r15d.result.raw.txt) · [kF result](sol2/job13/step2/kF.result.raw.txt)

## Prediction graded

The prediction was published alone at `373001025b02fb04a92ba9ccf892a7298b0df187` after both W signatures matched.

| Quantity | Prediction | Observed | Within range |
|---|---:|---:|---|
| Step F lower middle CPU endpoint | 0.940–0.990 | 0.9301 | no |
| Step F upper middle CPU endpoint | 1.010–1.060 | 1.0510 | yes |
| Step K CPU block median | 0.890–0.970 | 0.9739 | no |
| Step K CPU blocks below one | 13–16 | 11 | no |

[Original prediction](sol2/job13/prediction.txt) · [UTC checkpoints](sol2/job13/stamps.txt)

## Step 3 — Clang comparison on held-out self-play

A run uses one pinned engine playing both sides for W. The driver resets the engine before each original FEN and records best moves, last-info node counts and final soft-node telemetry. Each campaign uses alternating ABBA and BAAB. Its first arm also runs once as a recorded warm-up before each block. Warm-ups are excluded from every ratio. Engine CPU is the reaped engine's user plus system time. Wall is the full driver interval. [Driver and raw parsing](sol2/job13/soft_book_driver.py.txt) · [Timing harness](sol2/job13/soft_balanced_timing.py.txt) · [Arithmetic fixture](sol2/job13/runner-fixture.raw.txt) · [Byte-copy control](sol2/job13/stepF-copy.raw.txt)

The pooled ratio divides summed timed B duration by summed timed A duration. The block ratio uses the same calculation within the block. Means and two-sided 95% t intervals use the block ratios, with 15 degrees of freedom for the 16-block campaigns and 7 for the optional 8-block GCC campaign. Each Clang candidate median is compared with the second and 15th sorted ratios from its control. The declared reading requires a median outside that middle range and at least 13 of 16 ratios on the same side of one. [Independent readback](sol2/job13/timing_readback.py.txt)

W uses PC20, Threads 1, Hash 16 MiB, net768 and `go softnodes 2000` on book lines 7001–7020. Both Step 2 engines record 20 games, 2,247 searches, 7,905,938 last-info nodes, 9,189,426 final soft-node counts and trace `7f78d3aec021ab01`. [W signature](sol2/job13/known-answer.txt)

### Step F — identical-binary Clang floor

- Arm A `clang-r15d` (`540e63c0b7cf2512f1716657aded48b0558022b49c0fe8489596195cf2035834`)
- Arm B `copy` (`540e63c0b7cf2512f1716657aded48b0558022b49c0fe8489596195cf2035834`)

Logical CPU 2. B/A compares summed timed B durations with summed timed A durations.

| Block | Leg | Engine | CPU (s) | Wall (s) | Trace | Exit | In ratios |
|---:|---|---|---:|---:|---|---:|---|
| 1 | Warm-up | clang-r15d | 5.248 | 6.152 | `7f78d3aec021ab01` | 0 | no |
| 1 | 1 | clang-r15d | 5.327 | 6.095 | `7f78d3aec021ab01` | 0 | yes |
| 1 | 2 | copy | 4.899 | 5.612 | `7f78d3aec021ab01` | 0 | yes |
| 1 | 3 | copy | 4.502 | 5.127 | `7f78d3aec021ab01` | 0 | yes |
| 1 | 4 | clang-r15d | 4.654 | 5.313 | `7f78d3aec021ab01` | 0 | yes |
| 2 | Warm-up | copy | 6.062 | 6.958 | `7f78d3aec021ab01` | 0 | no |
| 2 | 1 | copy | 5.062 | 5.792 | `7f78d3aec021ab01` | 0 | yes |
| 2 | 2 | clang-r15d | 4.958 | 5.680 | `7f78d3aec021ab01` | 0 | yes |
| 2 | 3 | clang-r15d | 5.012 | 5.736 | `7f78d3aec021ab01` | 0 | yes |
| 2 | 4 | copy | 4.906 | 5.631 | `7f78d3aec021ab01` | 0 | yes |
| 3 | Warm-up | clang-r15d | 5.501 | 6.329 | `7f78d3aec021ab01` | 0 | no |
| 3 | 1 | clang-r15d | 4.980 | 5.698 | `7f78d3aec021ab01` | 0 | yes |
| 3 | 2 | copy | 5.000 | 5.717 | `7f78d3aec021ab01` | 0 | yes |
| 3 | 3 | copy | 4.840 | 5.541 | `7f78d3aec021ab01` | 0 | yes |
| 3 | 4 | clang-r15d | 5.340 | 6.123 | `7f78d3aec021ab01` | 0 | yes |
| 4 | Warm-up | copy | 5.342 | 6.135 | `7f78d3aec021ab01` | 0 | no |
| 4 | 1 | copy | 5.364 | 6.146 | `7f78d3aec021ab01` | 0 | yes |
| 4 | 2 | clang-r15d | 5.464 | 6.278 | `7f78d3aec021ab01` | 0 | yes |
| 4 | 3 | clang-r15d | 5.568 | 6.414 | `7f78d3aec021ab01` | 0 | yes |
| 4 | 4 | copy | 5.167 | 5.924 | `7f78d3aec021ab01` | 0 | yes |
| 5 | Warm-up | clang-r15d | 4.763 | 5.436 | `7f78d3aec021ab01` | 0 | no |
| 5 | 1 | clang-r15d | 5.600 | 6.413 | `7f78d3aec021ab01` | 0 | yes |
| 5 | 2 | copy | 4.990 | 5.715 | `7f78d3aec021ab01` | 0 | yes |
| 5 | 3 | copy | 5.055 | 5.783 | `7f78d3aec021ab01` | 0 | yes |
| 5 | 4 | clang-r15d | 5.036 | 5.767 | `7f78d3aec021ab01` | 0 | yes |
| 6 | Warm-up | copy | 5.210 | 5.983 | `7f78d3aec021ab01` | 0 | no |
| 6 | 1 | copy | 4.856 | 5.520 | `7f78d3aec021ab01` | 0 | yes |
| 6 | 2 | clang-r15d | 4.877 | 5.577 | `7f78d3aec021ab01` | 0 | yes |
| 6 | 3 | clang-r15d | 4.816 | 5.493 | `7f78d3aec021ab01` | 0 | yes |
| 6 | 4 | copy | 4.911 | 5.629 | `7f78d3aec021ab01` | 0 | yes |
| 7 | Warm-up | clang-r15d | 5.176 | 5.938 | `7f78d3aec021ab01` | 0 | no |
| 7 | 1 | clang-r15d | 5.725 | 6.558 | `7f78d3aec021ab01` | 0 | yes |
| 7 | 2 | copy | 5.287 | 6.072 | `7f78d3aec021ab01` | 0 | yes |
| 7 | 3 | copy | 4.737 | 5.406 | `7f78d3aec021ab01` | 0 | yes |
| 7 | 4 | clang-r15d | 5.053 | 5.757 | `7f78d3aec021ab01` | 0 | yes |
| 8 | Warm-up | copy | 5.224 | 5.991 | `7f78d3aec021ab01` | 0 | no |
| 8 | 1 | copy | 4.940 | 5.663 | `7f78d3aec021ab01` | 0 | yes |
| 8 | 2 | clang-r15d | 5.300 | 6.089 | `7f78d3aec021ab01` | 0 | yes |
| 8 | 3 | clang-r15d | 5.003 | 5.724 | `7f78d3aec021ab01` | 0 | yes |
| 8 | 4 | copy | 4.734 | 5.421 | `7f78d3aec021ab01` | 0 | yes |
| 9 | Warm-up | clang-r15d | 4.600 | 5.247 | `7f78d3aec021ab01` | 0 | no |
| 9 | 1 | clang-r15d | 4.902 | 5.611 | `7f78d3aec021ab01` | 0 | yes |
| 9 | 2 | copy | 4.953 | 5.659 | `7f78d3aec021ab01` | 0 | yes |
| 9 | 3 | copy | 4.878 | 5.575 | `7f78d3aec021ab01` | 0 | yes |
| 9 | 4 | clang-r15d | 5.167 | 5.911 | `7f78d3aec021ab01` | 0 | yes |
| 10 | Warm-up | copy | 5.063 | 5.808 | `7f78d3aec021ab01` | 0 | no |
| 10 | 1 | copy | 4.953 | 5.670 | `7f78d3aec021ab01` | 0 | yes |
| 10 | 2 | clang-r15d | 5.444 | 6.278 | `7f78d3aec021ab01` | 0 | yes |
| 10 | 3 | clang-r15d | 4.936 | 5.632 | `7f78d3aec021ab01` | 0 | yes |
| 10 | 4 | copy | 4.727 | 5.399 | `7f78d3aec021ab01` | 0 | yes |
| 11 | Warm-up | clang-r15d | 4.945 | 5.649 | `7f78d3aec021ab01` | 0 | no |
| 11 | 1 | clang-r15d | 5.457 | 6.235 | `7f78d3aec021ab01` | 0 | yes |
| 11 | 2 | copy | 4.894 | 5.595 | `7f78d3aec021ab01` | 0 | yes |
| 11 | 3 | copy | 4.867 | 5.561 | `7f78d3aec021ab01` | 0 | yes |
| 11 | 4 | clang-r15d | 5.037 | 5.777 | `7f78d3aec021ab01` | 0 | yes |
| 12 | Warm-up | copy | 4.852 | 5.540 | `7f78d3aec021ab01` | 0 | no |
| 12 | 1 | copy | 4.876 | 5.583 | `7f78d3aec021ab01` | 0 | yes |
| 12 | 2 | clang-r15d | 4.465 | 5.098 | `7f78d3aec021ab01` | 0 | yes |
| 12 | 3 | clang-r15d | 4.695 | 5.352 | `7f78d3aec021ab01` | 0 | yes |
| 12 | 4 | copy | 4.751 | 5.430 | `7f78d3aec021ab01` | 0 | yes |
| 13 | Warm-up | clang-r15d | 4.918 | 5.635 | `7f78d3aec021ab01` | 0 | no |
| 13 | 1 | clang-r15d | 4.877 | 5.590 | `7f78d3aec021ab01` | 0 | yes |
| 13 | 2 | copy | 4.821 | 5.512 | `7f78d3aec021ab01` | 0 | yes |
| 13 | 3 | copy | 4.652 | 5.290 | `7f78d3aec021ab01` | 0 | yes |
| 13 | 4 | clang-r15d | 4.508 | 5.153 | `7f78d3aec021ab01` | 0 | yes |
| 14 | Warm-up | copy | 4.450 | 5.078 | `7f78d3aec021ab01` | 0 | no |
| 14 | 1 | copy | 4.599 | 5.267 | `7f78d3aec021ab01` | 0 | yes |
| 14 | 2 | clang-r15d | 4.750 | 5.430 | `7f78d3aec021ab01` | 0 | yes |
| 14 | 3 | clang-r15d | 4.689 | 5.361 | `7f78d3aec021ab01` | 0 | yes |
| 14 | 4 | copy | 4.854 | 5.549 | `7f78d3aec021ab01` | 0 | yes |
| 15 | Warm-up | clang-r15d | 4.948 | 5.669 | `7f78d3aec021ab01` | 0 | no |
| 15 | 1 | clang-r15d | 4.758 | 5.453 | `7f78d3aec021ab01` | 0 | yes |
| 15 | 2 | copy | 4.804 | 5.497 | `7f78d3aec021ab01` | 0 | yes |
| 15 | 3 | copy | 5.292 | 6.081 | `7f78d3aec021ab01` | 0 | yes |
| 15 | 4 | clang-r15d | 4.846 | 5.537 | `7f78d3aec021ab01` | 0 | yes |
| 16 | Warm-up | copy | 4.977 | 5.697 | `7f78d3aec021ab01` | 0 | no |
| 16 | 1 | copy | 5.048 | 5.784 | `7f78d3aec021ab01` | 0 | yes |
| 16 | 2 | clang-r15d | 5.022 | 5.741 | `7f78d3aec021ab01` | 0 | yes |
| 16 | 3 | clang-r15d | 5.287 | 6.051 | `7f78d3aec021ab01` | 0 | yes |
| 16 | 4 | copy | 5.036 | 5.762 | `7f78d3aec021ab01` | 0 | yes |

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9419 | 0.9414 |
| 2 | BAAB | 0.9998 | 1.0006 |
| 3 | ABBA | 0.9534 | 0.9524 |
| 4 | BAAB | 0.9546 | 0.9509 |
| 5 | ABBA | 0.9445 | 0.9440 |
| 6 | BAAB | 1.0077 | 1.0072 |
| 7 | ABBA | 0.9301 | 0.9320 |
| 8 | BAAB | 0.9389 | 0.9382 |
| 9 | ABBA | 0.9763 | 0.9749 |
| 10 | BAAB | 0.9325 | 0.9294 |
| 11 | ABBA | 0.9301 | 0.9287 |
| 12 | BAAB | 1.0510 | 1.0539 |
| 13 | ABBA | 1.0094 | 1.0054 |
| 14 | BAAB | 1.0015 | 1.0023 |
| 15 | ABBA | 1.0512 | 1.0535 |
| 16 | BAAB | 0.9782 | 0.9791 |

| Metric | Median | Pooled B/A | Mean | 95% t interval | df | Middle range | Below 1 | Above 1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Engine CPU | 0.9654 | 0.9734 | 0.9751 | [0.9532, 0.9969] | 15 | 0.9301–1.0510 | 11/16 | 5/16 |
| Wall | 0.9637 | 0.9729 | 0.9746 | [0.9523, 0.9970] | 15 | 0.9294–1.0535 | 10/16 | 6/16 |

| Block cohort | Metric | Leg 1 | Leg 2 | Leg 3 | Leg 4 |
|---|---|---:|---:|---:|---:|
| Odd | Engine CPU | 1.04185 | 0.99313 | 0.97260 | 0.99242 |
| Odd | Wall | 1.04269 | 0.99361 | 0.97152 | 0.99218 |
| Even | Engine CPU | 0.99848 | 1.01238 | 1.00545 | 0.98369 |
| Even | Wall | 0.99802 | 1.01360 | 1.00462 | 0.98376 |

Position means use each block's four timed legs. The middle range drops one block at each end.

[Inputs](sol2/job13/stepF/inputs.txt) · [Raw runs](sol2/job13/stepF/runs.jsonl.txt) · [Summary](sol2/job13/stepF/summary.txt) · [Command](sol2/job13/stepF-command.raw.txt)

### Step K — Clang kF against Clang r15d

- Arm A `clang-r15d` (`540e63c0b7cf2512f1716657aded48b0558022b49c0fe8489596195cf2035834`)
- Arm B `clang-kF` (`da5df215a6aa255261d4e5574474da7c82aad1a9e95df83e15d5b38963ef439d`)

Logical CPU 2. B/A compares summed timed B durations with summed timed A durations.

| Block | Leg | Engine | CPU (s) | Wall (s) | Trace | Exit | In ratios |
|---:|---|---|---:|---:|---|---:|---|
| 1 | Warm-up | clang-r15d | 4.504 | 5.286 | `7f78d3aec021ab01` | 0 | no |
| 1 | 1 | clang-r15d | 4.945 | 5.640 | `7f78d3aec021ab01` | 0 | yes |
| 1 | 2 | clang-kF | 4.844 | 5.593 | `7f78d3aec021ab01` | 0 | yes |
| 1 | 3 | clang-kF | 4.898 | 5.656 | `7f78d3aec021ab01` | 0 | yes |
| 1 | 4 | clang-r15d | 4.871 | 5.586 | `7f78d3aec021ab01` | 0 | yes |
| 2 | Warm-up | clang-kF | 5.075 | 5.847 | `7f78d3aec021ab01` | 0 | no |
| 2 | 1 | clang-kF | 4.902 | 5.647 | `7f78d3aec021ab01` | 0 | yes |
| 2 | 2 | clang-r15d | 5.289 | 6.102 | `7f78d3aec021ab01` | 0 | yes |
| 2 | 3 | clang-r15d | 4.878 | 5.579 | `7f78d3aec021ab01` | 0 | yes |
| 2 | 4 | clang-kF | 5.481 | 6.327 | `7f78d3aec021ab01` | 0 | yes |
| 3 | Warm-up | clang-r15d | 5.289 | 6.068 | `7f78d3aec021ab01` | 0 | no |
| 3 | 1 | clang-r15d | 4.703 | 5.390 | `7f78d3aec021ab01` | 0 | yes |
| 3 | 2 | clang-kF | 4.448 | 5.119 | `7f78d3aec021ab01` | 0 | yes |
| 3 | 3 | clang-kF | 4.528 | 5.204 | `7f78d3aec021ab01` | 0 | yes |
| 3 | 4 | clang-r15d | 4.874 | 5.566 | `7f78d3aec021ab01` | 0 | yes |
| 4 | Warm-up | clang-kF | 4.634 | 5.336 | `7f78d3aec021ab01` | 0 | no |
| 4 | 1 | clang-kF | 4.859 | 5.604 | `7f78d3aec021ab01` | 0 | yes |
| 4 | 2 | clang-r15d | 4.983 | 5.701 | `7f78d3aec021ab01` | 0 | yes |
| 4 | 3 | clang-r15d | 5.006 | 5.722 | `7f78d3aec021ab01` | 0 | yes |
| 4 | 4 | clang-kF | 4.553 | 5.239 | `7f78d3aec021ab01` | 0 | yes |
| 5 | Warm-up | clang-r15d | 4.668 | 5.330 | `7f78d3aec021ab01` | 0 | no |
| 5 | 1 | clang-r15d | 4.648 | 5.293 | `7f78d3aec021ab01` | 0 | yes |
| 5 | 2 | clang-kF | 4.557 | 5.238 | `7f78d3aec021ab01` | 0 | yes |
| 5 | 3 | clang-kF | 4.714 | 5.425 | `7f78d3aec021ab01` | 0 | yes |
| 5 | 4 | clang-r15d | 5.239 | 6.022 | `7f78d3aec021ab01` | 0 | yes |
| 6 | Warm-up | clang-kF | 4.610 | 5.303 | `7f78d3aec021ab01` | 0 | no |
| 6 | 1 | clang-kF | 4.446 | 5.100 | `7f78d3aec021ab01` | 0 | yes |
| 6 | 2 | clang-r15d | 4.869 | 5.586 | `7f78d3aec021ab01` | 0 | yes |
| 6 | 3 | clang-r15d | 5.349 | 6.100 | `7f78d3aec021ab01` | 0 | yes |
| 6 | 4 | clang-kF | 4.778 | 5.509 | `7f78d3aec021ab01` | 0 | yes |
| 7 | Warm-up | clang-r15d | 4.686 | 5.351 | `7f78d3aec021ab01` | 0 | no |
| 7 | 1 | clang-r15d | 4.839 | 5.543 | `7f78d3aec021ab01` | 0 | yes |
| 7 | 2 | clang-kF | 4.360 | 5.014 | `7f78d3aec021ab01` | 0 | yes |
| 7 | 3 | clang-kF | 4.644 | 5.339 | `7f78d3aec021ab01` | 0 | yes |
| 7 | 4 | clang-r15d | 4.927 | 5.648 | `7f78d3aec021ab01` | 0 | yes |
| 8 | Warm-up | clang-kF | 4.634 | 5.340 | `7f78d3aec021ab01` | 0 | no |
| 8 | 1 | clang-kF | 4.765 | 5.505 | `7f78d3aec021ab01` | 0 | yes |
| 8 | 2 | clang-r15d | 4.653 | 5.325 | `7f78d3aec021ab01` | 0 | yes |
| 8 | 3 | clang-r15d | 5.135 | 5.878 | `7f78d3aec021ab01` | 0 | yes |
| 8 | 4 | clang-kF | 4.853 | 5.596 | `7f78d3aec021ab01` | 0 | yes |
| 9 | Warm-up | clang-r15d | 4.904 | 5.642 | `7f78d3aec021ab01` | 0 | no |
| 9 | 1 | clang-r15d | 5.075 | 5.802 | `7f78d3aec021ab01` | 0 | yes |
| 9 | 2 | clang-kF | 5.317 | 6.158 | `7f78d3aec021ab01` | 0 | yes |
| 9 | 3 | clang-kF | 5.218 | 6.045 | `7f78d3aec021ab01` | 0 | yes |
| 9 | 4 | clang-r15d | 5.114 | 5.865 | `7f78d3aec021ab01` | 0 | yes |
| 10 | Warm-up | clang-kF | 4.766 | 5.504 | `7f78d3aec021ab01` | 0 | no |
| 10 | 1 | clang-kF | 4.769 | 5.489 | `7f78d3aec021ab01` | 0 | yes |
| 10 | 2 | clang-r15d | 5.155 | 5.917 | `7f78d3aec021ab01` | 0 | yes |
| 10 | 3 | clang-r15d | 5.012 | 5.732 | `7f78d3aec021ab01` | 0 | yes |
| 10 | 4 | clang-kF | 5.122 | 5.904 | `7f78d3aec021ab01` | 0 | yes |
| 11 | Warm-up | clang-r15d | 5.159 | 5.938 | `7f78d3aec021ab01` | 0 | no |
| 11 | 1 | clang-r15d | 5.698 | 6.543 | `7f78d3aec021ab01` | 0 | yes |
| 11 | 2 | clang-kF | 5.286 | 6.139 | `7f78d3aec021ab01` | 0 | yes |
| 11 | 3 | clang-kF | 4.821 | 5.555 | `7f78d3aec021ab01` | 0 | yes |
| 11 | 4 | clang-r15d | 5.419 | 6.237 | `7f78d3aec021ab01` | 0 | yes |
| 12 | Warm-up | clang-kF | 5.142 | 5.929 | `7f78d3aec021ab01` | 0 | no |
| 12 | 1 | clang-kF | 5.023 | 5.801 | `7f78d3aec021ab01` | 0 | yes |
| 12 | 2 | clang-r15d | 5.170 | 5.936 | `7f78d3aec021ab01` | 0 | yes |
| 12 | 3 | clang-r15d | 4.596 | 5.257 | `7f78d3aec021ab01` | 0 | yes |
| 12 | 4 | clang-kF | 4.777 | 5.501 | `7f78d3aec021ab01` | 0 | yes |
| 13 | Warm-up | clang-r15d | 4.999 | 5.747 | `7f78d3aec021ab01` | 0 | no |
| 13 | 1 | clang-r15d | 4.674 | 5.349 | `7f78d3aec021ab01` | 0 | yes |
| 13 | 2 | clang-kF | 4.932 | 5.673 | `7f78d3aec021ab01` | 0 | yes |
| 13 | 3 | clang-kF | 5.042 | 5.812 | `7f78d3aec021ab01` | 0 | yes |
| 13 | 4 | clang-r15d | 4.997 | 5.721 | `7f78d3aec021ab01` | 0 | yes |
| 14 | Warm-up | clang-kF | 4.645 | 5.350 | `7f78d3aec021ab01` | 0 | no |
| 14 | 1 | clang-kF | 4.966 | 5.723 | `7f78d3aec021ab01` | 0 | yes |
| 14 | 2 | clang-r15d | 4.824 | 5.516 | `7f78d3aec021ab01` | 0 | yes |
| 14 | 3 | clang-r15d | 4.963 | 5.673 | `7f78d3aec021ab01` | 0 | yes |
| 14 | 4 | clang-kF | 5.229 | 6.083 | `7f78d3aec021ab01` | 0 | yes |
| 15 | Warm-up | clang-r15d | 5.300 | 6.076 | `7f78d3aec021ab01` | 0 | no |
| 15 | 1 | clang-r15d | 5.133 | 5.879 | `7f78d3aec021ab01` | 0 | yes |
| 15 | 2 | clang-kF | 4.910 | 5.649 | `7f78d3aec021ab01` | 0 | yes |
| 15 | 3 | clang-kF | 5.146 | 5.924 | `7f78d3aec021ab01` | 0 | yes |
| 15 | 4 | clang-r15d | 5.182 | 5.956 | `7f78d3aec021ab01` | 0 | yes |
| 16 | Warm-up | clang-kF | 5.209 | 6.000 | `7f78d3aec021ab01` | 0 | no |
| 16 | 1 | clang-kF | 4.533 | 5.222 | `7f78d3aec021ab01` | 0 | yes |
| 16 | 2 | clang-r15d | 5.157 | 5.906 | `7f78d3aec021ab01` | 0 | yes |
| 16 | 3 | clang-r15d | 5.077 | 5.824 | `7f78d3aec021ab01` | 0 | yes |
| 16 | 4 | clang-kF | 4.730 | 5.443 | `7f78d3aec021ab01` | 0 | yes |

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9925 | 1.0020 |
| 2 | BAAB | 1.0213 | 1.0251 |
| 3 | ABBA | 0.9372 | 0.9421 |
| 4 | BAAB | 0.9422 | 0.9492 |
| 5 | ABBA | 0.9378 | 0.9424 |
| 6 | BAAB | 0.9027 | 0.9079 |
| 7 | ABBA | 0.9220 | 0.9251 |
| 8 | BAAB | 0.9826 | 0.9908 |
| 9 | ABBA | 1.0340 | 1.0460 |
| 10 | BAAB | 0.9729 | 0.9780 |
| 11 | ABBA | 0.9091 | 0.9151 |
| 12 | BAAB | 1.0035 | 1.0098 |
| 13 | ABBA | 1.0314 | 1.0374 |
| 14 | BAAB | 1.0417 | 1.0552 |
| 15 | ABBA | 0.9748 | 0.9779 |
| 16 | BAAB | 0.9051 | 0.9091 |

| Metric | Median | Pooled B/A | Mean | 95% t interval | df | Middle range | Below 1 | Above 1 | Reading |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Engine CPU | 0.9739 | 0.9688 | 0.9694 | [0.9437, 0.9952] | 15 | 0.9051–1.0340 | 11/16 | 5/16 | not measurable here |
| Wall | 0.9780 | 0.9752 | 0.9758 | [0.9491, 1.0026] | 15 | 0.9091–1.0460 | 10/16 | 6/16 | not measurable here |

| Block cohort | Metric | Leg 1 | Leg 2 | Leg 3 | Leg 4 |
|---|---|---:|---:|---:|---:|
| Odd | Engine CPU | 1.00498 | 0.97764 | 0.98809 | 1.02929 |
| Odd | Wall | 1.00053 | 0.98107 | 0.99093 | 1.02747 |
| Even | Engine CPU | 0.96939 | 1.01576 | 1.01436 | 1.00049 |
| Even | Wall | 0.97205 | 1.01379 | 1.00961 | 1.00455 |

Position means use each block's four timed legs. The middle range drops one block at each end.

[Inputs](sol2/job13/stepK/inputs.txt) · [Raw runs](sol2/job13/stepK/runs.jsonl.txt) · [Summary](sol2/job13/stepK/summary.txt) · [Command](sol2/job13/stepK-command.raw.txt)

### Step 4 — frozen GCC kF-pgo against r15d-pgo

- Arm A `gcc-r15d` (`96f50b3eb6d4f05cfa8291eaab56ea9c943a8e98fb3b248fff3b9138fcce6808`)
- Arm B `gcc-kF` (`90413337a79410b49b76cbec4b2e1a77344bcc2385fecd5950f1f2ababd1539a`)

Logical CPU 2. B/A compares summed timed B durations with summed timed A durations.

| Block | Leg | Engine | CPU (s) | Wall (s) | Trace | Exit | In ratios |
|---:|---|---|---:|---:|---|---:|---|
| 1 | Warm-up | gcc-r15d | 5.402 | 6.288 | `7f78d3aec021ab01` | 0 | no |
| 1 | 1 | gcc-r15d | 5.288 | 6.004 | `7f78d3aec021ab01` | 0 | yes |
| 1 | 2 | gcc-kF | 4.975 | 5.730 | `7f78d3aec021ab01` | 0 | yes |
| 1 | 3 | gcc-kF | 5.383 | 6.103 | `7f78d3aec021ab01` | 0 | yes |
| 1 | 4 | gcc-r15d | 5.267 | 5.969 | `7f78d3aec021ab01` | 0 | yes |
| 2 | Warm-up | gcc-kF | 5.432 | 6.243 | `7f78d3aec021ab01` | 0 | no |
| 2 | 1 | gcc-kF | 5.425 | 6.225 | `7f78d3aec021ab01` | 0 | yes |
| 2 | 2 | gcc-r15d | 5.530 | 6.279 | `7f78d3aec021ab01` | 0 | yes |
| 2 | 3 | gcc-r15d | 5.258 | 5.989 | `7f78d3aec021ab01` | 0 | yes |
| 2 | 4 | gcc-kF | 5.019 | 5.749 | `7f78d3aec021ab01` | 0 | yes |
| 3 | Warm-up | gcc-r15d | 5.195 | 5.912 | `7f78d3aec021ab01` | 0 | no |
| 3 | 1 | gcc-r15d | 5.167 | 5.864 | `7f78d3aec021ab01` | 0 | yes |
| 3 | 2 | gcc-kF | 5.058 | 5.809 | `7f78d3aec021ab01` | 0 | yes |
| 3 | 3 | gcc-kF | 4.868 | 5.582 | `7f78d3aec021ab01` | 0 | yes |
| 3 | 4 | gcc-r15d | 5.040 | 5.729 | `7f78d3aec021ab01` | 0 | yes |
| 4 | Warm-up | gcc-kF | 5.393 | 6.229 | `7f78d3aec021ab01` | 0 | no |
| 4 | 1 | gcc-kF | 4.806 | 5.503 | `7f78d3aec021ab01` | 0 | yes |
| 4 | 2 | gcc-r15d | 4.917 | 5.570 | `7f78d3aec021ab01` | 0 | yes |
| 4 | 3 | gcc-r15d | 5.448 | 6.205 | `7f78d3aec021ab01` | 0 | yes |
| 4 | 4 | gcc-kF | 5.444 | 6.271 | `7f78d3aec021ab01` | 0 | yes |
| 5 | Warm-up | gcc-r15d | 5.500 | 6.275 | `7f78d3aec021ab01` | 0 | no |
| 5 | 1 | gcc-r15d | 5.046 | 5.742 | `7f78d3aec021ab01` | 0 | yes |
| 5 | 2 | gcc-kF | 4.828 | 5.519 | `7f78d3aec021ab01` | 0 | yes |
| 5 | 3 | gcc-kF | 4.764 | 5.457 | `7f78d3aec021ab01` | 0 | yes |
| 5 | 4 | gcc-r15d | 5.311 | 6.041 | `7f78d3aec021ab01` | 0 | yes |
| 6 | Warm-up | gcc-kF | 5.003 | 5.742 | `7f78d3aec021ab01` | 0 | no |
| 6 | 1 | gcc-kF | 4.748 | 5.427 | `7f78d3aec021ab01` | 0 | yes |
| 6 | 2 | gcc-r15d | 5.488 | 6.234 | `7f78d3aec021ab01` | 0 | yes |
| 6 | 3 | gcc-r15d | 5.505 | 6.267 | `7f78d3aec021ab01` | 0 | yes |
| 6 | 4 | gcc-kF | 4.727 | 5.411 | `7f78d3aec021ab01` | 0 | yes |
| 7 | Warm-up | gcc-r15d | 5.233 | 5.953 | `7f78d3aec021ab01` | 0 | no |
| 7 | 1 | gcc-r15d | 4.839 | 5.478 | `7f78d3aec021ab01` | 0 | yes |
| 7 | 2 | gcc-kF | 5.252 | 6.002 | `7f78d3aec021ab01` | 0 | yes |
| 7 | 3 | gcc-kF | 5.080 | 5.849 | `7f78d3aec021ab01` | 0 | yes |
| 7 | 4 | gcc-r15d | 5.584 | 6.371 | `7f78d3aec021ab01` | 0 | yes |
| 8 | Warm-up | gcc-kF | 5.187 | 5.947 | `7f78d3aec021ab01` | 0 | no |
| 8 | 1 | gcc-kF | 4.923 | 5.655 | `7f78d3aec021ab01` | 0 | yes |
| 8 | 2 | gcc-r15d | 5.055 | 5.722 | `7f78d3aec021ab01` | 0 | yes |
| 8 | 3 | gcc-r15d | 5.181 | 5.883 | `7f78d3aec021ab01` | 0 | yes |
| 8 | 4 | gcc-kF | 4.841 | 5.523 | `7f78d3aec021ab01` | 0 | yes |

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9813 | 0.9884 |
| 2 | BAAB | 0.9682 | 0.9760 |
| 3 | ABBA | 0.9725 | 0.9827 |
| 4 | BAAB | 0.9889 | 0.9999 |
| 5 | ABBA | 0.9261 | 0.9314 |
| 6 | BAAB | 0.8619 | 0.8670 |
| 7 | ABBA | 0.9912 | 1.0001 |
| 8 | BAAB | 0.9539 | 0.9632 |

| Metric | Median | Pooled B/A | Mean | 95% t interval | df | Middle range | Below 1 | Above 1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Engine CPU | 0.9703 | 0.9549 | 0.9555 | [0.9193, 0.9917] | 7 | 0.9261–0.9889 | 8/8 | 0/8 |
| Wall | 0.9793 | 0.9630 | 0.9636 | [0.9260, 1.0012] | 7 | 0.9314–0.9999 | 7/8 | 1/8 |

| Block cohort | Metric | Leg 1 | Leg 2 | Leg 3 | Leg 4 |
|---|---|---:|---:|---:|---:|
| Odd | Engine CPU | 0.99556 | 0.98420 | 0.98273 | 1.03752 |
| Odd | Wall | 0.99077 | 0.98918 | 0.98581 | 1.03424 |
| Even | Engine CPU | 0.96676 | 1.01983 | 1.03993 | 0.97348 |
| Even | Wall | 0.97122 | 1.01380 | 1.03727 | 0.97771 |

Position means use each block's four timed legs. The middle range drops one block at each end.

[Inputs](sol2/job13/step4/inputs.txt) · [Raw runs](sol2/job13/step4/runs.jsonl.txt) · [Summary](sol2/job13/step4/summary.txt) · [Command](sol2/job13/step4-command.raw.txt)

## Facts

- Every complete campaign retained the W signature in 160 timed runs and 40 warm-ups. Both node totals were checked each time. [Readback script](sol2/job13/timing_readback.py.txt)
- Clang kF/r15d pooled at **0.9688** CPU and **0.9752** wall. CPU was lower in 11/16 blocks. The declared readings were **not measurable here** for CPU and **not measurable here** for wall. [Clang comparison](sol2/job13/stepK/summary.txt)
- The frozen GCC pair on the same workload pooled at **0.9549** CPU, with 8/8 blocks below one. This optional comparison used the Job 7/9 GCC LTO+PGO builds and has no same-workload floor. [GCC comparison](sol2/job13/step4/summary.txt) · [Step 4 budget check](sol2/job13/step4-budget.raw.txt)


## Suspicions

The identical-binary Clang CPU t interval also lies below one. Shared-host timing and run order may contribute to that shift. The declared result uses the middle range and sign count. [Clang control](sol2/job13/stepF/summary.txt)

The same workload is used for the two compiler comparisons. The compiler and profile training recipe both differ between the Clang and frozen GCC builds, so their individual contributions remain unresolved.

## What this check cannot see

The PC's own net (larger), its clang 23 for Windows, its processor with 16 engines playing at once, its own
self-play openings (8 random plies from the start position).

## What I did not do

The experiment used cloud builds, synthetic net768 and a single pinned engine for timing. The branch contains text evidence for each step. [Publication layout](sol2/job13/publication-layout.raw.txt)

## What I am not sure about

Production data throughput on the owner's PC remains unmeasured. The recorded signature covers emitted moves and node totals. Internal node visitation order is outside the trace.
