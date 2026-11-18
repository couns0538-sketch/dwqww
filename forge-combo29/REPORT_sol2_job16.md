# sol2 — Job 16 Group G and the full kF stack

## Step 0 — machine and frozen identities

Debian Clang 19.1.7 was verified. The cloud VM reports an AMD EPYC 9V74, five logical CPUs on five guest cores, one thread per core and 32 MiB of L3 cache. The cgroup capacity is four CPU equivalents. Each reference engine and the driver use logical CPU 2. The frozen Job 13 r15d and kF Clang ThinLTO executables matched their hashes and each completed a fresh W replay with the Job 15 launch environment. [Machine and gate receipts](sol2/job16/step0-command.raw.txt) · [Frozen hashes](sol2/job16/clang-executables.raw.txt) · [Workload pins](sol2/job16/workload-pins.raw.txt)

Both Step 0 builds match W with 20 games, 2,247 searches, 7,905,938 last-info nodes, 9,189,426 final nodes and trace `7f78d3aec021ab01`. W uses PC20, Threads 1, Hash 16 MiB, net768 and `go softnodes 2000` on book lines 7001–7020. [r15d](sol2/job16/step0/r15d.result.raw.txt#L2-L6) · [kF](sol2/job16/step0/kF.result.raw.txt#L2-L6) · [W signature](sol2/job16/known-answer.txt#L2-L6)

## Step 1 — build receipts and launch arms

Group G adds carbon2's `04_S7`, `11_stop_hot` and `13_tt_avx512_fast_probe` pieces to r15d. I retrieved the patch from Carbon2’s pinned GitHub commit, verified its Git blob and SHA-256, and applied it to a scratch copy. G_1, G_2 and K_2 each generated a separate profile using the Job 13 self-play recipe before the optimized build. The default pins each ran in a fresh process with no UCI options. The W column links the games, searches, last-info nodes, final nodes and trace for a separate fresh process. [Patch provenance](sol2/job16/group-G-patch-source.raw.txt) · [Patch application](sol2/job16/group-source/patch.raw.txt) · [Build recipe](sol2/job16/build_selfplay_clang.sh.txt)

| Build | SHA-256 | Byte-identical to twin | bench 11 nodes | bench 13 nodes | go perft 5 nodes | W: games / searches / last-info / final / trace |
|---|---|---|---:|---:|---:|---|
| r15d | [`540e63c0b7cf2512f1716657aded48b0558022b49c0fe8489596195cf2035834`](sol2/job16/clang-executables.raw.txt#L1) | — | [312,866](sol2/job13/r15d-default.raw.txt#L7) | [862,329](sol2/job13/r15d-default.raw.txt#L14) | [4,865,609](sol2/job13/r15d-default.raw.txt#L42) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job16/step0/r15d.result.raw.txt#L2-L6) |
| K_1 | [`da5df215a6aa255261d4e5574474da7c82aad1a9e95df83e15d5b38963ef439d`](sol2/job16/clang-executables.raw.txt#L2) | K_2, no | [312,866](sol2/job13/kF-default.raw.txt#L7) | [862,329](sol2/job13/kF-default.raw.txt#L14) | [4,865,609](sol2/job13/kF-default.raw.txt#L42) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job16/step0/kF.result.raw.txt#L2-L6) |
| G_1 | [`f083de3cd62f29149bc26e4f1eb8cff6ad83c792001dd3b0a70877d55d57f2e1`](sol2/job16/step1-G_1/clang-sha256.raw.txt#L1) | G_2, no | [312,866](sol2/job16/build-checks/G_1/default-pins.raw.txt#L7) | [862,329](sol2/job16/build-checks/G_1/default-pins.raw.txt#L14) | [4,865,609](sol2/job16/build-checks/G_1/default-pins.raw.txt#L42) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job16/build-checks/G_1/W.result.raw.txt#L2-L6) |
| G_2 | [`bbbb90cddcc89111e8f46767ad7873017155731089a743846ca48e77366c1734`](sol2/job16/step1-G_2/clang-sha256.raw.txt#L1) | G_1, no | [312,866](sol2/job16/build-checks/G_2/default-pins.raw.txt#L7) | [862,329](sol2/job16/build-checks/G_2/default-pins.raw.txt#L14) | [4,865,609](sol2/job16/build-checks/G_2/default-pins.raw.txt#L42) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job16/build-checks/G_2/W.result.raw.txt#L2-L6) |
| K_2 | [`2890d5b1cf4f332a87e572222d5a24ecdc014e0920a6ade776c4f22f3730187f`](sol2/job16/step1-K_2/clang-sha256.raw.txt#L1) | K_1, no | [312,866](sol2/job16/build-checks/K_2/default-pins.raw.txt#L7) | [862,329](sol2/job16/build-checks/K_2/default-pins.raw.txt#L14) | [4,865,609](sol2/job16/build-checks/K_2/default-pins.raw.txt#L42) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job16/build-checks/K_2/W.result.raw.txt#L2-L6) |

[Build identities and gate status](sol2/job16/builds.txt)
[G_1 gates](sol2/job16/build-checks/G_1/checks.raw.txt) · [G_1 build commands](sol2/job16/step1-G_1/commands.raw.txt) · [G_2 gates](sol2/job16/build-checks/G_2/checks.raw.txt) · [G_2 build commands](sol2/job16/step1-G_2/commands.raw.txt) · [K_2 gates](sol2/job16/build-checks/K_2/checks.raw.txt) · [K_2 build commands](sol2/job16/step1-K_2/commands.raw.txt)

| Arm | Engine argv[0] | Characters | Device | Inode | SHA-256 |
|---|---|---:|---:|---:|---|
| K_1 | `/workspace/work/sol2-job16/arms/K_1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 280452 | `da5df215a6aa255261d4e5574474da7c82aad1a9e95df83e15d5b38963ef439d` |
| K_2 | `/workspace/work/sol2-job16/arms/K_2xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 280458 | `2890d5b1cf4f332a87e572222d5a24ecdc014e0920a6ade776c4f22f3730187f` |
| G_1 | `/workspace/work/sol2-job16/arms/G_1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 280454 | `f083de3cd62f29149bc26e4f1eb8cff6ad83c792001dd3b0a70877d55d57f2e1` |
| G_2 | `/workspace/work/sol2-job16/arms/G_2xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 280456 | `bbbb90cddcc89111e8f46767ad7873017155731089a743846ca48e77366c1734` |
| r15d | `/workspace/work/sol2-job16/arms/r15dxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 280450 | `540e63c0b7cf2512f1716657aded48b0558022b49c0fe8489596195cf2035834` |

Each engine receives `LC_ALL=C` and `TZ=UTC`, 16 bytes, SHA-256 `4d41c4c11fcc6efa3bd339441ec9b26e6a1442056205420dc4b11e93dbff2570`. [Arms](sol2/job16/arms.txt)

## Prediction graded

The prediction was committed alone at `d375f7abd543c9db289b59fd57d8de4d72727528` after Step 1 and before G1.

| Comparison | Predicted CPU B/A | Observed CPU B/A | Ratio in range | Expected reading | Observed reading | Reading met |
|---|---:|---:|---|---|---|---|
| G1 | 0.995–1.060 | 1.0376 | Yes | Rest NOT SEEN | Rest PAYS | No |
| G2 | 0.995–1.060 | 1.0225 | Yes | Rest NOT SEEN | Rest PAYS | No |
| G3 | 0.943–1.010 | 0.9532 | Yes | Rest NOT SEEN | Rest PAYS | No |
| R1 | 0.925–0.995 | 0.9878 | Yes | G alone PAYS | G alone NOT SEEN | No |
| F1 | 0.970–1.030 | 1.0007 | Yes | Floor interval includes one | Floor interval includes one | Yes |

The predicted swapped G/kF CPU ratio was 0.99–1.05. The observed ratio of 1.0433 was within range.

[Original prediction](sol2/job16/prediction.txt) · [UTC checkpoints](sol2/job16/stamps.txt)

## Step 2 — timing comparisons

Every run started a fresh engine on logical CPU 2 with workload W and the fixed replacement environment. Each arm used a 72-character executable path. Odd blocks used ABBA and even blocks used BAAB. One recorded warm-up preceded each block, and only its four timed runs entered the ratio. A run outside the W signature gate excluded its block. Engine CPU is the reaped engine process's user plus system time. Wall is the full driver call interval. Each complete comparison reports B/A with a Student t interval from the 16 block ratios and 15 degrees of freedom. [Timing commands](sol2/job16/run_campaign.sh.txt) · [Independent readback](sol2/job16/timing_readback.py.txt)

| Comparison | A | B | Metric | Blocks | Median | Pooled B/A | Mean | 95% t interval, df 15 | Below 1 |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| G1 | K_1 | G_1 | Engine CPU | 16/16 | 1.0404 | 1.0376 | 1.0382 | [1.0143, 1.0621] | 3/16 |
| G1 | K_1 | G_1 | Wall | 16/16 | 1.0348 | 1.0329 | 1.0336 | [1.0087, 1.0586] | 3/16 |
| G2 | K_2 | G_2 | Engine CPU | 16/16 | 1.0145 | 1.0225 | 1.0231 | [1.0010, 1.0453] | 3/16 |
| G2 | K_2 | G_2 | Wall | 16/16 | 1.0119 | 1.0180 | 1.0187 | [0.9957, 1.0417] | 4/16 |
| G3 | G_1 | K_1 | Engine CPU | 16/16 | 0.9543 | 0.9532 | 0.9536 | [0.9403, 0.9670] | 16/16 |
| G3 | G_1 | K_1 | Wall | 16/16 | 0.9590 | 0.9575 | 0.9580 | [0.9440, 0.9719] | 16/16 |
| R1 | r15d | G_1 | Engine CPU | 16/16 | 0.9779 | 0.9878 | 0.9879 | [0.9722, 1.0036] | 11/16 |
| R1 | r15d | G_1 | Wall | 16/16 | 0.9805 | 0.9890 | 0.9892 | [0.9734, 1.0049] | 11/16 |
| F1 | K_1 | K_2 | Engine CPU | 16/16 | 1.0069 | 1.0007 | 1.0016 | [0.9813, 1.0219] | 7/16 |
| F1 | K_1 | K_2 | Wall | 16/16 | 1.0081 | 1.0010 | 1.0019 | [0.9813, 1.0225] | 7/16 |

## Declared readings and arithmetic

| Metric | Rest of kF | G / kF swapped time ratio | G alone vs r15d | F1 floor |
|---|---|---:|---|---|
| Engine CPU | PAYS | 1.043295 | NOT SEEN | Interval contains 1 |
| Wall | OPEN | 1.038633 | NOT SEEN | Interval contains 1 |

G1 and G2 test whether the rest of kF pays. Both intervals wholly above 1 give PAYS, two completed intervals with neither wholly above 1 give NOT SEEN, and other cases give OPEN. G alone pays when R1 lies wholly below 1. The swapped ratio is sqrt(G1 pooled / G3 pooled).

Engine CPU gives sqrt(1.037579221 / 0.953249535) = 1.043295494. [G1](sol2/job16/G1/summary.txt) · [G3](sol2/job16/G3/summary.txt)

Wall gives sqrt(1.032941279 / 0.957526977) = 1.038633455. [G1](sol2/job16/G1/summary.txt) · [G3](sol2/job16/G3/summary.txt)

### G1

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 1.0523 | 1.0531 |
| 2 | BAAB | 1.0288 | 1.0234 |
| 3 | ABBA | 1.0650 | 1.0629 |
| 4 | BAAB | 0.9859 | 0.9802 |
| 5 | ABBA | 1.0171 | 1.0112 |
| 6 | BAAB | 1.0363 | 1.0279 |
| 7 | ABBA | 0.9768 | 0.9666 |
| 8 | BAAB | 1.0693 | 1.0677 |
| 9 | ABBA | 1.0499 | 1.0480 |
| 10 | BAAB | 1.0606 | 1.0563 |
| 11 | ABBA | 1.0139 | 1.0074 |
| 12 | BAAB | 1.0445 | 1.0418 |
| 13 | ABBA | 1.1564 | 1.1558 |
| 14 | BAAB | 0.9687 | 0.9630 |
| 15 | ABBA | 1.0195 | 1.0138 |
| 16 | BAAB | 1.0663 | 1.0592 |

[Inputs](sol2/job16/G1/inputs.txt) · [Raw runs](sol2/job16/G1/runs.jsonl.txt) · [Summary](sol2/job16/G1/summary.txt) · [Command](sol2/job16/G1-command.raw.txt)

### G2

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 1.0101 | 1.0075 |
| 2 | BAAB | 0.9544 | 0.9463 |
| 3 | ABBA | 1.0595 | 1.0548 |
| 4 | BAAB | 1.0834 | 1.0832 |
| 5 | ABBA | 1.0030 | 0.9951 |
| 6 | BAAB | 1.0889 | 1.0846 |
| 7 | ABBA | 0.9687 | 0.9607 |
| 8 | BAAB | 1.0937 | 1.0923 |
| 9 | ABBA | 0.9747 | 0.9688 |
| 10 | BAAB | 1.0082 | 1.0046 |
| 11 | ABBA | 1.0336 | 1.0303 |
| 12 | BAAB | 1.0089 | 1.0053 |
| 13 | ABBA | 1.0302 | 1.0257 |
| 14 | BAAB | 1.0298 | 1.0227 |
| 15 | ABBA | 1.0188 | 1.0162 |
| 16 | BAAB | 1.0046 | 1.0013 |

[Inputs](sol2/job16/G2/inputs.txt) · [Raw runs](sol2/job16/G2/runs.jsonl.txt) · [Summary](sol2/job16/G2/summary.txt) · [Command](sol2/job16/G2-command.raw.txt)

### G3

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9686 | 0.9772 |
| 2 | BAAB | 0.9831 | 0.9894 |
| 3 | ABBA | 0.9551 | 0.9576 |
| 4 | BAAB | 0.9534 | 0.9566 |
| 5 | ABBA | 0.9136 | 0.9150 |
| 6 | BAAB | 0.9882 | 0.9934 |
| 7 | ABBA | 0.9485 | 0.9552 |
| 8 | BAAB | 0.9530 | 0.9604 |
| 9 | ABBA | 0.9628 | 0.9673 |
| 10 | BAAB | 0.8997 | 0.9036 |
| 11 | ABBA | 0.9687 | 0.9718 |
| 12 | BAAB | 0.9777 | 0.9829 |
| 13 | ABBA | 0.9164 | 0.9171 |
| 14 | BAAB | 0.9707 | 0.9743 |
| 15 | ABBA | 0.9513 | 0.9538 |
| 16 | BAAB | 0.9474 | 0.9516 |

[Inputs](sol2/job16/G3/inputs.txt) · [Raw runs](sol2/job16/G3/runs.jsonl.txt) · [Summary](sol2/job16/G3/summary.txt) · [Command](sol2/job16/G3-command.raw.txt)

### R1

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9882 | 0.9905 |
| 2 | BAAB | 0.9877 | 0.9896 |
| 3 | ABBA | 0.9776 | 0.9783 |
| 4 | BAAB | 0.9757 | 0.9778 |
| 5 | ABBA | 0.9574 | 0.9586 |
| 6 | BAAB | 0.9325 | 0.9328 |
| 7 | ABBA | 0.9749 | 0.9772 |
| 8 | BAAB | 1.0309 | 1.0325 |
| 9 | ABBA | 0.9664 | 0.9678 |
| 10 | BAAB | 1.0280 | 1.0294 |
| 11 | ABBA | 0.9783 | 0.9827 |
| 12 | BAAB | 1.0059 | 1.0038 |
| 13 | ABBA | 0.9666 | 0.9660 |
| 14 | BAAB | 0.9761 | 0.9767 |
| 15 | ABBA | 1.0250 | 1.0256 |
| 16 | BAAB | 1.0359 | 1.0374 |

[Inputs](sol2/job16/R1/inputs.txt) · [Raw runs](sol2/job16/R1/runs.jsonl.txt) · [Summary](sol2/job16/R1/summary.txt) · [Command](sol2/job16/R1-command.raw.txt)

### F1

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 1.0400 | 1.0406 |
| 2 | BAAB | 1.0041 | 1.0057 |
| 3 | ABBA | 1.0097 | 1.0105 |
| 4 | BAAB | 0.9421 | 0.9427 |
| 5 | ABBA | 1.0212 | 1.0219 |
| 6 | BAAB | 0.9990 | 0.9979 |
| 7 | ABBA | 0.9804 | 0.9798 |
| 8 | BAAB | 0.9285 | 0.9323 |
| 9 | ABBA | 1.0453 | 1.0487 |
| 10 | BAAB | 0.9968 | 0.9968 |
| 11 | ABBA | 0.9500 | 0.9456 |
| 12 | BAAB | 1.0201 | 1.0184 |
| 13 | ABBA | 1.0548 | 1.0552 |
| 14 | BAAB | 1.0251 | 1.0262 |
| 15 | ABBA | 1.0370 | 1.0397 |
| 16 | BAAB | 0.9716 | 0.9691 |

[Inputs](sol2/job16/F1/inputs.txt) · [Raw runs](sol2/job16/F1/runs.jsonl.txt) · [Summary](sol2/job16/F1/summary.txt) · [Command](sol2/job16/F1-command.raw.txt)

## Facts

The five comparisons contain 320 timed runs and 80 warm-ups. Independent readback verified all 400 W signatures and recomputed the timing ratios. Procfs verified the launch arguments, environment and executable inode on all 400 runs. [Independent readback](sol2/job16/timing_readback.py.txt) · [Launch arms](sol2/job16/arms.txt)

## Suspicions

The CPU result compares the remaining pieces of kF as a group. Independent profiles can produce byte-different executables from the same source. F1 measures that variation for kF on this host. [Build identities](sol2/job16/builds.txt) · [Comparison plan](sol2/job16/comparison-plan.txt)

## What this check cannot see

> The PC's Windows loader, its clang 23, its Zen 5 processor with 16 engines playing at once, its trained net (net768
is synthetic), its own self-play openings; single pieces inside the rest of kF.

## What I did not do

The comparison was limited to these cloud builds, the fixed W workload and one pinned worker. The patch was applied only in scratch. [Publication layout](sol2/job16/publication-layout.raw.txt)

## What I am not sure about

The gain under the owner's production build and workload remains unresolved. W records moves and last-info node counts in its trace and verifies final soft-node counts in aggregate.
