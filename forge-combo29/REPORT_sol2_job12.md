# sol2 — Job 12 whole-game identity and Clang timing

## Step 0 — frozen GCC builds and machine

| Frozen executable | SHA-256 | Default bench 11 | Default bench 13 | Default perft 5 | PC20/net768 bench 11 | PC20/net768 bench 13 |
|---|---|---:|---:|---:|---:|---:|
| r15d-pgo | `96f50b3eb6d4f05cfa8291eaab56ea9c943a8e98fb3b248fff3b9138fcce6808` | 312,866 | 862,329 | 4,865,609 | 882,074 | 4,275,906 |
| kF-pgo | `90413337a79410b49b76cbec4b2e1a77344bcc2385fecd5950f1f2ababd1539a` | 312,866 | 862,329 | 4,865,609 | 882,074 | 4,275,906 |

The default pins ran in fresh processes without option overrides. The PC20/net768 pins used Threads 1, Hash 16 MiB and OwnBook false. Both GCC 14.2.0 LTO+PGO builds also matched the Job 10 known answer on the first 12 saved openings at `go nodes 20000`. Each gave 1,373 searches, 15,527,588 last-info nodes and trace `73ecbb5eedc59271`. [Build and raw gates](sol2/job12/step0-command-and-readback.raw.txt) · [Job 10 workload](REPORT_sol2_job10.md) · [Consolidated kF build](REPORT_sol2_job9.md)

The cloud VM reports AMD EPYC 9V74 with five logical CPUs on five guest cores, one thread per core and 32 MiB L3. The cgroup capacity is four CPU equivalents. Part A used pinned workers on CPUs 1–4. Part B's one-engine runs used CPU 2. [Machine](sol2/job12/step0-machine.txt)

## Part A controls — repeat and planted change passed

Both controls used physical book lines 4001–4020, PC20, net768, Threads 1, Hash 16 MiB and `go softnodes 2000`. Two runs of frozen r15d-pgo agreed in all 20 games. A separate pair used the same binary with `LmrQuietBase=60` on B after the usual PC20 setting of 93. All 20 games differed. This checked that the comparison detects a deliberate search change. [Repeated control](sol2/job12/control/repeat.jsonl.txt) · [Changed control](sol2/job12/control/changed.jsonl.txt) · [Independent control readback](sol2/job12/control/readback.raw.txt)

The first changed control game diverged at book line 4001, ply 1. A played `b8d7` at 2,098 last-info nodes, and B played `b8a6` at 4,978. The readback preserves both original `info depth` and `bestmove` lines. [First control difference](sol2/job12/control/readback.raw.txt)

## Prediction graded

The prediction was published alone at `20f4ea1533fc11b982543143cb90e37efb91e654` after Step 0 and both Part A controls, before the wider game replay.

| Quantity | Prediction | Observed | Within range |
|---|---:|---:|---|
| A1 differing games | 0–3 | 0 | yes |
| A2 differing games | 0–1 | 0 | yes |
| Clang ThinLTO without PGO Step F CPU minimum | 0.950–0.985 | 0.9189 | no |
| Clang ThinLTO without PGO Step F CPU maximum | 1.020–1.065 | 1.0741 | no |
| Clang ThinLTO without PGO Step K CPU median | 0.895–0.950 | 0.9324 | yes |
| Clang ThinLTO with PGO Step F CPU minimum | 0.950–0.985 | 0.9638 | yes |
| Clang ThinLTO with PGO Step F CPU maximum | 1.020–1.065 | 1.0246 | yes |
| Clang ThinLTO with PGO Step K CPU median | 0.895–0.950 | 0.9815 | no |

[Original prediction](sol2/job12/prediction.txt) · [UTC checkpoints](sol2/job12/stamps.txt)

## Part A — whole-game identity

Each arm used its frozen GCC executable to play both sides under PC20, synthetic net768, Threads 1, Hash 16 MiB and OwnBook false. The driver kept both engine processes alive within each shard, sent `ucinewgame` and `isready` before each game, and passed each original six-field FEN followed by the move history. Python 3.12.14 with python-chess 1.11.2 checked `is_game_over(claim_draw=True)` before the next move. There was a 300-ply cap. The complete canonical pair for every played ply was best move and last-info node count. [Driver](sol2/job12/fen_identity.py.txt) · [Shard orchestrator and validation](sol2/job12/part_a_shards.py.txt) · [Python package receipt](sol2/job12/python-chess-install.raw.txt)

