# sol2 — Job 14 timing controls and swapped-arm stack comparison

## Step 0 — machine and frozen identities

The workspace compiler reports Debian Clang 19.1.7. Both Job 13 self-play-profiled Clang ThinLTO executables matched their frozen SHA-256 hashes. The cloud VM reports AMD EPYC 9V74, five logical CPUs on five guest cores, one thread per core and one 32 MiB L3 cache. The cgroup capacity was four CPU equivalents. Each engine and its driver ran on logical CPU 2. The book, net768, driver and W signature bytes matched Job 13. [Machine, compiler and pin receipts](sol2/job14/step0-launch-attempt-command.raw.txt) · [Frozen executables](sol2/job14/clang-executables.raw.txt) · [W replay command](sol2/job14/step0-command.raw.txt)

The first launch observer reported an argument or environment mismatch immediately after `Popen` returned. It stopped the engine before W produced a signature. A toy probe reproduced empty procfs reads in that interval, consistent with the first failure. I moved the observer to the first engine response, before subsequent UCI reads, with no added sleep. The fresh r15d and kF replays then passed and both process receipts verified. All timing runs used this corrected observer. [Initial attempt](sol2/job14/step0-launch-attempt/r15d.result.raw.txt) · [Toy probe](sol2/job14/step0-procfs-probe.raw.txt) · [Final harness](sol2/job14/arm_timing.py.txt)

The cloud shell relay disconnected during S3. The same workspace retained the timing process and all 80 S3 runs. The original sequence ended after the S3 commit and before its push. I verified the complete S3 raw data, pushed that commit, and resumed at S4. [Recovery receipts](sol2/job14/connection-recovery.raw.txt)

Both Step 0 builds match W with 20 games, 2,247 searches, 7,905,938 last-info nodes, 9,189,426 final nodes and trace `7f78d3aec021ab01`. W uses PC20, Threads 1, Hash 16 MiB, net768 and `go softnodes 2000` on book lines 7001–7020. [r15d](sol2/job14/step0/r15d.result.raw.txt) · [kF](sol2/job14/step0/kF.result.raw.txt) · [W signature](sol2/job14/known-answer.txt)

## Step 1 — paths, executable identities and environment

| Arm | Engine argv[0] | Characters | Device | Inode | SHA-256 |
|---|---|---:|---:|---:|---|
| P0 | `/workspace/work/sol2-job13/build-clang-selfplay-r15d/forge` | 58 | 27 | 278740 | `540e63c0b7cf2512f1716657aded48b0558022b49c0fe8489596195cf2035834` |
| C0 | `/workspace/work/sol2-job13/r15d-clang-selfplay-copy` | 51 | 27 | 279918 | `540e63c0b7cf2512f1716657aded48b0558022b49c0fe8489596195cf2035834` |
| H1 | `/workspace/work/sol2-job14/hard-link-to-r15d-at-a-substantially-longer-launch-path/forge` | 88 | 27 | 278740 | `540e63c0b7cf2512f1716657aded48b0558022b49c0fe8489596195cf2035834` |
| E1 | `/workspace/work/sol2-job14/arms/e1/forge` | 40 | 27 | 262545 | `540e63c0b7cf2512f1716657aded48b0558022b49c0fe8489596195cf2035834` |
| E2 | `/workspace/work/sol2-job14/arms/e2/forge` | 40 | 27 | 262563 | `540e63c0b7cf2512f1716657aded48b0558022b49c0fe8489596195cf2035834` |
| K1 | `/workspace/work/sol2-job14/arms/k1/forge` | 40 | 27 | 262564 | `da5df215a6aa255261d4e5574474da7c82aad1a9e95df83e15d5b38963ef439d` |
| R1 | `/workspace/work/sol2-job14/arms/r1/forge` | 40 | 27 | 262565 | `540e63c0b7cf2512f1716657aded48b0558022b49c0fe8489596195cf2035834` |

