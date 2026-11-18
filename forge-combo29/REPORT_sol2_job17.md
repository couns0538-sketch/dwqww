# sol2 — Job 17 W replay with three engines at once

## Step 0 — machine and frozen identities

Debian Clang 19.1.7 was verified. The cloud VM reports AMD EPYC 9V74, five logical CPUs on five guest cores, one thread per core and shared 32 MiB L3. `nproc` reports five and the cgroup capacity is four CPU equivalents. The three worker and engine pairs use logical CPUs 1, 2 and 3 on distinct guest cores. Each of the frozen r15d, kF and Group G executables matched its Job 16 SHA-256 and independently passed W at its unchanged 72-character launch path. [Machine and gate receipts](sol2/job17/step0-command.raw.txt) · [Frozen hashes](sol2/job17/clang-executables.raw.txt) · [Job 16 build gates](REPORT_sol2_job16.md#step-1--build-receipts-and-launch-arms)

All Step 0 builds match W with 20 games, 2,247 searches, 7,905,938 last-info nodes, 9,189,426 final nodes and trace `7f78d3aec021ab01`. W uses PC20, Threads 1, Hash 16 MiB, net768 and `go softnodes 2000` on book lines 7001–7020. [r15d](sol2/job17/step0/r15d.result.raw.txt#L2-L6) · [kF](sol2/job17/step0/kF.result.raw.txt#L2-L6) · [G_1](sol2/job17/step0/G_1.result.raw.txt#L2-L6) · [W signature](sol2/job17/known-answer.txt#L2-L6)

| Arm | Engine argv[0] | Characters | Device | Inode | SHA-256 |
|---|---|---:|---:|---:|---|
| r15d | `/workspace/work/sol2-job16/arms/r15dxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 280450 | `540e63c0b7cf2512f1716657aded48b0558022b49c0fe8489596195cf2035834` |
| kF | `/workspace/work/sol2-job16/arms/K_1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 280452 | `da5df215a6aa255261d4e5574474da7c82aad1a9e95df83e15d5b38963ef439d` |
| G_1 | `/workspace/work/sol2-job16/arms/G_1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 280454 | `f083de3cd62f29149bc26e4f1eb8cff6ad83c792001dd3b0a70877d55d57f2e1` |

Each engine receives `LC_ALL=C` and `TZ=UTC`, 16 bytes, SHA-256 `4d41c4c11fcc6efa3bd339441ec9b26e6a1442056205420dc4b11e93dbff2570`. [Arms](sol2/job17/arms.txt)

## Prediction graded

The prediction was committed alone at `969df9ec22f79a094a25b06d6b97412583daab57` after Step 0 and before L0.

| Comparison | Predicted CPU B/A | Observed pooled CPU B/A | Within range |
|---|---:|---:|---|
| L0 | 0.940–1.060 | 0.9988 | Yes |
| L1 | 0.900–0.995 | 0.9563 | Yes |
| L2 | 0.940–1.035 | 0.9897 | Yes |

[Original prediction](sol2/job17/prediction.txt) · [UTC checkpoints](sol2/job17/stamps.txt)

## Step 2 — timing comparisons

Each run started three copies of one arm together on distinct pinned CPUs. All copies played W. Run CPU sums the engine processes' user and system times. Run wall starts when the coordinator releases the shared pre-launch barrier and ends when the last engine is reaped. The first run of each block was a recorded warm-up. The timed order was ABBA in odd blocks and BAAB in even blocks. A block qualified only when every worker in its runs matched the frozen W signature. Each complete comparison reports B/A with a Student t interval based on the 16 block ratios and 15 degrees of freedom. [Timing command](sol2/job17/run_campaign.sh.txt) · [Independent readback](sol2/job17/timing_readback.py.txt)

| Comparison | A | B | Metric | Blocks | Median | Pooled B/A | Mean | 95% t interval, df 15 | Below 1 |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| L0 | r15d | r15d | Engine CPU | 16/16 | 1.0040 | 0.9988 | 1.0001 | [0.973607, 1.026683] | 6/16 |
| L0 | r15d | r15d | Wall | 16/16 | 1.0076 | 0.9990 | 1.0007 | [0.972257, 1.029070] | 7/16 |
| L1 | r15d | kF | Engine CPU | 16/16 | 0.9553 | 0.9563 | 0.9566 | [0.942658, 0.970544] | 15/16 |
| L1 | r15d | kF | Wall | 16/16 | 0.9684 | 0.9646 | 0.9649 | [0.950654, 0.979176] | 14/16 |
| L2 | r15d | G_1 | Engine CPU | 16/16 | 0.9750 | 0.9897 | 0.9913 | [0.960234, 1.022308] | 11/16 |
| L2 | r15d | G_1 | Wall | 16/16 | 0.9883 | 0.9947 | 0.9967 | [0.962100, 1.031257] | 10/16 |

## Declared readings and arithmetic

| Metric | L0 floor | kF under load, L1 | Group G under load, L2 |
|---|---|---|---|
| Engine CPU | L0 interval contains 1 | PAYS | Criterion unmet |
| Wall | L0 interval contains 1 | PAYS | Criterion unmet |

L1 or L2 pays when its 95% t interval lies wholly below 1. The contrasts below describe changes from one engine to three at once. Ratios use the same r15d reference and W.

| Comparison | Metric | Three-engine mean [t interval] | One-engine mean [t interval] | Difference | Subtracted t endpoints | Approximate propagated 95% t interval | Effective df |
|---|---|---:|---:|---:|---:|---:|---:|
| L1 | Engine CPU | 0.956601 [0.942658, 0.970544] | 0.950212 [0.941547, 0.958876] | +0.006389 | [-0.016218, 0.028996] | [-0.009636, 0.022414] | 29.36 |
| L1 | Wall | 0.964915 [0.950654, 0.979176] | 0.956030 [0.947158, 0.964902] | +0.008885 | [-0.014248, 0.032019] | [-0.007510, 0.025281] | 29.40 |
| L2 | Engine CPU | 0.991271 [0.960234, 1.022308] | 0.987941 [0.972235, 1.003646] | +0.003331 | [-0.043412, 0.050073] | [-0.030496, 0.037157] | 22.21 |
| L2 | Wall | 0.996678 [0.962100, 1.031257] | 0.989165 [0.973434, 1.004895] | +0.007514 | [-0.042795, 0.057822] | [-0.029556, 0.044583] | 20.95 |

L1 uses Job 15’s unrounded inverse-variance mean across four path lengths, which gives 0.9502 when rounded on CPU. The reported Job 15 weights use each interval radius divided by 2.131. I calculated a reference t interval with variance `1 / sum(weights)` and Welch–Satterthwaite effective degrees of freedom. [U40](sol2/job15/U40/summary.txt#L112-L146) · [U56](sol2/job15/U56/summary.txt#L112-L146) · [U72](sol2/job15/U72/summary.txt#L112-L146) · [U88](sol2/job15/U88/summary.txt#L112-L146)

L2 uses Job 16’s R1 arithmetic block means and their original t intervals. [R1](sol2/job16/R1/summary.txt#L112-L146)

The difference is the three-engine mean minus the one-engine mean. Subtracted endpoints use `[load lower − single upper, load upper − single lower]`. Under an independence assumption, the approximate 95% t interval adds the variances obtained from the interval radii and applies a Welch–Satterthwaite t multiplier. Endpoint subtraction is descriptive. The propagated intervals for both builds and both timing measures include zero.

### L0

Logical CPUs 1, 2, 3. 80 attempted groups, 240 collected worker rows, 16 included blocks, 64 included timed groups. Procfs verified 240/240 engine launches. [Raw groups](sol2/job17/L0/runs.jsonl.txt)

The engine launch timestamps within each eligible group had a median spread of 40.0 µs and a maximum spread of 299.5 µs. [Raw groups](sol2/job17/L0/runs.jsonl.txt)

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 1.0347 | 1.0422 |
| 2 | BAAB | 1.0248 | 1.0313 |
| 3 | ABBA | 0.9706 | 0.9682 |
| 4 | BAAB | 1.0014 | 1.0134 |
| 5 | ABBA | 0.9717 | 0.9689 |
| 6 | BAAB | 1.0176 | 1.0018 |
| 7 | ABBA | 0.9652 | 0.9745 |
| 8 | BAAB | 1.0257 | 1.0287 |
| 9 | ABBA | 0.8707 | 0.8654 |
| 10 | BAAB | 1.0631 | 1.0548 |
| 11 | ABBA | 1.0066 | 1.0178 |
| 12 | BAAB | 1.0731 | 1.0644 |
| 13 | ABBA | 0.9733 | 0.9705 |
| 14 | BAAB | 1.0015 | 0.9841 |
| 15 | ABBA | 0.9525 | 0.9443 |
| 16 | BAAB | 1.0498 | 1.0802 |

[Inputs](sol2/job17/L0/inputs.txt) · [Raw groups](sol2/job17/L0/runs.jsonl.txt) · [Summary](sol2/job17/L0/summary.txt) · [Command](sol2/job17/L0-command.raw.txt)

### L1

Logical CPUs 1, 2, 3. 80 attempted groups, 240 collected worker rows, 16 included blocks, 64 included timed groups. Procfs verified 240/240 engine launches. [Raw groups](sol2/job17/L1/runs.jsonl.txt)

The engine launch timestamps within each eligible group had a median spread of 40.9 µs and a maximum spread of 1036.3 µs. [Raw groups](sol2/job17/L1/runs.jsonl.txt)

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9735 | 0.9732 |
| 2 | BAAB | 0.9345 | 0.9339 |
| 3 | ABBA | 0.9362 | 0.9372 |
| 4 | BAAB | 0.9646 | 0.9686 |
| 5 | ABBA | 0.9692 | 0.9855 |
| 6 | BAAB | 0.9173 | 0.9352 |
| 7 | ABBA | 0.9867 | 1.0022 |
| 8 | BAAB | 0.9493 | 0.9659 |
| 9 | ABBA | 0.9850 | 0.9934 |
| 10 | BAAB | 0.9447 | 0.9397 |
| 11 | ABBA | 0.9338 | 0.9500 |
| 12 | BAAB | 1.0093 | 1.0171 |
| 13 | ABBA | 0.9536 | 0.9682 |
| 14 | BAAB | 0.9570 | 0.9716 |
| 15 | ABBA | 0.9759 | 0.9735 |
| 16 | BAAB | 0.9150 | 0.9235 |

[Inputs](sol2/job17/L1/inputs.txt) · [Raw groups](sol2/job17/L1/runs.jsonl.txt) · [Summary](sol2/job17/L1/summary.txt) · [Command](sol2/job17/L1-command.raw.txt)

### L2

Logical CPUs 1, 2, 3. 80 attempted groups, 240 collected worker rows, 16 included blocks, 64 included timed groups. Procfs verified 240/240 engine launches. [Raw groups](sol2/job17/L2/runs.jsonl.txt)

The engine launch timestamps within each eligible group had a median spread of 39.6 µs and a maximum spread of 142.1 µs. [Raw groups](sol2/job17/L2/runs.jsonl.txt)

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 1.0092 | 1.0132 |
| 2 | BAAB | 0.9741 | 0.9978 |
| 3 | ABBA | 0.9902 | 1.0077 |
| 4 | BAAB | 0.9648 | 0.9811 |
| 5 | ABBA | 0.9496 | 0.9448 |
| 6 | BAAB | 0.9865 | 0.9751 |
| 7 | ABBA | 0.9758 | 0.9641 |
| 8 | BAAB | 0.9465 | 0.9390 |
| 9 | ABBA | 1.0072 | 1.0329 |
| 10 | BAAB | 0.9057 | 0.8978 |
| 11 | ABBA | 1.1371 | 1.1299 |
| 12 | BAAB | 0.9717 | 0.9955 |
| 13 | ABBA | 0.9450 | 0.9424 |
| 14 | BAAB | 1.0667 | 1.1019 |
| 15 | ABBA | 0.9545 | 0.9354 |
| 16 | BAAB | 1.0759 | 1.0882 |

[Inputs](sol2/job17/L2/inputs.txt) · [Raw groups](sol2/job17/L2/runs.jsonl.txt) · [Summary](sol2/job17/L2/summary.txt) · [Command](sol2/job17/L2-command.raw.txt)

## Facts

The three comparisons included 192 timed groups and 48 warm-up groups. All 720 engine replays matched W and passed the procfs launch checks. The independent readback recomputed timing from the archived worker and group receipts. [Independent readback](sol2/job17/timing_readback.py.txt)

## Suspicions

Sharing cache or memory bandwidth could change an engine's time relative to r15d when other copies run concurrently. The three-engine measurements establish the relative timing under this load and leave the mechanism open. [Timing receipts](sol2/job17/)

## What this check cannot see

> The PC's Windows loader, its clang 23, its Zen 5 processor with 16 engines at once (three is not sixteen), its
trained net (net768 is synthetic), its own self-play openings.

## What I did not do

The experiment was limited to the frozen Clang 19.1.7 builds, pinned cloud workers and their W replays. [Publication layout](sol2/job17/publication-layout.raw.txt)

## What I am not sure about

The one-engine references came from earlier jobs. Differences between the measured ratios describe this host and these campaigns. Cache and memory counters would be needed to distinguish competing explanations.