The official UHO Lichess book SHA-256 was `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. The readback checked inclusive physical line coverage, exact FENs, complete canonical traces, and matching exits for the four pinned shards in each part. [Pinned book receipt](sol2/job12/step0-command-and-readback.raw.txt)

| Part | Physical book lines | Node command | Game pairs | Equal | Differ | Searches per arm | Last-info nodes per arm | Coverage |
|---|---|---|---:|---:|---:|---:|---:|---|
| A1 | 4001–5500 | `go softnodes 2000` | 1,500 | 1,500 | 0 | 171,408 / 171,408 | 589,582,250 / 589,582,250 | complete |
| A2 | 6001–6300 | `go nodes 20000` | 300 | 300 | 0 | 29,364 / 29,364 | 346,159,155 / 346,159,155 | complete |

[A1 raw shards](sol2/job12/A1) · [A1 readback](sol2/job12/A1/readback.raw.json.txt) · [A2 raw shards](sol2/job12/A2) · [A2 readback](sol2/job12/A2/readback.raw.json.txt)

## Part B — Clang builds, identity and fixed-node timing

The workspace-local install provided Debian Clang, LLVM and LLD 19.1.7. Both variants used the original r15d and kF scratch trees, CMake Release, C++20, `-O3 -DNDEBUG -ffp-contract=off -fno-fast-math -march=x86-64-v4`, the existing Forge defines, `-flto=thin` and the system libstdc++ 6.0.33. [Toolchain receipt](sol2/job12/clang-install-receipt.raw.txt) · [Build commands](sol2/job12/clang_build.sh.txt)

| Recipe | Arm | Executable SHA-256 | Default pins, bench 11 / 13 / perft 5 | PC20/net768 pins, bench 11 / 13 | 12-game searches / last-info nodes / trace | Evidence |
|---|---|---|---|---|---|---|
| Clang ThinLTO without PGO | r15d | `df7a41aaa9e8cd9bc76e3b6169b6e59cb1e4754fc5385dc5350276e27a7daade` | 312,866 / 862,329 / 4,865,609 | 882,074 / 4,275,906 | 1,373 / 15,527,588 / `73ecbb5eedc59271` | [commands](sol2/job12/clang-plain/r15d-command.raw.txt), [trace](sol2/job12/clang-plain/r15d-identity.raw.txt) |
| Clang ThinLTO without PGO | kF | `d84fafe6f5d19a7f040f602b4a68a8b8d88c5ba8987a8bbe4923174a791df19b` | 312,866 / 862,329 / 4,865,609 | 882,074 / 4,275,906 | 1,373 / 15,527,588 / `73ecbb5eedc59271` | [commands](sol2/job12/clang-plain/kF-command.raw.txt), [trace](sol2/job12/clang-plain/kF-identity.raw.txt) |
| Clang ThinLTO with PGO | r15d | `1f6961c55f774edaa7f080bc73f209acb434b8acceeb7bab491e238708cdfdf2` | 312,866 / 862,329 / 4,865,609 | 882,074 / 4,275,906 | 1,373 / 15,527,588 / `73ecbb5eedc59271` | [commands](sol2/job12/clang-pgo/r15d-command.raw.txt), [trace](sol2/job12/clang-pgo/r15d-identity.raw.txt) |
| Clang ThinLTO with PGO | kF | `a08a2442140a067d4e75d9176b92df0cdcc119afb39c9c1cf2ee174c8b559a7c` | 312,866 / 862,329 / 4,865,609 | 882,074 / 4,275,906 | 1,373 / 15,527,588 / `73ecbb5eedc59271` | [commands](sol2/job12/clang-pgo/kF-command.raw.txt), [trace](sol2/job12/clang-pgo/kF-identity.raw.txt) |

For the profiled recipe each arm trained its own `-fprofile-instr-generate` executable with the same pinned 12-game fixed-node replay used for its timing. LLVM merged a private profile per arm and the clean use build used `-fprofile-instr-use` and `-Werror=profile-instr-out-of-date`. The training and final identity signatures both matched the Job 10 known answer. [r15d profile](sol2/job12/clang-pgo/r15d-profile-receipt.raw.txt) · [kF profile](sol2/job12/clang-pgo/kF-profile-receipt.raw.txt)


Each campaign used one engine on logical CPU 2 and eight blocks. Odd blocks used ABBA and even blocks BAAB. Each had one recorded first-arm warm-up, excluded from the ratios. Engine CPU is reaped user plus system time. Wall is the full driver interval. To count as measured, the candidate median had to lie outside the same-recipe identical-binary floor with at least seven of eight block ratios on one side of one. [Timing harness](sol2/job12/clang_balanced_timing.py.txt) · [Independent readback](sol2/job12/clang_timing_readback.py.txt)

Part B's protocol uses one engine on one logical CPU, PC20, Threads 1, Hash 16 MiB, net768 and `go nodes 20000`. Each eligible run records 12 games, 1,373 searches, 15,527,588 last-info nodes and `73ecbb5eedc59271`.

Step K is MEASURED when its median is outside the corresponding Step F range and at least seven of eight blocks are on one side of 1. Warm-ups are excluded. [Pinned workload](sol2/job10/known-answer.txt)

### Clang without PGO

#### Step F — identical-binary floor

Logical CPU 2. Arm B durations divided by arm A durations.

- A `clang-r15d` (`df7a41aaa9e8cd9bc76e3b6169b6e59cb1e4754fc5385dc5350276e27a7daade`)
- B `copy` (`df7a41aaa9e8cd9bc76e3b6169b6e59cb1e4754fc5385dc5350276e27a7daade`)

| Block | Leg | Engine | CPU (s) | Wall (s) | Trace | Exit | In ratios |
|---:|---|---|---:|---:|---|---:|---|
| 1 | Warm-up | clang-r15d | 15.269 | 15.504 | `73ecbb5eedc59271` | 0 | no |
| 1 | 1 | clang-r15d | 15.014 | 15.256 | `73ecbb5eedc59271` | 0 | yes |
| 1 | 2 | copy | 15.283 | 15.530 | `73ecbb5eedc59271` | 0 | yes |
| 1 | 3 | copy | 15.483 | 15.738 | `73ecbb5eedc59271` | 0 | yes |
| 1 | 4 | clang-r15d | 16.589 | 16.874 | `73ecbb5eedc59271` | 0 | yes |
| 2 | Warm-up | copy | 16.483 | 16.793 | `73ecbb5eedc59271` | 0 | no |
| 2 | 1 | copy | 16.163 | 16.463 | `73ecbb5eedc59271` | 0 | yes |
| 2 | 2 | clang-r15d | 17.808 | 18.170 | `73ecbb5eedc59271` | 0 | yes |
| 2 | 3 | clang-r15d | 18.345 | 18.766 | `73ecbb5eedc59271` | 0 | yes |
| 2 | 4 | copy | 17.059 | 17.390 | `73ecbb5eedc59271` | 0 | yes |
| 3 | Warm-up | clang-r15d | 15.349 | 15.608 | `73ecbb5eedc59271` | 0 | no |
| 3 | 1 | clang-r15d | 15.669 | 15.939 | `73ecbb5eedc59271` | 0 | yes |
| 3 | 2 | copy | 15.866 | 16.179 | `73ecbb5eedc59271` | 0 | yes |
| 3 | 3 | copy | 15.654 | 15.954 | `73ecbb5eedc59271` | 0 | yes |
| 3 | 4 | clang-r15d | 16.912 | 17.248 | `73ecbb5eedc59271` | 0 | yes |
| 4 | Warm-up | copy | 15.949 | 16.226 | `73ecbb5eedc59271` | 0 | no |
| 4 | 1 | copy | 15.529 | 15.794 | `73ecbb5eedc59271` | 0 | yes |
| 4 | 2 | clang-r15d | 15.909 | 16.174 | `73ecbb5eedc59271` | 0 | yes |
| 4 | 3 | clang-r15d | 15.310 | 15.560 | `73ecbb5eedc59271` | 0 | yes |
| 4 | 4 | copy | 14.922 | 15.169 | `73ecbb5eedc59271` | 0 | yes |
| 5 | Warm-up | clang-r15d | 16.062 | 16.328 | `73ecbb5eedc59271` | 0 | no |
| 5 | 1 | clang-r15d | 15.947 | 16.233 | `73ecbb5eedc59271` | 0 | yes |
| 5 | 2 | copy | 15.589 | 15.864 | `73ecbb5eedc59271` | 0 | yes |
| 5 | 3 | copy | 15.204 | 15.468 | `73ecbb5eedc59271` | 0 | yes |
| 5 | 4 | clang-r15d | 15.475 | 15.737 | `73ecbb5eedc59271` | 0 | yes |
| 6 | Warm-up | copy | 15.747 | 16.019 | `73ecbb5eedc59271` | 0 | no |
| 6 | 1 | copy | 15.611 | 15.870 | `73ecbb5eedc59271` | 0 | yes |
| 6 | 2 | clang-r15d | 15.081 | 15.335 | `73ecbb5eedc59271` | 0 | yes |
| 6 | 3 | clang-r15d | 15.036 | 15.304 | `73ecbb5eedc59271` | 0 | yes |
| 6 | 4 | copy | 15.991 | 16.284 | `73ecbb5eedc59271` | 0 | yes |
| 7 | Warm-up | clang-r15d | 15.685 | 15.953 | `73ecbb5eedc59271` | 0 | no |
| 7 | 1 | clang-r15d | 15.628 | 15.923 | `73ecbb5eedc59271` | 0 | yes |
| 7 | 2 | copy | 16.449 | 16.757 | `73ecbb5eedc59271` | 0 | yes |
| 7 | 3 | copy | 17.655 | 17.978 | `73ecbb5eedc59271` | 0 | yes |
| 7 | 4 | clang-r15d | 16.124 | 16.415 | `73ecbb5eedc59271` | 0 | yes |
| 8 | Warm-up | copy | 16.419 | 16.695 | `73ecbb5eedc59271` | 0 | no |
| 8 | 1 | copy | 16.201 | 16.479 | `73ecbb5eedc59271` | 0 | yes |
| 8 | 2 | clang-r15d | 14.727 | 14.948 | `73ecbb5eedc59271` | 0 | yes |
| 8 | 3 | clang-r15d | 16.773 | 17.057 | `73ecbb5eedc59271` | 0 | yes |
| 8 | 4 | copy | 15.564 | 15.830 | `73ecbb5eedc59271` | 0 | yes |

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9735 | 0.9732 |
| 2 | BAAB | 0.9189 | 0.9166 |
| 3 | ABBA | 0.9674 | 0.9682 |
| 4 | BAAB | 0.9754 | 0.9757 |
| 5 | ABBA | 0.9800 | 0.9800 |
| 6 | BAAB | 1.0493 | 1.0495 |
| 7 | ABBA | 1.0741 | 1.0741 |
| 8 | BAAB | 1.0084 | 1.0095 |

| Metric | Median | Pooled | Range | Below 1 | Above 1 | Reading |
|---|---:|---:|---:|---:|---:|---|
| Engine CPU | 0.9777 | 0.9917 | 0.9189–1.0741 | 5/8 | 3/8 | Identical-binary floor |
| Wall | 0.9779 | 0.9916 | 0.9166–1.0741 | 5/8 | 3/8 | Identical-binary floor |

| Block cohort | Metric | Leg 1 | Leg 2 | Leg 3 | Leg 4 |
|---|---|---:|---:|---:|---:|
| Odd | Engine CPU | 0.97879 | 0.99291 | 1.00491 | 1.02339 |
| Odd | Wall | 0.97849 | 0.99309 | 1.00486 | 1.02356 |
| Even | Engine CPU | 0.99381 | 0.99179 | 1.02143 | 0.99297 |
| Even | Wall | 0.99344 | 0.99128 | 1.02221 | 0.99306 |

[Inputs](sol2/job12/clang-plain/stepF/inputs.txt) · [Raw runs](sol2/job12/clang-plain/stepF/runs.jsonl.txt) · [Summary](sol2/job12/clang-plain/stepF/summary.txt) · [Command](sol2/job12/clang-plain/stepF-command.raw.txt)

#### Step K — Clang kF against Clang r15d

Logical CPU 2. Arm B durations divided by arm A durations.

- A `clang-r15d` (`df7a41aaa9e8cd9bc76e3b6169b6e59cb1e4754fc5385dc5350276e27a7daade`)
- B `clang-kF` (`d84fafe6f5d19a7f040f602b4a68a8b8d88c5ba8987a8bbe4923174a791df19b`)

| Block | Leg | Engine | CPU (s) | Wall (s) | Trace | Exit | In ratios |
|---:|---|---|---:|---:|---|---:|---|
| 1 | Warm-up | clang-r15d | 15.134 | 15.369 | `73ecbb5eedc59271` | 0 | no |
| 1 | 1 | clang-r15d | 14.558 | 14.788 | `73ecbb5eedc59271` | 0 | yes |
| 1 | 2 | clang-kF | 13.455 | 13.664 | `73ecbb5eedc59271` | 0 | yes |
| 1 | 3 | clang-kF | 14.544 | 14.783 | `73ecbb5eedc59271` | 0 | yes |
| 1 | 4 | clang-r15d | 15.639 | 15.888 | `73ecbb5eedc59271` | 0 | yes |
| 2 | Warm-up | clang-kF | 14.959 | 15.216 | `73ecbb5eedc59271` | 0 | no |
| 2 | 1 | clang-kF | 14.826 | 15.074 | `73ecbb5eedc59271` | 0 | yes |
| 2 | 2 | clang-r15d | 16.015 | 16.293 | `73ecbb5eedc59271` | 0 | yes |
| 2 | 3 | clang-r15d | 15.285 | 15.533 | `73ecbb5eedc59271` | 0 | yes |
| 2 | 4 | clang-kF | 15.214 | 15.471 | `73ecbb5eedc59271` | 0 | yes |
| 3 | Warm-up | clang-r15d | 17.263 | 17.592 | `73ecbb5eedc59271` | 0 | no |
| 3 | 1 | clang-r15d | 15.414 | 15.667 | `73ecbb5eedc59271` | 0 | yes |
| 3 | 2 | clang-kF | 15.379 | 15.668 | `73ecbb5eedc59271` | 0 | yes |
| 3 | 3 | clang-kF | 14.077 | 14.305 | `73ecbb5eedc59271` | 0 | yes |
| 3 | 4 | clang-r15d | 16.826 | 17.129 | `73ecbb5eedc59271` | 0 | yes |
| 4 | Warm-up | clang-kF | 14.859 | 15.115 | `73ecbb5eedc59271` | 0 | no |
| 4 | 1 | clang-kF | 14.670 | 14.915 | `73ecbb5eedc59271` | 0 | yes |
| 4 | 2 | clang-r15d | 15.275 | 15.509 | `73ecbb5eedc59271` | 0 | yes |
| 4 | 3 | clang-r15d | 15.603 | 15.881 | `73ecbb5eedc59271` | 0 | yes |
| 4 | 4 | clang-kF | 14.700 | 14.942 | `73ecbb5eedc59271` | 0 | yes |
| 5 | Warm-up | clang-r15d | 15.350 | 15.598 | `73ecbb5eedc59271` | 0 | no |
| 5 | 1 | clang-r15d | 15.423 | 15.676 | `73ecbb5eedc59271` | 0 | yes |
| 5 | 2 | clang-kF | 14.908 | 15.156 | `73ecbb5eedc59271` | 0 | yes |
| 5 | 3 | clang-kF | 14.153 | 14.393 | `73ecbb5eedc59271` | 0 | yes |
| 5 | 4 | clang-r15d | 15.574 | 15.828 | `73ecbb5eedc59271` | 0 | yes |
| 6 | Warm-up | clang-kF | 15.191 | 15.459 | `73ecbb5eedc59271` | 0 | no |
| 6 | 1 | clang-kF | 14.550 | 14.796 | `73ecbb5eedc59271` | 0 | yes |
| 6 | 2 | clang-r15d | 15.845 | 16.120 | `73ecbb5eedc59271` | 0 | yes |
| 6 | 3 | clang-r15d | 15.436 | 15.687 | `73ecbb5eedc59271` | 0 | yes |
| 6 | 4 | clang-kF | 14.164 | 14.404 | `73ecbb5eedc59271` | 0 | yes |
| 7 | Warm-up | clang-r15d | 14.222 | 14.437 | `73ecbb5eedc59271` | 0 | no |
| 7 | 1 | clang-r15d | 16.281 | 16.563 | `73ecbb5eedc59271` | 0 | yes |
| 7 | 2 | clang-kF | 14.539 | 14.781 | `73ecbb5eedc59271` | 0 | yes |
| 7 | 3 | clang-kF | 14.700 | 14.942 | `73ecbb5eedc59271` | 0 | yes |
| 7 | 4 | clang-r15d | 15.428 | 15.678 | `73ecbb5eedc59271` | 0 | yes |
| 8 | Warm-up | clang-kF | 14.780 | 15.024 | `73ecbb5eedc59271` | 0 | no |
| 8 | 1 | clang-kF | 15.180 | 15.450 | `73ecbb5eedc59271` | 0 | yes |
| 8 | 2 | clang-r15d | 15.557 | 15.812 | `73ecbb5eedc59271` | 0 | yes |
| 8 | 3 | clang-r15d | 15.201 | 15.469 | `73ecbb5eedc59271` | 0 | yes |
| 8 | 4 | clang-kF | 14.580 | 14.840 | `73ecbb5eedc59271` | 0 | yes |

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9272 | 0.9273 |
| 2 | BAAB | 0.9597 | 0.9598 |
| 3 | ABBA | 0.9136 | 0.9139 |
| 4 | BAAB | 0.9512 | 0.9512 |
| 5 | ABBA | 0.9375 | 0.9380 |
| 6 | BAAB | 0.9179 | 0.9180 |
| 7 | ABBA | 0.9221 | 0.9219 |
| 8 | BAAB | 0.9675 | 0.9683 |

| Metric | Median | Pooled | Range | Below 1 | Above 1 | Reading |
|---|---:|---:|---:|---:|---:|---|
| Engine CPU | 0.9324 | 0.9369 | 0.9136–0.9675 | 8/8 | 0/8 | not measurable here |
| Wall | 0.9327 | 0.9371 | 0.9139–0.9683 | 8/8 | 0/8 | not measurable here |

| Block cohort | Metric | Leg 1 | Leg 2 | Leg 3 | Leg 4 |
|---|---|---:|---:|---:|---:|
| Odd | Engine CPU | 1.02393 | 0.96724 | 0.95492 | 1.05391 |
| Odd | Wall | 1.02379 | 0.96751 | 0.95483 | 1.05388 |
| Even | Engine CPU | 0.97854 | 1.03579 | 1.01665 | 0.96902 |
| Even | Wall | 0.97866 | 1.03549 | 1.01671 | 0.96915 |

[Inputs](sol2/job12/clang-plain/stepK/inputs.txt) · [Raw runs](sol2/job12/clang-plain/stepK/runs.jsonl.txt) · [Summary](sol2/job12/clang-plain/stepK/summary.txt) · [Command](sol2/job12/clang-plain/stepK-command.raw.txt)

### Clang with PGO

#### Step F — identical-binary floor

Logical CPU 2. Arm B durations divided by arm A durations.

- A `clang-r15d` (`1f6961c55f774edaa7f080bc73f209acb434b8acceeb7bab491e238708cdfdf2`)
- B `copy` (`1f6961c55f774edaa7f080bc73f209acb434b8acceeb7bab491e238708cdfdf2`)

| Block | Leg | Engine | CPU (s) | Wall (s) | Trace | Exit | In ratios |
|---:|---|---|---:|---:|---|---:|---|
| 1 | Warm-up | clang-r15d | 15.275 | 15.548 | `73ecbb5eedc59271` | 0 | no |
| 1 | 1 | clang-r15d | 15.437 | 15.724 | `73ecbb5eedc59271` | 0 | yes |
| 1 | 2 | copy | 14.503 | 14.751 | `73ecbb5eedc59271` | 0 | yes |
| 1 | 3 | copy | 15.012 | 15.284 | `73ecbb5eedc59271` | 0 | yes |
| 1 | 4 | clang-r15d | 15.188 | 15.447 | `73ecbb5eedc59271` | 0 | yes |
| 2 | Warm-up | copy | 14.171 | 14.398 | `73ecbb5eedc59271` | 0 | no |
| 2 | 1 | copy | 13.810 | 14.036 | `73ecbb5eedc59271` | 0 | yes |
| 2 | 2 | clang-r15d | 14.611 | 14.863 | `73ecbb5eedc59271` | 0 | yes |
| 2 | 3 | clang-r15d | 14.099 | 14.333 | `73ecbb5eedc59271` | 0 | yes |
| 2 | 4 | copy | 14.072 | 14.310 | `73ecbb5eedc59271` | 0 | yes |
| 3 | Warm-up | clang-r15d | 14.038 | 14.290 | `73ecbb5eedc59271` | 0 | no |
| 3 | 1 | clang-r15d | 14.551 | 14.801 | `73ecbb5eedc59271` | 0 | yes |
| 3 | 2 | copy | 14.230 | 14.456 | `73ecbb5eedc59271` | 0 | yes |
| 3 | 3 | copy | 14.394 | 14.639 | `73ecbb5eedc59271` | 0 | yes |
| 3 | 4 | clang-r15d | 14.111 | 14.335 | `73ecbb5eedc59271` | 0 | yes |
| 4 | Warm-up | copy | 14.128 | 14.349 | `73ecbb5eedc59271` | 0 | no |
| 4 | 1 | copy | 16.158 | 16.482 | `73ecbb5eedc59271` | 0 | yes |
| 4 | 2 | clang-r15d | 15.840 | 16.105 | `73ecbb5eedc59271` | 0 | yes |
| 4 | 3 | clang-r15d | 14.381 | 14.611 | `73ecbb5eedc59271` | 0 | yes |
| 4 | 4 | copy | 14.702 | 14.963 | `73ecbb5eedc59271` | 0 | yes |
| 5 | Warm-up | clang-r15d | 14.709 | 14.951 | `73ecbb5eedc59271` | 0 | no |
| 5 | 1 | clang-r15d | 14.550 | 14.788 | `73ecbb5eedc59271` | 0 | yes |
| 5 | 2 | copy | 14.438 | 14.663 | `73ecbb5eedc59271` | 0 | yes |
| 5 | 3 | copy | 14.283 | 14.507 | `73ecbb5eedc59271` | 0 | yes |
| 5 | 4 | clang-r15d | 13.482 | 13.684 | `73ecbb5eedc59271` | 0 | yes |
| 6 | Warm-up | copy | 14.621 | 14.881 | `73ecbb5eedc59271` | 0 | no |
| 6 | 1 | copy | 14.872 | 15.126 | `73ecbb5eedc59271` | 0 | yes |
| 6 | 2 | clang-r15d | 15.282 | 15.568 | `73ecbb5eedc59271` | 0 | yes |
| 6 | 3 | clang-r15d | 14.204 | 14.446 | `73ecbb5eedc59271` | 0 | yes |
| 6 | 4 | copy | 14.180 | 14.425 | `73ecbb5eedc59271` | 0 | yes |
| 7 | Warm-up | clang-r15d | 14.543 | 14.791 | `73ecbb5eedc59271` | 0 | no |
| 7 | 1 | clang-r15d | 14.952 | 15.211 | `73ecbb5eedc59271` | 0 | yes |
| 7 | 2 | copy | 14.708 | 14.945 | `73ecbb5eedc59271` | 0 | yes |
| 7 | 3 | copy | 15.014 | 15.292 | `73ecbb5eedc59271` | 0 | yes |
| 7 | 4 | clang-r15d | 14.748 | 15.003 | `73ecbb5eedc59271` | 0 | yes |
| 8 | Warm-up | copy | 15.058 | 15.316 | `73ecbb5eedc59271` | 0 | no |
| 8 | 1 | copy | 14.735 | 14.985 | `73ecbb5eedc59271` | 0 | yes |
| 8 | 2 | clang-r15d | 14.787 | 15.054 | `73ecbb5eedc59271` | 0 | yes |
| 8 | 3 | clang-r15d | 14.485 | 14.733 | `73ecbb5eedc59271` | 0 | yes |
| 8 | 4 | copy | 14.992 | 15.270 | `73ecbb5eedc59271` | 0 | yes |

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9638 | 0.9636 |
| 2 | BAAB | 0.9711 | 0.9709 |
| 3 | ABBA | 0.9987 | 0.9986 |
| 4 | BAAB | 1.0211 | 1.0237 |
| 5 | ABBA | 1.0246 | 1.0245 |
| 6 | BAAB | 0.9853 | 0.9846 |
| 7 | ABBA | 1.0008 | 1.0007 |
| 8 | BAAB | 1.0156 | 1.0157 |

| Metric | Median | Pooled | Range | Below 1 | Above 1 | Reading |
|---|---:|---:|---:|---:|---:|---|
| Engine CPU | 0.9997 | 0.9974 | 0.9638–1.0246 | 4/8 | 4/8 | Identical-binary floor |
| Wall | 0.9997 | 0.9976 | 0.9636–1.0245 | 4/8 | 4/8 | Identical-binary floor |

| Block cohort | Metric | Leg 1 | Leg 2 | Leg 3 | Leg 4 |
|---|---|---:|---:|---:|---:|
| Odd | Engine CPU | 1.01868 | 0.99148 | 1.00522 | 0.98462 |
| Odd | Wall | 1.01925 | 0.99086 | 1.00575 | 0.98414 |
| Even | Engine CPU | 1.01237 | 1.02921 | 0.97274 | 0.98569 |
| Even | Wall | 1.01259 | 1.02947 | 0.97205 | 0.98590 |

[Inputs](sol2/job12/clang-pgo/stepF/inputs.txt) · [Raw runs](sol2/job12/clang-pgo/stepF/runs.jsonl.txt) · [Summary](sol2/job12/clang-pgo/stepF/summary.txt) · [Command](sol2/job12/clang-pgo/stepF-command.raw.txt)

#### Step K — Clang kF against Clang r15d

Logical CPU 2. Arm B durations divided by arm A durations.

- A `clang-r15d` (`1f6961c55f774edaa7f080bc73f209acb434b8acceeb7bab491e238708cdfdf2`)
- B `clang-kF` (`a08a2442140a067d4e75d9176b92df0cdcc119afb39c9c1cf2ee174c8b559a7c`)

| Block | Leg | Engine | CPU (s) | Wall (s) | Trace | Exit | In ratios |
|---:|---|---|---:|---:|---|---:|---|
| 1 | Warm-up | clang-r15d | 14.236 | 14.463 | `73ecbb5eedc59271` | 0 | no |
| 1 | 1 | clang-r15d | 14.926 | 15.204 | `73ecbb5eedc59271` | 0 | yes |
| 1 | 2 | clang-kF | 14.092 | 14.339 | `73ecbb5eedc59271` | 0 | yes |
| 1 | 3 | clang-kF | 13.997 | 14.248 | `73ecbb5eedc59271` | 0 | yes |
| 1 | 4 | clang-r15d | 15.517 | 15.811 | `73ecbb5eedc59271` | 0 | yes |
| 2 | Warm-up | clang-kF | 14.715 | 14.983 | `73ecbb5eedc59271` | 0 | no |
| 2 | 1 | clang-kF | 14.561 | 14.835 | `73ecbb5eedc59271` | 0 | yes |
| 2 | 2 | clang-r15d | 14.205 | 14.445 | `73ecbb5eedc59271` | 0 | yes |
| 2 | 3 | clang-r15d | 14.690 | 14.956 | `73ecbb5eedc59271` | 0 | yes |
| 2 | 4 | clang-kF | 14.219 | 14.469 | `73ecbb5eedc59271` | 0 | yes |
| 3 | Warm-up | clang-r15d | 14.882 | 15.128 | `73ecbb5eedc59271` | 0 | no |
| 3 | 1 | clang-r15d | 14.986 | 15.256 | `73ecbb5eedc59271` | 0 | yes |
| 3 | 2 | clang-kF | 13.878 | 14.140 | `73ecbb5eedc59271` | 0 | yes |
| 3 | 3 | clang-kF | 14.153 | 14.415 | `73ecbb5eedc59271` | 0 | yes |
| 3 | 4 | clang-r15d | 15.287 | 15.561 | `73ecbb5eedc59271` | 0 | yes |
| 4 | Warm-up | clang-kF | 14.756 | 15.012 | `73ecbb5eedc59271` | 0 | no |
| 4 | 1 | clang-kF | 16.188 | 16.528 | `73ecbb5eedc59271` | 0 | yes |
| 4 | 2 | clang-r15d | 14.496 | 14.746 | `73ecbb5eedc59271` | 0 | yes |
| 4 | 3 | clang-r15d | 14.503 | 14.758 | `73ecbb5eedc59271` | 0 | yes |
| 4 | 4 | clang-kF | 13.992 | 14.262 | `73ecbb5eedc59271` | 0 | yes |
| 5 | Warm-up | clang-r15d | 14.345 | 14.580 | `73ecbb5eedc59271` | 0 | no |
| 5 | 1 | clang-r15d | 14.201 | 14.444 | `73ecbb5eedc59271` | 0 | yes |
| 5 | 2 | clang-kF | 14.036 | 14.292 | `73ecbb5eedc59271` | 0 | yes |
| 5 | 3 | clang-kF | 13.491 | 13.714 | `73ecbb5eedc59271` | 0 | yes |
| 5 | 4 | clang-r15d | 14.005 | 14.229 | `73ecbb5eedc59271` | 0 | yes |
| 6 | Warm-up | clang-kF | 14.598 | 14.852 | `73ecbb5eedc59271` | 0 | no |
| 6 | 1 | clang-kF | 13.960 | 14.217 | `73ecbb5eedc59271` | 0 | yes |
| 6 | 2 | clang-r15d | 14.422 | 14.655 | `73ecbb5eedc59271` | 0 | yes |
| 6 | 3 | clang-r15d | 14.502 | 14.758 | `73ecbb5eedc59271` | 0 | yes |
| 6 | 4 | clang-kF | 15.517 | 15.831 | `73ecbb5eedc59271` | 0 | yes |
| 7 | Warm-up | clang-r15d | 14.710 | 14.965 | `73ecbb5eedc59271` | 0 | no |
| 7 | 1 | clang-r15d | 13.892 | 14.123 | `73ecbb5eedc59271` | 0 | yes |
| 7 | 2 | clang-kF | 14.014 | 14.306 | `73ecbb5eedc59271` | 0 | yes |
| 7 | 3 | clang-kF | 13.942 | 14.184 | `73ecbb5eedc59271` | 0 | yes |
| 7 | 4 | clang-r15d | 14.430 | 14.672 | `73ecbb5eedc59271` | 0 | yes |
| 8 | Warm-up | clang-kF | 13.339 | 13.566 | `73ecbb5eedc59271` | 0 | no |
| 8 | 1 | clang-kF | 14.144 | 14.392 | `73ecbb5eedc59271` | 0 | yes |
| 8 | 2 | clang-r15d | 14.731 | 14.998 | `73ecbb5eedc59271` | 0 | yes |
| 8 | 3 | clang-r15d | 14.454 | 14.705 | `73ecbb5eedc59271` | 0 | yes |
| 8 | 4 | clang-kF | 13.852 | 14.110 | `73ecbb5eedc59271` | 0 | yes |

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9227 | 0.9218 |
| 2 | BAAB | 0.9960 | 0.9967 |
| 3 | ABBA | 0.9259 | 0.9266 |
| 4 | BAAB | 1.0407 | 1.0436 |
| 5 | ABBA | 0.9759 | 0.9767 |
| 6 | BAAB | 1.0191 | 1.0216 |
| 7 | ABBA | 0.9871 | 0.9894 |
| 8 | BAAB | 0.9593 | 0.9596 |

| Metric | Median | Pooled | Range | Below 1 | Above 1 | Reading |
|---|---:|---:|---:|---:|---:|---|
| Engine CPU | 0.9815 | 0.9777 | 0.9227–1.0407 | 6/8 | 2/8 | not measurable here |
| Wall | 0.9831 | 0.9788 | 0.9218–1.0436 | 6/8 | 2/8 | not measurable here |

| Block cohort | Metric | Leg 1 | Leg 2 | Leg 3 | Leg 4 |
|---|---|---:|---:|---:|---:|
| Odd | Engine CPU | 1.01368 | 0.97965 | 0.97167 | 1.03500 |
| Odd | Wall | 1.01343 | 0.98062 | 0.97142 | 1.03453 |
| Even | Engine CPU | 1.01241 | 0.99581 | 1.00086 | 0.99093 |
| Even | Wall | 1.01319 | 0.99478 | 1.00037 | 0.99167 |

[Inputs](sol2/job12/clang-pgo/stepK/inputs.txt) · [Raw runs](sol2/job12/clang-pgo/stepK/runs.jsonl.txt) · [Summary](sol2/job12/clang-pgo/stepK/summary.txt) · [Command](sol2/job12/clang-pgo/stepK-command.raw.txt)

## Facts

- The frozen GCC builds matched 1,800 of 1,800 complete opening pairs under the defined whole-game move and last-info-node identity check. [Part A1 readback](sol2/job12/A1/readback.raw.json.txt) · [Part A2 readback](sol2/job12/A2/readback.raw.json.txt)
- The complete Clang campaigns retained the fixed-node trace in 128 timed runs and 32 warm-ups. [Independent readback](sol2/job12/clang_timing_readback.py.txt)
- The Clang ThinLTO without PGO kF/r15d comparison pooled at **0.9369** CPU and **0.9371** wall, with CPU lower in 8/8 blocks. The readings were **not measurable here** for CPU and **not measurable here** for wall. [Comparison summary](sol2/job12/clang-plain/stepK/summary.txt)
- The Clang ThinLTO with PGO kF/r15d comparison pooled at **0.9777** CPU and **0.9788** wall, with CPU lower in 6/8 blocks. The readings were **not measurable here** for CPU and **not measurable here** for wall. [Comparison summary](sol2/job12/clang-pgo/stepK/summary.txt)


## Suspicions

Part A holds the GCC toolchain constant across builds and spans the two selected book slices. Part B holds the toolchain within each pair and uses twelve fixed opening histories. The timing design gives the stack's combined effect within each recipe. The profiled timing uses the same workload as profile generation.

## What this check cannot see

The PC's own net (larger), its clang version and its profile from self-play, its processor and its 16 threads,
time-limited games.

## What I did not do

The work used cloud executables, synthetic net768 and fixed search budgets. The branch carries the text traces and build and timing evidence. [Publication layout](sol2/job12/publication-layout.raw.txt)

## What I am not sure about

The owner's production gain remains unmeasured. Part A compared each observed best move and last-info node count. Internal node order and unreported hard-limit nodes are outside that trace.
