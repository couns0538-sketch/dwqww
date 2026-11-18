# sol2 — Job 19 independent builds of the kF prefix ladder

## Step 0 — machine and frozen identities

Debian Clang 19.1.7 was verified. The cloud VM reports AMD EPYC 9V74, five logical CPUs on five guest cores, shared 32 MiB L3 and four CPU equivalents in the cgroup. Each replay uses one engine and its driver pinned to logical CPU 2. Frozen r15d, K_2, P4, P8 and P10 matched their Job 16 or Job 18 hashes and each passed a fresh W replay from its original 72-character launch path with the fixed environment. [Machine and gate receipts](sol2/job19/step0-command.raw.txt) · [Frozen hashes](sol2/job19/clang-executables.raw.txt) · [Reference launch arms](sol2/job19/reference-arms.txt)

All five Step 0 builds matched W with 20 games, 2,247 searches, 7,905,938 last-info nodes, 9,189,426 final nodes and trace `7f78d3aec021ab01`. W uses PC20, Threads 1, Hash 16 MiB, net768 and `go softnodes 2000` on book lines 7001–7020. [r15d](sol2/job19/step0/r15d.result.raw.txt#L2-L6) · [K_2](sol2/job19/step0/K_2.result.raw.txt#L2-L6) · [P4](sol2/job19/step0/P4.result.raw.txt#L2-L6) · [P8](sol2/job19/step0/P8.result.raw.txt#L2-L6) · [P10](sol2/job19/step0/P10.result.raw.txt#L2-L6) · [W signature](sol2/job19/known-answer.txt#L2-L6)

| Frozen build | SHA-256 | Fresh W games / searches / last-info / final / trace |
|---|---|---|
| r15d | [`540e63c0b7cf2512f1716657aded48b0558022b49c0fe8489596195cf2035834`](sol2/job19/clang-executables.raw.txt#L1) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job19/step0/r15d.result.raw.txt#L2-L6) |
| K_2 | [`2890d5b1cf4f332a87e572222d5a24ecdc014e0920a6ade776c4f22f3730187f`](sol2/job19/clang-executables.raw.txt#L2) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job19/step0/K_2.result.raw.txt#L2-L6) |
| P4 | [`791a4fc172886cb28c5648c0d7a808d23814786bd67e340c3cb8b242a8df4573`](sol2/job19/clang-executables.raw.txt#L3) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job19/step0/P4.result.raw.txt#L2-L6) |
| P8 | [`7b2c2b2a4807680d4d17ca3e32f037ada215edc9cdf251d2c4d4060a6a637c1d`](sol2/job19/clang-executables.raw.txt#L4) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job19/step0/P8.result.raw.txt#L2-L6) |
| P10 | [`dee47b3cd9135abb2c52eb58a741c0e7d65875e08d525c1438d72f1f88a390ad`](sol2/job19/clang-executables.raw.txt#L5) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job19/step0/P10.result.raw.txt#L2-L6) |

## Step 1 — independent second prefix builds and launch arms

Each second prefix executable differs byte-for-byte from its first build. The corresponding source trees match exactly. [Executable comparisons](sol2/job19/prefix-build-twins.raw.txt)

The fresh source copies apply the recorded carbon2 stack in its original order. P4_2 stops after piece 04, P8_2 after piece 08 and P10_2 after piece 10. Each prefix used its own profile run with the Clang recipe from Job 16. Every default pin used a fresh process with no UCI options. Each W entry links to a separate fresh process's games, searches, last-info nodes, final nodes and trace.

| Build | SHA-256 | bench 11 nodes | bench 13 nodes | go perft 5 nodes | W games / searches / last-info / final / trace | Timing gate |
|---|---|---:|---:|---:|---|---|
| P4_2 | [`19a3a47029f7947ba9fd8e348fc6a41889d8ee549af9f32996de58837cdeb78e`](sol2/job19/step1-P4_2/clang-sha256.raw.txt#L1) | [312,866](sol2/job19/build-checks/P4_2/default-pins.raw.txt#L7) | [862,329](sol2/job19/build-checks/P4_2/default-pins.raw.txt#L14) | [4,865,609](sol2/job19/build-checks/P4_2/default-pins.raw.txt#L42) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job19/build-checks/P4_2/W.result.raw.txt#L2-L6) | Pass |
| P8_2 | [`04fc4c88cbe6841a0960eb194125725555ff11cc1fa4aac116668fe9cb937055`](sol2/job19/step1-P8_2/clang-sha256.raw.txt#L1) | [312,866](sol2/job19/build-checks/P8_2/default-pins.raw.txt#L7) | [862,329](sol2/job19/build-checks/P8_2/default-pins.raw.txt#L14) | [4,865,609](sol2/job19/build-checks/P8_2/default-pins.raw.txt#L42) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job19/build-checks/P8_2/W.result.raw.txt#L2-L6) | Pass |
| P10_2 | [`208b733ed56273edd1c607a86347e744588f4ea888076e7f3c51085d50e6d0fb`](sol2/job19/step1-P10_2/clang-sha256.raw.txt#L1) | [312,866](sol2/job19/build-checks/P10_2/default-pins.raw.txt#L7) | [862,329](sol2/job19/build-checks/P10_2/default-pins.raw.txt#L14) | [4,865,609](sol2/job19/build-checks/P10_2/default-pins.raw.txt#L42) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job19/build-checks/P10_2/W.result.raw.txt#L2-L6) | Pass |

[Build identities and gate status](sol2/job19/builds.txt)
[Stack patch provenance and SHA-256](sol2/job19/prefix-patch-provenance.raw.txt)
[P4_2 gates](sol2/job19/build-checks/P4_2/checks.raw.txt) · [P4_2 build commands](sol2/job19/step1-P4_2/commands.raw.txt)
[P8_2 gates](sol2/job19/build-checks/P8_2/checks.raw.txt) · [P8_2 build commands](sol2/job19/step1-P8_2/commands.raw.txt)
[P10_2 gates](sol2/job19/build-checks/P10_2/checks.raw.txt) · [P10_2 build commands](sol2/job19/step1-P10_2/commands.raw.txt)

### P4_2 patch commands

```sh
cd /workspace/work/sol2-job19/.P4_2.partial
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job19/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job19/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job19/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job19/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job19/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job19/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job19/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job19/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job19/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job19/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job19/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job19/patches/04_S7.patch.txt
```

[P4_2 source receipt](sol2/job19/prefix-source/P4_2.git-apply.raw.txt#L34-L100) · [P4_2 source SHA-256 manifest](sol2/job19/prefix-source/P4_2-source-sha256.raw.txt) · [29 files match Job 18 P4](sol2/job19/prefix-source/P4_2.git-apply.raw.txt#L171)

### P8_2 patch commands

```sh
cd /workspace/work/sol2-job19/.P8_2.partial
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job19/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job19/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job19/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job19/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job19/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job19/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job19/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job19/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job19/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job19/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job19/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job19/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job19/patches/05_G1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job19/patches/05_G1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job19/patches/05_G1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job19/patches/06_G2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job19/patches/06_G2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job19/patches/06_G2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job19/patches/07_G3.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job19/patches/07_G3.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job19/patches/07_G3.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job19/patches/08_G4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job19/patches/08_G4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job19/patches/08_G4.patch.txt
```

[P8_2 source receipt](sol2/job19/prefix-source/P8_2.git-apply.raw.txt#L34-L182) · [P8_2 source SHA-256 manifest](sol2/job19/prefix-source/P8_2-source-sha256.raw.txt) · [29 files match Job 18 P8](sol2/job19/prefix-source/P8_2.git-apply.raw.txt#L259)

### P10_2 patch commands

```sh
cd /workspace/work/sol2-job19/.P10_2.partial
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job19/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job19/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job19/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job19/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job19/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job19/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job19/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job19/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job19/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job19/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job19/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job19/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job19/patches/05_G1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job19/patches/05_G1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job19/patches/05_G1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job19/patches/06_G2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job19/patches/06_G2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job19/patches/06_G2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job19/patches/07_G3.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job19/patches/07_G3.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job19/patches/07_G3.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job19/patches/08_G4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job19/patches/08_G4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job19/patches/08_G4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job19/patches/09_W1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job19/patches/09_W1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job19/patches/09_W1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job19/patches/10_W2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job19/patches/10_W2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job19/patches/10_W2.patch.txt
```

[P10_2 source receipt](sol2/job19/prefix-source/P10_2.git-apply.raw.txt#L34-L228) · [P10_2 source SHA-256 manifest](sol2/job19/prefix-source/P10_2-source-sha256.raw.txt) · [29 files match Job 18 P10](sol2/job19/prefix-source/P10_2.git-apply.raw.txt#L299)

| Arm | Engine argv[0] | Characters | Device | Inode | SHA-256 |
|---|---|---:|---:|---:|---|
| r15d | `/workspace/work/sol2-job16/arms/r15dxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 280450 | `540e63c0b7cf2512f1716657aded48b0558022b49c0fe8489596195cf2035834` |
| P4_2 | `/workspace/work/sol2-job19/arms/P4_2xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 289519 | `19a3a47029f7947ba9fd8e348fc6a41889d8ee549af9f32996de58837cdeb78e` |
| P8_2 | `/workspace/work/sol2-job19/arms/P8_2xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 289521 | `04fc4c88cbe6841a0960eb194125725555ff11cc1fa4aac116668fe9cb937055` |
| P10_2 | `/workspace/work/sol2-job19/arms/P10_2xxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 289523 | `208b733ed56273edd1c607a86347e744588f4ea888076e7f3c51085d50e6d0fb` |
| K_2 | `/workspace/work/sol2-job16/arms/K_2xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 280458 | `2890d5b1cf4f332a87e572222d5a24ecdc014e0920a6ade776c4f22f3730187f` |

Each engine receives `LC_ALL=C` and `TZ=UTC`, 16 bytes, SHA-256 `4d41c4c11fcc6efa3bd339441ec9b26e6a1442056205420dc4b11e93dbff2570`. [Arms](sol2/job19/arms.txt)

## Prediction graded

The prediction was committed alone at `fcc6e24157e673e6b39d70241b8de638238a1fa9` after Step 1 and before L1b.

| Comparison | Predicted CPU B/A | Observed pooled CPU B/A | Ratio in range | Expected joint reading | Observed joint reading | Reading met |
|---|---:|---:|---|---|---|---|
| L1b | 0.960–1.035 | 0.9768 | Yes | NOT SEEN | NOT SEEN | Yes |
| L2b | 0.950–1.035 | 0.9912 | Yes | NOT SEEN | NOT SEEN | Yes |
| L3b | 0.940–1.020 | 0.9846 | Yes | PAYS | NOT SEEN | No |
| L4b | 0.940–1.020 | 0.9679 | Yes | PAYS | PAYS | Yes |

[Original prediction](sol2/job19/prediction.txt) · [UTC checkpoints](sol2/job19/stamps.txt)

## Step 2 — timing comparisons

Every run started a fresh engine on logical CPU 2 with workload W and the fixed replacement environment. Each arm used a 72-character executable path. Odd blocks used ABBA and even blocks used BAAB. One recorded warm-up preceded each block, and only its four timed runs entered the ratio. A run outside the W signature gate excluded its block. Engine CPU is the reaped engine process's user plus system time. Wall is the full driver call interval. Each complete comparison reports B/A with a Student t interval from the 16 block ratios and 15 degrees of freedom. [Timing commands](sol2/job19/run_campaign.sh.txt) · [Independent readback](sol2/job19/timing_readback.py.txt)

| Comparison | A | B | Metric | Blocks | Median | Pooled B/A | Mean | 95% t interval, df 15 | Below 1 |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| L1b | r15d | P4_2 | Engine CPU | 16/16 | 0.9781 | 0.9768 | 0.9774 | [0.9647, 0.9902] | 15/16 |
| L1b | r15d | P4_2 | Wall | 16/16 | 0.9772 | 0.9762 | 0.9768 | [0.9637, 0.9899] | 15/16 |
| L2b | P4_2 | P8_2 | Engine CPU | 16/16 | 0.9865 | 0.9912 | 0.9916 | [0.9744, 1.0088] | 9/16 |
| L2b | P4_2 | P8_2 | Wall | 16/16 | 0.9867 | 0.9927 | 0.9931 | [0.9754, 1.0108] | 9/16 |
| L3b | P8_2 | P10_2 | Engine CPU | 16/16 | 0.9771 | 0.9846 | 0.9852 | [0.9687, 1.0016] | 11/16 |
| L3b | P8_2 | P10_2 | Wall | 16/16 | 0.9785 | 0.9864 | 0.9870 | [0.9698, 1.0042] | 11/16 |
| L4b | P10_2 | K_2 | Engine CPU | 16/16 | 0.9727 | 0.9679 | 0.9686 | [0.9520, 0.9853] | 14/16 |
| L4b | P10_2 | K_2 | Wall | 16/16 | 0.9742 | 0.9706 | 0.9714 | [0.9545, 0.9882] | 13/16 |

## Declared readings and arithmetic

Each step shows the pooled B/A ratio, the arithmetic mean and its 95% t interval. The joint reading uses CPU.

| First ladder → second ladder | Job 18 CPU | Job 19 CPU | Job 18 wall | Job 19 wall | Joint CPU reading |
|---|---:|---:|---:|---:|---|
| [L1](sol2/job18/L1/summary.txt#L112-L146) → [L1b](sol2/job19/L1b/summary.txt#L112-L146) | 0.9999 / 1.0006 [0.9758, 1.0255] | 0.9768 / 0.9774 [0.9647, 0.9902] | 1.0006 / 1.0014 [0.9758, 1.0271] | 0.9762 / 0.9768 [0.9637, 0.9899] | NOT SEEN |
| [L2](sol2/job18/L2/summary.txt#L112-L146) → [L2b](sol2/job19/L2b/summary.txt#L112-L146) | 0.9957 / 0.9975 [0.9642, 1.0309] | 0.9912 / 0.9916 [0.9744, 1.0088] | 0.9963 / 0.9982 [0.9644, 1.0320] | 0.9927 / 0.9931 [0.9754, 1.0108] | NOT SEEN |
| [L3](sol2/job18/L3/summary.txt#L112-L146) → [L3b](sol2/job19/L3b/summary.txt#L112-L146) | 0.9714 / 0.9733 [0.9476, 0.9990] | 0.9846 / 0.9852 [0.9687, 1.0016] | 0.9721 / 0.9742 [0.9478, 1.0006] | 0.9864 / 0.9870 [0.9698, 1.0042] | NOT SEEN |
| [L4](sol2/job18/L4/summary.txt#L112-L146) → [L4b](sol2/job19/L4b/summary.txt#L112-L146) | 0.9756 / 0.9763 [0.9574, 0.9951] | 0.9679 / 0.9686 [0.9520, 0.9853] | 0.9784 / 0.9790 [0.9597, 0.9984] | 0.9706 / 0.9714 [0.9545, 0.9882] | PAYS |

A step PAYS when both CPU intervals lie wholly below 1 and COSTS when both lie wholly above 1. Other pairs give NOT SEEN. Wall intervals are descriptive.

| Comparison | Pooled CPU product or weighted mean | Difference from Job 15 | Pooled factors | Sources |
|---|---:|---:|---|---|
| First ladder | 0.943557172 | -0.006654760 | 0.999888239 × 0.995710409 × 0.971396885 × 0.975634178 | [L1](sol2/job18/L1/summary.txt#L112-L129) · [L2](sol2/job18/L2/summary.txt#L112-L129) · [L3](sol2/job18/L3/summary.txt#L112-L129) · [L4](sol2/job18/L4/summary.txt#L112-L129) |
| Second ladder | 0.922651379 | -0.027560553 | 0.976770788 × 0.991189293 × 0.984610506 × 0.967885323 | [L1b](sol2/job19/L1b/summary.txt#L112-L129) · [L2b](sol2/job19/L2b/summary.txt#L112-L129) · [L3b](sol2/job19/L3b/summary.txt#L112-L129) · [L4b](sol2/job19/L4b/summary.txt#L112-L129) |
| Job 15 weighted one-engine r15d-to-kF CPU mean | 0.950211932 (0.9502 rounded) | — | — | [U40](sol2/job15/U40/summary.txt#L112-L129) · [U56](sol2/job15/U56/summary.txt#L112-L129) · [U72](sol2/job15/U72/summary.txt#L112-L129) · [U88](sol2/job15/U88/summary.txt#L112-L129) |

Each ladder product multiplies its four pooled CPU B/A ratios. Differences from the Job 15 reference are descriptive.

### L1b

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9303 | 0.9285 |
| 2 | BAAB | 1.0313 | 1.0316 |
| 3 | ABBA | 0.9536 | 0.9538 |
| 4 | BAAB | 0.9962 | 0.9955 |
| 5 | ABBA | 0.9981 | 0.9983 |
| 6 | BAAB | 0.9883 | 0.9874 |
| 7 | ABBA | 0.9832 | 0.9854 |
| 8 | BAAB | 0.9802 | 0.9798 |
| 9 | ABBA | 0.9392 | 0.9379 |
| 10 | BAAB | 0.9740 | 0.9716 |
| 11 | ABBA | 0.9717 | 0.9690 |
| 12 | BAAB | 0.9952 | 0.9974 |
| 13 | ABBA | 0.9760 | 0.9746 |
| 14 | BAAB | 0.9694 | 0.9684 |
| 15 | ABBA | 0.9703 | 0.9693 |
| 16 | BAAB | 0.9815 | 0.9806 |

[Inputs](sol2/job19/L1b/inputs.txt) · [Raw runs](sol2/job19/L1b/runs.jsonl.txt) · [Summary](sol2/job19/L1b/summary.txt) · [Command](sol2/job19/L1b-command.raw.txt)

### L2b

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9578 | 0.9585 |
| 2 | BAAB | 1.0358 | 1.0393 |
| 3 | ABBA | 1.0156 | 1.0176 |
| 4 | BAAB | 1.0132 | 1.0174 |
| 5 | ABBA | 1.0494 | 1.0525 |
| 6 | BAAB | 1.0212 | 1.0227 |
| 7 | ABBA | 0.9737 | 0.9757 |
| 8 | BAAB | 0.9368 | 0.9380 |
| 9 | ABBA | 0.9755 | 0.9771 |
| 10 | BAAB | 1.0087 | 1.0105 |
| 11 | ABBA | 0.9763 | 0.9760 |
| 12 | BAAB | 0.9643 | 0.9639 |
| 13 | ABBA | 0.9713 | 0.9709 |
| 14 | BAAB | 1.0154 | 1.0184 |
| 15 | ABBA | 0.9967 | 0.9964 |
| 16 | BAAB | 0.9537 | 0.9545 |

[Inputs](sol2/job19/L2b/inputs.txt) · [Raw runs](sol2/job19/L2b/runs.jsonl.txt) · [Summary](sol2/job19/L2b/summary.txt) · [Command](sol2/job19/L2b-command.raw.txt)

### L3b

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9562 | 0.9563 |
| 2 | BAAB | 0.9406 | 0.9403 |
| 3 | ABBA | 1.0150 | 1.0198 |
| 4 | BAAB | 0.9758 | 0.9791 |
| 5 | ABBA | 1.0200 | 1.0245 |
| 6 | BAAB | 0.9480 | 0.9487 |
| 7 | ABBA | 1.0013 | 1.0033 |
| 8 | BAAB | 0.9749 | 0.9744 |
| 9 | ABBA | 0.9587 | 0.9613 |
| 10 | BAAB | 1.0451 | 1.0495 |
| 11 | ABBA | 0.9783 | 0.9779 |
| 12 | BAAB | 1.0315 | 1.0339 |
| 13 | ABBA | 0.9967 | 0.9980 |
| 14 | BAAB | 0.9916 | 0.9953 |
| 15 | ABBA | 0.9675 | 0.9685 |
| 16 | BAAB | 0.9615 | 0.9617 |

[Inputs](sol2/job19/L3b/inputs.txt) · [Raw runs](sol2/job19/L3b/runs.jsonl.txt) · [Summary](sol2/job19/L3b/summary.txt) · [Command](sol2/job19/L3b-command.raw.txt)

### L4b

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9806 | 0.9837 |
| 2 | BAAB | 0.9445 | 0.9455 |
| 3 | ABBA | 1.0068 | 1.0075 |
| 4 | BAAB | 0.9190 | 0.9230 |
| 5 | ABBA | 0.9391 | 0.9428 |
| 6 | BAAB | 0.9274 | 0.9291 |
| 7 | ABBA | 1.0279 | 1.0322 |
| 8 | BAAB | 0.9290 | 0.9286 |
| 9 | ABBA | 0.9886 | 0.9908 |
| 10 | BAAB | 0.9673 | 0.9691 |
| 11 | ABBA | 0.9781 | 0.9793 |
| 12 | BAAB | 0.9519 | 0.9558 |
| 13 | ABBA | 0.9898 | 0.9941 |
| 14 | BAAB | 0.9855 | 0.9896 |
| 15 | ABBA | 0.9965 | 1.0016 |
| 16 | BAAB | 0.9664 | 0.9691 |

[Inputs](sol2/job19/L4b/inputs.txt) · [Raw runs](sol2/job19/L4b/runs.jsonl.txt) · [Summary](sol2/job19/L4b/summary.txt) · [Command](sol2/job19/L4b-command.raw.txt)

## Facts

The 4 complete comparisons contain 256 timed runs and 64 warm-ups. The independent readback verifies each W signature and recomputes ratios from the receipts. [Independent readback](sol2/job19/timing_readback.py.txt) Procfs verified 320 of 320 complete raw run records. [Launch arms](sol2/job19/arms.txt)

## Suspicions

Pieces that change a shared hot path may interact. Each measured ratio reflects the pieces added in the context of the preceding prefix. [Build identities](sol2/job19/builds.txt)

## What this check cannot see

> The PC's Windows loader, its clang 23, its Zen 5 processor with 16 engines at once, its trained net (net768 is
synthetic), its own self-play openings; two builds per prefix are still few (two builds of one source differed by up
to 1.5 % on the PC).

## What I did not do

The comparisons used the two prefix builds, the fixed W workload and one pinned cloud worker. Patch application was confined to fresh scratch source copies. [Publication layout](sol2/job19/publication-layout.raw.txt)

## What I am not sure about

The contribution of individual pieces within each increment remains unresolved. Each interval covers repeated measurements of its build pair. W records moves and last-info node counts in its trace and verifies final soft-node counts in aggregate.
