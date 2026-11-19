# sol2 — Job 22 soft and hard node limits in one session

## Step 0 — machine and frozen identities

Debian Clang 19.1.7 was verified. The cloud VM reports an AMD EPYC 9V74, five logical CPUs on five guest cores, shared 32 MiB L3 and four CPU equivalents in the cgroup. Each engine and driver run on logical CPU 2. Frozen r15d and K_1 matched their Job 16 SHA-256 hashes and passed W in fresh processes from the existing 72-character launch paths. [Machine and gate receipts](sol2/job22/step0-command.raw.txt) · [Frozen hashes](sol2/job22/clang-executables.raw.txt) · [Launch arms](sol2/job22/reference-arms.txt)

Both Step 0 builds matched W with 20 games, 2,247 searches, 7,905,938 last-info nodes, 9,189,426 final nodes and trace `7f78d3aec021ab01`. W uses PC20, Threads 1, Hash 16 MiB, net768 and `go softnodes 2000` on book lines 7001–7020. [r15d](sol2/job22/step0/r15d.result.raw.txt#L2-L6) · [K_1](sol2/job22/step0/K_1.result.raw.txt#L2-L6) · [W signature](sol2/job22/known-answer.txt#L2-L6)

| Arm | Engine argv[0] | Characters | Device | Inode | SHA-256 |
|---|---|---:|---:|---:|---|
| r15d | `/workspace/work/sol2-job16/arms/r15dxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 280450 | `540e63c0b7cf2512f1716657aded48b0558022b49c0fe8489596195cf2035834` |
| K_1 | `/workspace/work/sol2-job16/arms/K_1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 280452 | `da5df215a6aa255261d4e5574474da7c82aad1a9e95df83e15d5b38963ef439d` |

Each engine receives `LC_ALL=C` and `TZ=UTC`, 16 bytes, SHA-256 `4d41c4c11fcc6efa3bd339441ec9b26e6a1442056205420dc4b11e93dbff2570`. [Arms](sol2/job22/reference-arms.txt)

## Hard workload gates

| Workload | Book lines | Command | First r15d games / searches / last-info nodes / final nodes / trace | First K_1 |
|---|---|---|---|---|
| W20 | 7001–7004 | `go nodes 20000` | 4 / 292 / 3,552,477 / unavailable / `6c8a346a0e739aad`. [Raw first r15d](sol2/job22/hard-gates/W20/A.r15d.result.raw.txt) · [Known answer](sol2/job22/known-answer-W20.txt#L2-L6) | Matched. [Raw first K_1](sol2/job22/hard-gates/W20/B.K_1.result.raw.txt) |
| W22 | 7001–7004 | `go nodes 22000` | 4 / 403 / 5,228,684 / unavailable / `9c47c86225fba704`. [Raw first r15d](sol2/job22/hard-gates/W22/A.r15d.result.raw.txt) · [Known answer](sol2/job22/known-answer-W22.txt#L2-L6) | r15d-only control |
| W50 | 7001–7002 | `go nodes 50000` | 2 / 156 / 4,584,156 / unavailable / `5b4514f9ca9a3a36`. [Raw first r15d](sol2/job22/hard-gates/W50/A.r15d.result.raw.txt) · [Known answer](sol2/job22/known-answer-W50.txt#L2-L6) | Matched. [Raw first K_1](sol2/job22/hard-gates/W50/B.K_1.result.raw.txt) |

The hard-node final total is unavailable in the frozen UCI output. Equality uses the observed games, searches, last-info nodes, trace and absence of final-node telemetry. The configured limit remains a separate field.

The per-run receipt files linked below preserve each engine hash, workload, observed signature, and block eligibility.

[Final-node output guards in both frozen sources](sol2/job22/hard-node-uci-source.raw.txt)

## C22 control

| Comparison | A | B | Workload A / B | Metric | Blocks | Median | Pooled B/A | Mean | 95% t interval, df 7 | Below 1 |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| C22 | r15d | r15d | W20 / W22 | Engine CPU | 8/8 | 1.5905 | 1.5960 | 1.5964 | [1.5534, 1.6393] | 0/8 |
| C22 | r15d | r15d | W20 / W22 | Wall | 8/8 | 1.5832 | 1.5882 | 1.5886 | [1.5436, 1.6336] | 0/8 |

The 20,000-to-22,000 configured limit change also changed replay length from 292 to 403 searches. C22 tests whether the harness detects the full workload perturbation. [W20](sol2/job22/known-answer-W20.txt#L3) · [W22](sol2/job22/known-answer-W22.txt#L3)

**PASS**. The CPU interval must lie wholly above one for W22 relative to W20.

### C22

Logical CPU 2. 40 attempted runs, 8 included blocks, 32 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 1.5827 | 1.5744 |
| 2 | BAAB | 1.6100 | 1.6034 |
| 3 | ABBA | 1.5689 | 1.5583 |
| 4 | BAAB | 1.5982 | 1.5920 |
| 5 | ABBA | 1.5259 | 1.5121 |
| 6 | BAAB | 1.6628 | 1.6565 |
| 7 | ABBA | 1.6726 | 1.6689 |
| 8 | BAAB | 1.5499 | 1.5432 |

[Inputs](sol2/job22/C22/inputs.txt) · [Raw runs](sol2/job22/C22/runs.jsonl.txt) · [Summary](sol2/job22/C22/summary.txt) · [Command](sol2/job22/C22-command.raw.txt)

## Prediction graded

The prediction was committed alone at `a6b8ea4ce32bf17fe366690ffbcaf375d152547e` after C22 and before H0.

| Comparison | Predicted CPU B/A | Observed pooled CPU B/A | Ratio in range | Expected CPU reading | Observed CPU reading | Reading met |
|---|---:|---:|---|---|---|---|
| H0 | 0.920–0.990 | 0.9315 | Yes | PAYS | PAYS | Yes |
| H1 | 0.900–0.985 | 0.9305 | Yes | PAYS | PAYS | Yes |
| H2 | 0.900–0.985 | 0.9405 | Yes | PAYS | PAYS | Yes |

| Hard vs soft CPU comparison | Expected | Observed | Reading met |
|---|---|---|---|
| H1 vs H0 | same within the error | same within the error | Yes |
| H2 vs H0 | same within the error | same within the error | Yes |

[Original prediction](sol2/job22/prediction.txt) · [UTC checkpoints](sol2/job22/stamps.txt)

## Timings H0–H2

| Comparison | A | B | Workload A / B | Metric | Blocks | Median | Pooled B/A | Mean | 95% t interval, df 15 | Below 1 |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| H0 | r15d | K_1 | W / W | Engine CPU | 16/16 | 0.9378 | 0.9315 | 0.9323 | [0.9175, 0.9471] | 16/16 |
| H0 | r15d | K_1 | W / W | Wall | 16/16 | 0.9436 | 0.9366 | 0.9375 | [0.9223, 0.9526] | 16/16 |
| H1 | r15d | K_1 | W20 / W20 | Engine CPU | 16/16 | 0.9175 | 0.9305 | 0.9308 | [0.9087, 0.9529] | 14/16 |
| H1 | r15d | K_1 | W20 / W20 | Wall | 16/16 | 0.9184 | 0.9317 | 0.9320 | [0.9096, 0.9544] | 14/16 |
| H2 | r15d | K_1 | W50 / W50 | Engine CPU | 16/16 | 0.9488 | 0.9405 | 0.9408 | [0.9252, 0.9565] | 16/16 |
| H2 | r15d | K_1 | W50 / W50 | Wall | 16/16 | 0.9502 | 0.9413 | 0.9417 | [0.9258, 0.9575] | 16/16 |

## Declared readings and arithmetic

| Comparison | CPU reading | 95% t interval | Pooled B/A | Wall pooled B/A [95% t interval] |
|---|---|---:|---:|---:|
| H0 | PAYS | [0.9175, 0.9471] | 0.9315 | 0.9366 [0.9223, 0.9526] |
| H1 | PAYS | [0.9087, 0.9529] | 0.9305 | 0.9317 [0.9096, 0.9544] |
| H2 | PAYS | [0.9252, 0.9565] | 0.9405 | 0.9413 [0.9258, 0.9575] |

The CPU interval wholly below one reads PAYS. Wholly above one reads COSTS. An interval containing one reads NOT SEEN.

| Comparison | CPU conclusion from 95% interval overlap | Hard minus soft pooled CPU ratio | Hard minus soft pooled wall ratio |
|---|---|---:|---:|
| H1 vs H0 | same within the error | -0.000993 | -0.004889 |
| H2 vs H0 | same within the error | +0.009045 | +0.004716 |

The pooled differences are descriptive. The CPU conclusion uses interval overlap as specified for this job.

### H0

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9505 | 0.9551 |
| 2 | BAAB | 0.9353 | 0.9431 |
| 3 | ABBA | 0.9390 | 0.9439 |
| 4 | BAAB | 0.9000 | 0.9043 |
| 5 | ABBA | 0.9378 | 0.9432 |
| 6 | BAAB | 0.9277 | 0.9306 |
| 7 | ABBA | 0.9141 | 0.9169 |
| 8 | BAAB | 0.9378 | 0.9442 |
| 9 | ABBA | 0.9481 | 0.9523 |
| 10 | BAAB | 0.9594 | 0.9640 |
| 11 | ABBA | 0.8667 | 0.8704 |
| 12 | BAAB | 0.9066 | 0.9114 |
| 13 | ABBA | 0.9469 | 0.9535 |
| 14 | BAAB | 0.9162 | 0.9222 |
| 15 | ABBA | 0.9886 | 0.9962 |
| 16 | BAAB | 0.9420 | 0.9481 |

[Inputs](sol2/job22/H0/inputs.txt) · [Raw runs](sol2/job22/H0/runs.jsonl.txt) · [Summary](sol2/job22/H0/summary.txt) · [Command](sol2/job22/H0-command.raw.txt)

### H1

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9084 | 0.9094 |
| 2 | BAAB | 0.9106 | 0.9123 |
| 3 | ABBA | 1.0585 | 1.0607 |
| 4 | BAAB | 0.9093 | 0.9099 |
| 5 | ABBA | 0.9340 | 0.9354 |
| 6 | BAAB | 0.9057 | 0.9072 |
| 7 | ABBA | 0.9370 | 0.9381 |
| 8 | BAAB | 0.9162 | 0.9181 |
| 9 | ABBA | 0.9027 | 0.9029 |
| 10 | BAAB | 1.0011 | 1.0046 |
| 11 | ABBA | 0.9031 | 0.9023 |
| 12 | BAAB | 0.9087 | 0.9111 |
| 13 | ABBA | 0.9281 | 0.9285 |
| 14 | BAAB | 0.9243 | 0.9262 |
| 15 | ABBA | 0.9260 | 0.9271 |
| 16 | BAAB | 0.9187 | 0.9188 |

[Inputs](sol2/job22/H1/inputs.txt) · [Raw runs](sol2/job22/H1/runs.jsonl.txt) · [Summary](sol2/job22/H1/summary.txt) · [Command](sol2/job22/H1-command.raw.txt)

### H2

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9530 | 0.9525 |
| 2 | BAAB | 0.9490 | 0.9504 |
| 3 | ABBA | 0.9080 | 0.9083 |
| 4 | BAAB | 0.9592 | 0.9598 |
| 5 | ABBA | 0.9536 | 0.9548 |
| 6 | BAAB | 0.9351 | 0.9356 |
| 7 | ABBA | 0.9195 | 0.9204 |
| 8 | BAAB | 0.9806 | 0.9821 |
| 9 | ABBA | 0.9479 | 0.9479 |
| 10 | BAAB | 0.9524 | 0.9533 |
| 11 | ABBA | 0.8642 | 0.8644 |
| 12 | BAAB | 0.9485 | 0.9499 |
| 13 | ABBA | 0.9281 | 0.9293 |
| 14 | BAAB | 0.9852 | 0.9873 |
| 15 | ABBA | 0.9152 | 0.9155 |
| 16 | BAAB | 0.9539 | 0.9548 |

[Inputs](sol2/job22/H2/inputs.txt) · [Raw runs](sol2/job22/H2/runs.jsonl.txt) · [Summary](sol2/job22/H2/summary.txt) · [Command](sol2/job22/H2-command.raw.txt)

## Facts

The 3 completed engine comparisons contributed 192 timed runs and 48 warm-ups. The independent readback checks workload and launch identities and recomputes ratios from the archived receipts. Procfs verified 280 of 280 archived comparison and control runs. [Independent readback](sol2/job22/timing_readback.py.txt)

## Suspicions

The hard-node stop path may change kF's relative CPU cost. The declared interval comparison measures that difference for the workload as a whole. [H0–H2 raw receipts](sol2/job22/)

## What this check cannot see

> The PC's Windows loader, its clang 23 and its own profile, its Zen 5 processor with 16 engines at once, its trained
net (net768 is synthetic), its own openings; differences between the hard and the soft limit smaller than about
2 % (your intervals are about that wide).

## What I did not do

Timing used two frozen binaries and one pinned cloud worker per replay. The workloads used the pinned synthetic net and the recorded book slices. [Publication layout](sol2/job22/publication-layout.raw.txt)

## What I am not sure about

The hard replays use shorter slices of the opening book, so the observed soft-to-hard difference also includes that workload change. The comparisons measure the entire kF stack together. [Independent readback](sol2/job22/timing_readback.py.txt)