Each engine receives `LC_ALL=C` and `TZ=UTC`, 16 bytes, SHA-256 `4d41c4c11fcc6efa3bd339441ec9b26e6a1442056205420dc4b11e93dbff2570`. [Arms](sol2/job14/arms.txt)

H1 is a hard link to P0 and extends its path by 30 characters. E1 and E2 are distinct copies at paths of equal length. K1 and R1 are separate copies at paths of that same length. C0 is the retained Job 13 copy. [Arm construction](sol2/job14/make_arms.py.txt)

## Prediction graded

The prediction was published alone at `1e8222da2caaccfba35c1a977ba74e4e927bba9e` after the arm inventory and before S1.

| Comparison | Predicted CPU B/A | Observed CPU B/A | Within range | Expected reading | Observed reading |
|---|---:|---:|---|---|---|
| S1 | 0.970–1.030 | 1.0025 | yes | No detected order effect | No detected order effect |
| S2 | 0.970–1.030 | 0.9960 | yes | No detected file-copy effect | No detected file-copy effect |
| S3 | 0.960–1.040 | 0.9760 | yes | No detected path-length effect | Path-length effect detected |
| S4 | 0.950–1.010 | 1.0013 | yes | Offset not replicated | Offset not replicated |
| S5 | 0.990–1.050 | 1.0148 | yes | Offset not replicated | Offset not replicated |
| S6 | 0.930–1.010 | 0.9367 | yes | Stack effect not measurable | Stack effect measured |
| S7 | 0.990–1.080 | 1.0532 | yes | Stack effect not measurable | Stack effect measured |

[Original prediction](sol2/job14/prediction.txt) · [UTC checkpoints](sol2/job14/stamps.txt)

## Step 2 — seven balanced comparisons

Each comparison uses one engine and its driver on CPU 2 with W, a fresh process for every run and a common replacement environment. Odd blocks use ABBA and even blocks use BAAB. The first arm runs once as a recorded warm-up before its block. The warm-up is excluded from the ratios. Engine CPU is reaped user plus system time. Wall is the full call interval. Ratios are B divided by A using summed durations. The reported mean interval uses the 16 block ratios and Student t with 15 degrees of freedom. [Timing command](sol2/job14/run_campaign.sh.txt) · [Independent readback](sol2/job14/timing_readback.py.txt)

The declared reading treats S1, S2 and S3 separately. Each detects an effect when its interval excludes one. S4/S5 replicate the old offset when the S4 interval is wholly below one and S5 wholly above one. S6/S7 use the same directional interval test for the stack and report the square root of the ratio of their pooled ratios. These rules apply to CPU and wall separately.

| Comparison | A | B | Metric | Blocks | Median | Pooled B/A | Mean | 95% t interval, df 15 | Below 1 |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| S1 | P0 | P0 | Engine CPU | 16/16 | 0.9937 | 1.0025 | 1.0022 | [0.9773, 1.0271] | 9/16 |
| S1 | P0 | P0 | Wall | 16/16 | 0.9916 | 1.0028 | 1.0025 | [0.9765, 1.0285] | 9/16 |
| S2 | E1 | E2 | Engine CPU | 16/16 | 0.9940 | 0.9960 | 0.9964 | [0.9758, 1.0170] | 9/16 |
| S2 | E1 | E2 | Wall | 16/16 | 0.9924 | 0.9961 | 0.9965 | [0.9750, 1.0179] | 9/16 |
| S3 | P0 | H1 | Engine CPU | 16/16 | 0.9768 | 0.9760 | 0.9770 | [0.9548, 0.9992] | 12/16 |
| S3 | P0 | H1 | Wall | 16/16 | 0.9742 | 0.9750 | 0.9760 | [0.9531, 0.9989] | 12/16 |
| S4 | P0 | C0 | Engine CPU | 16/16 | 1.0055 | 1.0013 | 1.0023 | [0.9872, 1.0173] | 6/16 |
| S4 | P0 | C0 | Wall | 16/16 | 1.0059 | 1.0006 | 1.0016 | [0.9861, 1.0171] | 6/16 |
| S5 | C0 | P0 | Engine CPU | 16/16 | 1.0168 | 1.0148 | 1.0154 | [1.0034, 1.0273] | 5/16 |
| S5 | C0 | P0 | Wall | 16/16 | 1.0166 | 1.0157 | 1.0162 | [1.0040, 1.0285] | 4/16 |
| S6 | R1 | K1 | Engine CPU | 16/16 | 0.9420 | 0.9367 | 0.9371 | [0.9225, 0.9516] | 16/16 |
| S6 | R1 | K1 | Wall | 16/16 | 0.9468 | 0.9415 | 0.9419 | [0.9266, 0.9572] | 16/16 |
| S7 | K1 | R1 | Engine CPU | 16/16 | 1.0516 | 1.0532 | 1.0538 | [1.0301, 1.0775] | 2/16 |
| S7 | K1 | R1 | Wall | 16/16 | 1.0455 | 1.0478 | 1.0485 | [1.0239, 1.0730] | 2/16 |

