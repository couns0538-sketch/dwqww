# sol2 — Job 23 kF timing at two 40-setting draws

## Step 0 — machine and frozen identities

Debian Clang 19.1.7 was verified. The cloud VM reports AMD EPYC 9V74, five logical CPUs on five guest cores, shared 32 MiB L3 and four CPU equivalents in the cgroup. Each engine and driver run on logical CPU 2. Frozen r15d and K_1 matched their Job 16 SHA-256 hashes and passed W in fresh processes from their existing 72-character paths with the fixed launch environment. Both complete UCI inventories declared all 40 required search settings as spins. [Machine and gate receipts](sol2/job23/step0-command.raw.txt) · [Frozen hashes](sol2/job23/clang-executables.raw.txt) · [Launch arms](sol2/job23/reference-arms.txt)

Both Step 0 builds matched W with 20 games, 2,247 searches, 7,905,938 last-info nodes, 9,189,426 final nodes and trace `7f78d3aec021ab01`. W uses PC20, Threads 1, Hash 16 MiB, net768 and `go softnodes 2000` on book lines 7001–7020. [r15d](sol2/job23/step0/r15d.result.raw.txt#L2-L6) · [K_1](sol2/job23/step0/K_1.result.raw.txt#L2-L6) · [W signature](sol2/job23/known-answer.txt#L2-L6)
The r15d UCI inventory declares all 40 settings as spins. [Raw UCI inventory](sol2/job23/step0/r15d.uci.stdout.txt)
The K_1 UCI inventory declares all 40 settings as spins. [Raw UCI inventory](sol2/job23/step0/K_1.uci.stdout.txt)

| Arm | Engine argv[0] | Characters | Device | Inode | SHA-256 |
|---|---|---:|---:|---:|---|
| r15d | `/workspace/work/sol2-job16/arms/r15dxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 280450 | `540e63c0b7cf2512f1716657aded48b0558022b49c0fe8489596195cf2035834` |
| K_1 | `/workspace/work/sol2-job16/arms/K_1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 280452 | `da5df215a6aa255261d4e5574474da7c82aad1a9e95df83e15d5b38963ef439d` |

Each engine receives `LC_ALL=C` and `TZ=UTC`, 16 bytes, SHA-256 `4d41c4c11fcc6efa3bd339441ec9b26e6a1442056205420dc4b11e93dbff2570`. [Arms](sol2/job23/reference-arms.txt)

### r15d UCI spin declarations

```text
option name DrawJitter type spin default 0 min 0 max 8
option name LmrQuietBase type spin default 85 min 0 max 300
option name LmrQuietDivisor type spin default 220 min 100 max 500
option name LmrNoisyBase type spin default 10 min 0 max 300
option name LmrNoisyDivisor type spin default 340 min 100 max 800
option name NullMoveMinDepth type spin default 3 min 1 max 10
option name NullMoveBase type spin default 3 min 1 max 6
option name NullMoveDepthDivisor type spin default 3 min 1 max 10
option name NullMoveEvalDivisor type spin default 200 min 50 max 1000
option name RfpDepth type spin default 8 min 0 max 15
option name RfpMargin type spin default 72 min 10 max 300
option name RfpImproving type spin default 40 min 0 max 200
option name RazorDepth type spin default 2 min 0 max 6
option name RazorBase type spin default 150 min 0 max 1000
option name RazorMultiplier type spin default 350 min 0 max 1000
option name FutilityDepth type spin default 7 min 0 max 15
option name FutilityBase type spin default 100 min 0 max 500
option name FutilityMultiplier type spin default 110 min 0 max 500
option name LmpBase type spin default 4 min 0 max 20
option name HistoryPruneDepth type spin default 3 min 0 max 10
option name HistoryPruneMultiplier type spin default 2048 min 0 max 20000
option name SeeQuietMultiplier type spin default 24 min 0 max 200
option name SeeNoisyMultiplier type spin default 150 min 0 max 1000
option name SingularDepth type spin default 7 min 2 max 20
option name SingularMargin type spin default 2 min 0 max 10
option name IirDepth type spin default 4 min 1 max 20
option name ProbcutDepth type spin default 5 min 1 max 20
option name ProbcutMargin type spin default 180 min 0 max 1000
option name QsFutilityMargin type spin default 160 min 0 max 1000
option name AspirationDelta type spin default 18 min 4 max 200
option name HistoryBonusQuadratic type spin default 20 min 0 max 100
option name HistoryBonusLinear type spin default 48 min 0 max 500
option name HistoryBonusMax type spin default 2048 min 100 max 10000
option name LmrHistoryDivisor type spin default 6000 min 1000 max 30000
option name CheckExtensionDepth type spin default 2 min 1 max 30
option name LmrCutoffThreshold type spin default 3 min 0 max 20
option name MaterialCorrectionWeight type spin default 100 min 0 max 300
option name CaptureFutilityBase type spin default 0 min 0 max 1000
option name FailLowContinuationBonus type spin default 0 min 0 max 300
option name EvalSwingMult type spin default 0 min 0 max 64
```

[Full UCI inventory](sol2/job23/step0/r15d.uci.stdout.txt)

### K_1 UCI spin declarations

```text
option name DrawJitter type spin default 0 min 0 max 8
option name LmrQuietBase type spin default 85 min 0 max 300
option name LmrQuietDivisor type spin default 220 min 100 max 500
option name LmrNoisyBase type spin default 10 min 0 max 300
option name LmrNoisyDivisor type spin default 340 min 100 max 800
option name NullMoveMinDepth type spin default 3 min 1 max 10
option name NullMoveBase type spin default 3 min 1 max 6
option name NullMoveDepthDivisor type spin default 3 min 1 max 10
option name NullMoveEvalDivisor type spin default 200 min 50 max 1000
option name RfpDepth type spin default 8 min 0 max 15
option name RfpMargin type spin default 72 min 10 max 300
option name RfpImproving type spin default 40 min 0 max 200
option name RazorDepth type spin default 2 min 0 max 6
option name RazorBase type spin default 150 min 0 max 1000
option name RazorMultiplier type spin default 350 min 0 max 1000
option name FutilityDepth type spin default 7 min 0 max 15
option name FutilityBase type spin default 100 min 0 max 500
option name FutilityMultiplier type spin default 110 min 0 max 500
option name LmpBase type spin default 4 min 0 max 20
option name HistoryPruneDepth type spin default 3 min 0 max 10
option name HistoryPruneMultiplier type spin default 2048 min 0 max 20000
option name SeeQuietMultiplier type spin default 24 min 0 max 200
option name SeeNoisyMultiplier type spin default 150 min 0 max 1000
option name SingularDepth type spin default 7 min 2 max 20
option name SingularMargin type spin default 2 min 0 max 10
option name IirDepth type spin default 4 min 1 max 20
option name ProbcutDepth type spin default 5 min 1 max 20
option name ProbcutMargin type spin default 180 min 0 max 1000
option name QsFutilityMargin type spin default 160 min 0 max 1000
option name AspirationDelta type spin default 18 min 4 max 200
option name HistoryBonusQuadratic type spin default 20 min 0 max 100
option name HistoryBonusLinear type spin default 48 min 0 max 500
option name HistoryBonusMax type spin default 2048 min 100 max 10000
option name LmrHistoryDivisor type spin default 6000 min 1000 max 30000
option name CheckExtensionDepth type spin default 2 min 1 max 30
option name LmrCutoffThreshold type spin default 3 min 0 max 20
option name MaterialCorrectionWeight type spin default 100 min 0 max 300
option name CaptureFutilityBase type spin default 0 min 0 max 1000
option name FailLowContinuationBonus type spin default 0 min 0 max 300
option name EvalSwingMult type spin default 0 min 0 max 64
```

[Full UCI inventory](sol2/job23/step0/K_1.uci.stdout.txt)

## Setting draw gates

| Workload | Book lines | Command | First r15d games / searches / last-info nodes / final nodes / trace | First K_1 | Differs from W |
|---|---|---|---|---|---|
| WD1 | 7001–7020 | `go softnodes 2000` | 20 / 2,616 / 8,625,233 / 10,735,148 / `ad3eee11d1b85bec`. [Raw first r15d](sol2/job23/draw-gates/WD1/A.r15d.result.raw.txt) · [Known answer](sol2/job23/known-answer-WD1.txt#L2-L6) | Matched. [Raw first K_1](sol2/job23/draw-gates/WD1/B.K_1.result.raw.txt) | Yes |
| WD100 | 7001–7020 | `go softnodes 2000` | 20 / 2,235 / 7,930,923 / 9,535,830 / `112771c5fca37ea4`. [Raw first r15d](sol2/job23/draw-gates/WD100/A.r15d.result.raw.txt) · [Known answer](sol2/job23/known-answer-WD100.txt#L2-L6) | Matched. [Raw first K_1](sol2/job23/draw-gates/WD100/B.K_1.result.raw.txt) | Yes |
| W2200 | 7001–7020 | `go softnodes 2200` | 20 / 2,446 / 8,919,843 / 11,342,512 / `475781ee88f28696`. [Raw first r15d](sol2/job23/draw-gates/W2200/A.r15d.result.raw.txt) · [Known answer](sol2/job23/known-answer-W2200.txt#L2-L6) | r15d-only control | — |

Each accepted draw has 40 ordered setting acknowledgments per engine run. The raw timing files preserve each observed signature, engine hash, workload, and block eligibility. [D1 settings](sol2/job23/draw-D1.txt) · [D100 settings](sol2/job23/draw-D100.txt)

## C23 control

| Comparison | A | B | Workload A / B | Metric | Blocks | Median | Pooled B/A | Mean | 95% t interval, df 7 | Below 1 |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| C23 | r15d | r15d | W / W2200 | Engine CPU | 8/8 | 1.1982 | 1.1923 | 1.1929 | [1.1598, 1.2260] | 0/8 |
| C23 | r15d | r15d | W / W2200 | Wall | 8/8 | 1.1884 | 1.1830 | 1.1835 | [1.1507, 1.2163] | 0/8 |

Changing the configured soft-node limit from 2,000 to 2,200 gave 2,247 and 2,446 searches. Each arm uses its own exact known answer. [W](sol2/job23/known-answer.txt#L2-L6) · [W2200](sol2/job23/known-answer-W2200.txt#L2-L6)

**PASS**. The CPU interval must lie wholly above one for W2200 relative to W.

### C23

Logical CPU 2. 40 attempted runs, 8 included blocks, 32 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 1.1347 | 1.1307 |
| 2 | BAAB | 1.2418 | 1.2332 |
| 3 | ABBA | 1.1935 | 1.1830 |
| 4 | BAAB | 1.2295 | 1.2213 |
| 5 | ABBA | 1.2029 | 1.1937 |
| 6 | BAAB | 1.1846 | 1.1718 |
| 7 | ABBA | 1.1376 | 1.1266 |
| 8 | BAAB | 1.2183 | 1.2077 |

[Inputs](sol2/job23/C23/inputs.txt) · [Raw runs](sol2/job23/C23/runs.jsonl.txt) · [Summary](sol2/job23/C23/summary.txt) · [Command](sol2/job23/C23-command.raw.txt)

## Prediction graded

The prediction was committed alone at `401e965a4d9086e1b5d74eee901145ee6f355fba` after C23 and before D0.

| Comparison | Predicted CPU B/A | Observed pooled CPU B/A | Ratio in range | Expected CPU reading | Observed CPU reading | Reading met |
|---|---:|---:|---|---|---|---|
| D0 | 0.920–0.990 | 0.9480 | Yes | PAYS | PAYS | Yes |
| D1 | 0.910–1.000 | 0.9460 | Yes | PAYS | PAYS | Yes |
| D2 | 0.910–1.000 | 0.9533 | Yes | PAYS | PAYS | Yes |

| Setting draw vs D0 CPU comparison | Expected | Observed | Reading met |
|---|---|---|---|
| D1 vs D0 | same within the error | same within the error | Yes |
| D2 vs D0 | same within the error | same within the error | Yes |

[Original prediction](sol2/job23/prediction.txt) · [UTC checkpoints](sol2/job23/stamps.txt)

## Timings D0–D2

| Comparison | A | B | Workload A / B | Metric | Blocks | Median | Pooled B/A | Mean | 95% t interval, df 15 | Below 1 |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| D0 | r15d | K_1 | W / W | Engine CPU | 16/16 | 0.9407 | 0.9480 | 0.9485 | [0.9314, 0.9655] | 15/16 |
| D0 | r15d | K_1 | W / W | Wall | 16/16 | 0.9480 | 0.9540 | 0.9546 | [0.9365, 0.9726] | 14/16 |
| D1 | r15d | K_1 | WD1 / WD1 | Engine CPU | 16/16 | 0.9401 | 0.9460 | 0.9472 | [0.9244, 0.9700] | 14/16 |
| D1 | r15d | K_1 | WD1 / WD1 | Wall | 16/16 | 0.9470 | 0.9538 | 0.9551 | [0.9318, 0.9783] | 13/16 |
| D2 | r15d | K_1 | WD100 / WD100 | Engine CPU | 16/16 | 0.9500 | 0.9533 | 0.9538 | [0.9379, 0.9696] | 14/16 |
| D2 | r15d | K_1 | WD100 / WD100 | Wall | 16/16 | 0.9552 | 0.9592 | 0.9597 | [0.9437, 0.9757] | 14/16 |

## Declared readings and arithmetic

| Comparison | CPU reading | 95% t interval | Pooled B/A | Wall pooled B/A [95% t interval] |
|---|---|---:|---:|---:|
| D0 | PAYS | [0.9314, 0.9655] | 0.9480 | 0.9540 [0.9365, 0.9726] |
| D1 | PAYS | [0.9244, 0.9700] | 0.9460 | 0.9538 [0.9318, 0.9783] |
| D2 | PAYS | [0.9379, 0.9696] | 0.9533 | 0.9592 [0.9437, 0.9757] |

The CPU interval wholly below one reads PAYS. Wholly above one reads COSTS. An interval containing one reads NOT SEEN.

| Comparison | CPU conclusion from 95% interval overlap | Draw minus PC20 pooled CPU ratio | Draw minus PC20 pooled wall ratio |
|---|---|---:|---:|
| D1 vs D0 | same within the error | -0.001942 | -0.000155 |
| D2 vs D0 | same within the error | +0.005285 | +0.005220 |

The pooled differences are descriptive. The CPU conclusion uses interval overlap as specified for this job.

### D0

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9542 | 0.9611 |
| 2 | BAAB | 0.9291 | 0.9337 |
| 3 | ABBA | 0.9395 | 0.9470 |
| 4 | BAAB | 0.9652 | 0.9718 |
| 5 | ABBA | 0.9263 | 0.9292 |
| 6 | BAAB | 0.9583 | 0.9665 |
| 7 | ABBA | 1.0255 | 1.0384 |
| 8 | BAAB | 0.9852 | 0.9913 |
| 9 | ABBA | 0.9152 | 0.9195 |
| 10 | BAAB | 0.9064 | 0.9103 |
| 11 | ABBA | 0.9494 | 0.9544 |
| 12 | BAAB | 0.9333 | 0.9400 |
| 13 | ABBA | 0.9420 | 0.9490 |
| 14 | BAAB | 0.9141 | 0.9169 |
| 15 | ABBA | 0.9364 | 0.9426 |
| 16 | BAAB | 0.9957 | 1.0014 |

[Inputs](sol2/job23/D0/inputs.txt) · [Raw runs](sol2/job23/D0/runs.jsonl.txt) · [Summary](sol2/job23/D0/summary.txt) · [Command](sol2/job23/D0-command.raw.txt)

### D1

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9289 | 0.9367 |
| 2 | BAAB | 0.8873 | 0.8949 |
| 3 | ABBA | 0.9180 | 0.9234 |
| 4 | BAAB | 0.9415 | 0.9457 |
| 5 | ABBA | 0.9604 | 0.9666 |
| 6 | BAAB | 0.9431 | 0.9515 |
| 7 | ABBA | 1.0572 | 1.0687 |
| 8 | BAAB | 0.8872 | 0.8945 |
| 9 | ABBA | 0.9226 | 0.9294 |
| 10 | BAAB | 0.9408 | 0.9483 |
| 11 | ABBA | 0.9560 | 0.9654 |
| 12 | BAAB | 0.9372 | 0.9445 |
| 13 | ABBA | 1.0083 | 1.0159 |
| 14 | BAAB | 0.9916 | 1.0010 |
| 15 | ABBA | 0.9360 | 0.9440 |
| 16 | BAAB | 0.9394 | 0.9506 |

[Inputs](sol2/job23/D1/inputs.txt) · [Raw runs](sol2/job23/D1/runs.jsonl.txt) · [Summary](sol2/job23/D1/summary.txt) · [Command](sol2/job23/D1-command.raw.txt)

### D2

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 1.0089 | 1.0138 |
| 2 | BAAB | 0.9668 | 0.9717 |
| 3 | ABBA | 0.9471 | 0.9524 |
| 4 | BAAB | 0.9507 | 0.9554 |
| 5 | ABBA | 0.9554 | 0.9604 |
| 6 | BAAB | 0.9492 | 0.9549 |
| 7 | ABBA | 1.0071 | 1.0144 |
| 8 | BAAB | 0.9534 | 0.9603 |
| 9 | ABBA | 0.9198 | 0.9271 |
| 10 | BAAB | 0.9314 | 0.9367 |
| 11 | ABBA | 0.9075 | 0.9129 |
| 12 | BAAB | 0.9447 | 0.9498 |
| 13 | ABBA | 0.9118 | 0.9165 |
| 14 | BAAB | 0.9465 | 0.9535 |
| 15 | ABBA | 0.9818 | 0.9903 |
| 16 | BAAB | 0.9779 | 0.9855 |

[Inputs](sol2/job23/D2/inputs.txt) · [Raw runs](sol2/job23/D2/runs.jsonl.txt) · [Summary](sol2/job23/D2/summary.txt) · [Command](sol2/job23/D2-command.raw.txt)

## Facts

The three comparisons contributed 192 timed runs and 48 warm-ups. Independent readback verified all 280 comparison and control signatures and recomputed their timing ratios. It also verified 6,400 option acknowledgments across 160 draw replays. Procfs verified all 280 launch receipts. [Independent readback](sol2/job23/timing_readback.py.txt)

## Suspicions

Search setting changes can shift how much time the engine spends in evaluation, move generation and the transposition table. The intervals compare the full profiled kF stack with r15d for the two specified draws. [D0–D2 raw receipts](sol2/job23/)

## What this check cannot see

> The tune's final values (not known before it ends; two random points stand in for them), the PC's Windows loader,
its clang 23 and its own profile, its Zen 5 processor with 16 engines at once, its trained net (net768 is
synthetic), differences between settings smaller than about 2 % (your intervals are about that wide).

## What I did not do

Timing used two frozen binaries, one pinned cloud worker per replay and the recorded synthetic-net workload. [Publication layout](sol2/job23/publication-layout.raw.txt)

## What I am not sure about

The two draws sample the joint setting space. The measurements leave the effect of individual settings and the final tuned values unresolved. [Independent readback](sol2/job23/timing_readback.py.txt)