| Declared reading | Engine CPU | Wall |
|---|---|---|
| Order | effect not detected | effect not detected |
| File copy | effect not detected | effect not detected |
| Path length | effect detected, interval wholly below 1 | effect detected, interval wholly below 1 |
| Job 13 offset | not replicated | not replicated |
| kF against r15d | MEASURED, adjusted time ratio 0.9431 | MEASURED, adjusted time ratio 0.9479 |

### S1

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 1.0172 | 1.0170 |
| 2 | BAAB | 0.9906 | 0.9910 |
| 3 | ABBA | 1.1020 | 1.1083 |
| 4 | BAAB | 0.9814 | 0.9835 |
| 5 | ABBA | 0.9968 | 0.9921 |
| 6 | BAAB | 0.9798 | 0.9789 |
| 7 | ABBA | 0.9379 | 0.9368 |
| 8 | BAAB | 0.9114 | 0.9073 |
| 9 | ABBA | 1.0420 | 1.0415 |
| 10 | BAAB | 0.9739 | 0.9755 |
| 11 | ABBA | 1.0161 | 1.0183 |
| 12 | BAAB | 1.0698 | 1.0735 |
| 13 | ABBA | 0.9872 | 0.9875 |
| 14 | BAAB | 1.0009 | 1.0002 |
| 15 | ABBA | 1.0410 | 1.0425 |
| 16 | BAAB | 0.9870 | 0.9860 |

[Inputs](sol2/job14/S1/inputs.txt) · [Raw runs](sol2/job14/S1/runs.jsonl.txt) · [Summary](sol2/job14/S1/summary.txt) · [Command](sol2/job14/S1-command.raw.txt)

### S2

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9453 | 0.9409 |
| 2 | BAAB | 1.0147 | 1.0156 |
| 3 | ABBA | 1.0047 | 1.0063 |
| 4 | BAAB | 1.0552 | 1.0590 |
| 5 | ABBA | 0.9861 | 0.9871 |
| 6 | BAAB | 0.9778 | 0.9777 |
| 7 | ABBA | 0.9790 | 0.9787 |
| 8 | BAAB | 0.9883 | 0.9885 |
| 9 | ABBA | 0.9741 | 0.9744 |
| 10 | BAAB | 1.0474 | 1.0481 |
| 11 | ABBA | 1.0268 | 1.0294 |
| 12 | BAAB | 1.0063 | 1.0039 |
| 13 | ABBA | 0.9929 | 0.9907 |
| 14 | BAAB | 0.9033 | 0.9010 |
| 15 | ABBA | 0.9951 | 0.9942 |
| 16 | BAAB | 1.0448 | 1.0478 |

[Inputs](sol2/job14/S2/inputs.txt) · [Raw runs](sol2/job14/S2/runs.jsonl.txt) · [Summary](sol2/job14/S2/summary.txt) · [Command](sol2/job14/S2-command.raw.txt)

### S3

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9892 | 0.9893 |
| 2 | BAAB | 0.8952 | 0.8936 |
| 3 | ABBA | 1.0066 | 1.0053 |
| 4 | BAAB | 0.9625 | 0.9595 |
| 5 | ABBA | 0.9732 | 0.9706 |
| 6 | BAAB | 0.9046 | 0.9025 |
| 7 | ABBA | 0.9909 | 0.9938 |
| 8 | BAAB | 0.9781 | 0.9778 |
| 9 | ABBA | 0.9731 | 0.9669 |
| 10 | BAAB | 1.0402 | 1.0437 |
| 11 | ABBA | 0.9463 | 0.9437 |
| 12 | BAAB | 0.9413 | 0.9405 |
| 13 | ABBA | 0.9756 | 0.9705 |
| 14 | BAAB | 1.0411 | 1.0428 |
| 15 | ABBA | 0.9903 | 0.9925 |
| 16 | BAAB | 1.0232 | 1.0224 |

[Inputs](sol2/job14/S3/inputs.txt) · [Raw runs](sol2/job14/S3/runs.jsonl.txt) · [Summary](sol2/job14/S3/summary.txt) · [Command](sol2/job14/S3-command.raw.txt)

### S4

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 1.0377 | 1.0388 |
| 2 | BAAB | 0.9737 | 0.9688 |
| 3 | ABBA | 1.0022 | 1.0047 |
| 4 | BAAB | 1.0065 | 1.0072 |
| 5 | ABBA | 0.9711 | 0.9711 |
| 6 | BAAB | 1.0279 | 1.0291 |
| 7 | ABBA | 0.9852 | 0.9827 |
| 8 | BAAB | 1.0104 | 1.0133 |
| 9 | ABBA | 0.9879 | 0.9860 |
| 10 | BAAB | 1.0153 | 1.0127 |
| 11 | ABBA | 0.9342 | 0.9335 |
| 12 | BAAB | 0.9952 | 0.9932 |
| 13 | ABBA | 1.0218 | 1.0216 |
| 14 | BAAB | 1.0508 | 1.0511 |
| 15 | ABBA | 1.0120 | 1.0104 |
| 16 | BAAB | 1.0044 | 1.0016 |

[Inputs](sol2/job14/S4/inputs.txt) · [Raw runs](sol2/job14/S4/runs.jsonl.txt) · [Summary](sol2/job14/S4/summary.txt) · [Command](sol2/job14/S4-command.raw.txt)

### S5

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 1.0177 | 1.0144 |
| 2 | BAAB | 0.9896 | 0.9907 |
| 3 | ABBA | 1.0272 | 1.0284 |
| 4 | BAAB | 1.0158 | 1.0187 |
| 5 | ABBA | 1.0048 | 1.0066 |
| 6 | BAAB | 0.9785 | 0.9780 |
| 7 | ABBA | 0.9994 | 1.0001 |
| 8 | BAAB | 1.0486 | 1.0496 |
| 9 | ABBA | 0.9837 | 0.9834 |
| 10 | BAAB | 1.0391 | 1.0403 |
| 11 | ABBA | 1.0183 | 1.0197 |
| 12 | BAAB | 0.9933 | 0.9934 |
| 13 | ABBA | 1.0378 | 1.0392 |
| 14 | BAAB | 1.0474 | 1.0507 |
| 15 | ABBA | 1.0324 | 1.0332 |
| 16 | BAAB | 1.0122 | 1.0132 |

[Inputs](sol2/job14/S5/inputs.txt) · [Raw runs](sol2/job14/S5/runs.jsonl.txt) · [Summary](sol2/job14/S5/summary.txt) · [Command](sol2/job14/S5-command.raw.txt)

### S6

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9336 | 0.9414 |
| 2 | BAAB | 0.9289 | 0.9323 |
| 3 | ABBA | 0.9393 | 0.9437 |
| 4 | BAAB | 0.9363 | 0.9400 |
| 5 | ABBA | 0.9762 | 0.9836 |
| 6 | BAAB | 0.9448 | 0.9499 |
| 7 | ABBA | 0.9605 | 0.9683 |
| 8 | BAAB | 0.9467 | 0.9528 |
| 9 | ABBA | 0.9526 | 0.9556 |
| 10 | BAAB | 0.9621 | 0.9678 |
| 11 | ABBA | 0.9658 | 0.9704 |
| 12 | BAAB | 0.9090 | 0.9141 |
| 13 | ABBA | 0.8687 | 0.8686 |
| 14 | BAAB | 0.9483 | 0.9529 |
| 15 | ABBA | 0.9011 | 0.9051 |
| 16 | BAAB | 0.9188 | 0.9235 |

[Inputs](sol2/job14/S6/inputs.txt) · [Raw runs](sol2/job14/S6/runs.jsonl.txt) · [Summary](sol2/job14/S6/summary.txt) · [Command](sol2/job14/S6-command.raw.txt)

### S7

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 1.1386 | 1.1367 |
| 2 | BAAB | 1.0604 | 1.0574 |
| 3 | ABBA | 1.0294 | 1.0268 |
| 4 | BAAB | 1.0539 | 1.0451 |
| 5 | ABBA | 1.0953 | 1.0884 |
| 6 | BAAB | 0.9765 | 0.9692 |
| 7 | ABBA | 1.0267 | 1.0209 |
| 8 | BAAB | 1.0731 | 1.0681 |
| 9 | ABBA | 1.1429 | 1.1412 |
| 10 | BAAB | 1.0549 | 1.0473 |
| 11 | ABBA | 1.0484 | 1.0406 |
| 12 | BAAB | 1.0285 | 1.0203 |
| 13 | ABBA | 1.0571 | 1.0568 |
| 14 | BAAB | 1.0493 | 1.0458 |
| 15 | ABBA | 1.0367 | 1.0297 |
| 16 | BAAB | 0.9896 | 0.9810 |

[Inputs](sol2/job14/S7/inputs.txt) · [Raw runs](sol2/job14/S7/runs.jsonl.txt) · [Summary](sol2/job14/S7/summary.txt) · [Command](sol2/job14/S7-command.raw.txt)

## Facts

- The complete comparisons included 448 timed runs and 112 warm-ups, with both W node totals checked in each run. Procfs verified the supplied arguments, environment and executable inode in 560 of 560 archived runs with summaries. [Independent readback](sol2/job14/timing_readback.py.txt)
- The Job 13 CPU offset reading was **not replicated**. [S4](sol2/job14/S4/summary.txt) · [S5](sol2/job14/S5/summary.txt)
- The swapped-arm stack estimates were **0.9431** CPU and **0.9479** wall. The CPU reading was **measured**, with wall **measured**. [S6](sol2/job14/S6/summary.txt) · [S7](sol2/job14/S7/summary.txt)


## Suspicions

The hard-link contrast holds the executable device and inode fixed while changing the pathname bytes and length. The equal-length copy arms use separate inodes. An effect in the hard-link comparison identifies sensitivity to the launch path. The mechanism that produced the timing difference remains unresolved. Job 13 inherited the launch environment. Job 14 used the explicitly fixed environment above. S3's faster launch path was longer. Job 13's faster C0 launch path was shorter. These observations leave the direction of a path-length effect unresolved. [S3](sol2/job14/S3/summary.txt) · [Job 13 Step F](sol2/job13/stepF/summary.txt)

## What this check cannot see

The PC's Windows loader, its clang 23, its processor with 16 engines playing at once, its trained net (net768 is
synthetic), its own self-play openings.

## What I did not do

All comparisons used the frozen cloud builds and one pinned CPU. This branch contains only text evidence for the job. [Publication layout](sol2/job14/publication-layout.raw.txt)

## What I am not sure about

The owner's production gain remains unmeasured. The trace hashes each best move and last-info node count. The final soft-node count is checked as a sum across W. Internal node visitation order is beyond these checks.
