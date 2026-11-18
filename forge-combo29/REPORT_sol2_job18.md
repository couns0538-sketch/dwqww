# sol2 — Job 18 kF prefix ladder

## Step 0 — machine and frozen identities

Debian Clang 19.1.7 was verified on the same cloud VM with an AMD EPYC 9V74, five logical CPUs on five guest cores, shared 32 MiB L3 and four CPU equivalents in the cgroup. The replay driver and engine use logical CPU 2. Frozen r15d and K_1 matched their Job 16 SHA-256 values and passed fresh W replays at their existing 72-character paths using the fixed launch environment. [Machine and gate receipts](sol2/job18/step0-command.raw.txt) · [Frozen hashes](sol2/job18/clang-executables.raw.txt) · [Workload pins](sol2/job18/workload-pins.raw.txt)

Both Step 0 builds match W with 20 games, 2,247 searches, 7,905,938 last-info nodes, 9,189,426 final nodes and trace `7f78d3aec021ab01`. W uses PC20, Threads 1, Hash 16 MiB, net768 and `go softnodes 2000` on book lines 7001–7020. [r15d](sol2/job18/step0/r15d.result.raw.txt#L2-L6) · [K_1](sol2/job18/step0/kF.result.raw.txt#L2-L6) · [W signature](sol2/job18/known-answer.txt#L2-L6)

## Step 1 — prefix builds and launch arms

The three source copies apply the recorded carbon2 stack in its original order. P4 stops after piece 04, P8 after piece 08 and P10 after piece 10. Each prefix used the same Clang self-play profile recipe as Job 16. Every default pin used a fresh process with no UCI options. Each W entry links to a separate fresh process's games, searches, last-info nodes, final nodes and trace.

| Build | SHA-256 | bench 11 nodes | bench 13 nodes | go perft 5 nodes | W games / searches / last-info / final / trace | Timing gate |
|---|---|---:|---:|---:|---|---|
| r15d | [`540e63c0b7cf2512f1716657aded48b0558022b49c0fe8489596195cf2035834`](sol2/job18/clang-executables.raw.txt#L1) | [312,866](sol2/job13/r15d-default.raw.txt#L7) | [862,329](sol2/job13/r15d-default.raw.txt#L14) | [4,865,609](sol2/job13/r15d-default.raw.txt#L42) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job18/step0/r15d.result.raw.txt#L2-L6) | Pass |
| K_1 | [`da5df215a6aa255261d4e5574474da7c82aad1a9e95df83e15d5b38963ef439d`](sol2/job18/clang-executables.raw.txt#L2) | [312,866](sol2/job13/kF-default.raw.txt#L7) | [862,329](sol2/job13/kF-default.raw.txt#L14) | [4,865,609](sol2/job13/kF-default.raw.txt#L42) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job18/step0/kF.result.raw.txt#L2-L6) | Pass |
| P4 | [`791a4fc172886cb28c5648c0d7a808d23814786bd67e340c3cb8b242a8df4573`](sol2/job18/step1-P4/clang-sha256.raw.txt#L1) | [312,866](sol2/job18/build-checks/P4/default-pins.raw.txt#L7) | [862,329](sol2/job18/build-checks/P4/default-pins.raw.txt#L14) | [4,865,609](sol2/job18/build-checks/P4/default-pins.raw.txt#L42) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job18/build-checks/P4/W.result.raw.txt#L2-L6) | Pass |
| P8 | [`7b2c2b2a4807680d4d17ca3e32f037ada215edc9cdf251d2c4d4060a6a637c1d`](sol2/job18/step1-P8/clang-sha256.raw.txt#L1) | [312,866](sol2/job18/build-checks/P8/default-pins.raw.txt#L7) | [862,329](sol2/job18/build-checks/P8/default-pins.raw.txt#L14) | [4,865,609](sol2/job18/build-checks/P8/default-pins.raw.txt#L42) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job18/build-checks/P8/W.result.raw.txt#L2-L6) | Pass |
| P10 | [`dee47b3cd9135abb2c52eb58a741c0e7d65875e08d525c1438d72f1f88a390ad`](sol2/job18/step1-P10/clang-sha256.raw.txt#L1) | [312,866](sol2/job18/build-checks/P10/default-pins.raw.txt#L7) | [862,329](sol2/job18/build-checks/P10/default-pins.raw.txt#L14) | [4,865,609](sol2/job18/build-checks/P10/default-pins.raw.txt#L42) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job18/build-checks/P10/W.result.raw.txt#L2-L6) | Pass |

[Build identities and gate status](sol2/job18/builds.txt)
[Stack patch provenance and SHA-256](sol2/job18/prefix-patch-provenance.raw.txt)
The full-stack replay reproduced the known kF source hashes. [Full-stack source verification](sol2/job18/prefix-source/full-kF-proof.git-apply.raw.txt#L350)
[P4 gates](sol2/job18/build-checks/P4/checks.raw.txt) · [P4 build commands](sol2/job18/step1-P4/commands.raw.txt)
[P8 gates](sol2/job18/build-checks/P8/checks.raw.txt) · [P8 build commands](sol2/job18/step1-P8/commands.raw.txt)
[P10 gates](sol2/job18/build-checks/P10/checks.raw.txt) · [P10 build commands](sol2/job18/step1-P10/commands.raw.txt)

### P4 patch commands

```sh
cd /workspace/work/sol2-job18/.P4.partial
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/04_S7.patch.txt
```

[P4 source receipt](sol2/job18/prefix-source/P4.git-apply.raw.txt#L34-L100) · [P4 source SHA-256 manifest](sol2/job18/prefix-source/P4-source-sha256.raw.txt)

### P8 patch commands

```sh
cd /workspace/work/sol2-job18/.P8.partial
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/05_G1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/05_G1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/05_G1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/06_G2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/06_G2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/06_G2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/07_G3.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/07_G3.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/07_G3.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/08_G4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/08_G4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/08_G4.patch.txt
```

[P8 source receipt](sol2/job18/prefix-source/P8.git-apply.raw.txt#L34-L182) · [P8 source SHA-256 manifest](sol2/job18/prefix-source/P8-source-sha256.raw.txt)

### P10 patch commands

```sh
cd /workspace/work/sol2-job18/.P10.partial
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/05_G1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/05_G1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/05_G1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/06_G2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/06_G2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/06_G2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/07_G3.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/07_G3.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/07_G3.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/08_G4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/08_G4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/08_G4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/09_W1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/09_W1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/09_W1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/10_W2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/10_W2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/10_W2.patch.txt
```

[P10 source receipt](sol2/job18/prefix-source/P10.git-apply.raw.txt#L34-L228) · [P10 source SHA-256 manifest](sol2/job18/prefix-source/P10-source-sha256.raw.txt)

### full-kF-proof patch commands

```sh
cd /workspace/work/sol2-job18/.full-kF-proof.partial
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/05_G1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/05_G1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/05_G1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/06_G2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/06_G2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/06_G2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/07_G3.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/07_G3.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/07_G3.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/08_G4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/08_G4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/08_G4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/09_W1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/09_W1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/09_W1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/10_W2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/10_W2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/10_W2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/11_stop_hot.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/11_stop_hot.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/11_stop_hot.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/12_v3_refresh_fuse.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/12_v3_refresh_fuse.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/12_v3_refresh_fuse.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/13_tt_avx512_fast_probe.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/13_tt_avx512_fast_probe.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/13_tt_avx512_fast_probe.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job18/patches/tidy.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job18/patches/tidy.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job18/patches/tidy.patch.txt
```

[full-kF-proof source receipt](sol2/job18/prefix-source/full-kF-proof.git-apply.raw.txt#L34-L310) · [full-kF-proof source SHA-256 manifest](sol2/job18/prefix-source/full-kF-proof-source-sha256.raw.txt)

| Arm | Engine argv[0] | Characters | Device | Inode | SHA-256 |
|---|---|---:|---:|---:|---|
| r15d | `/workspace/work/sol2-job16/arms/r15dxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 280450 | `540e63c0b7cf2512f1716657aded48b0558022b49c0fe8489596195cf2035834` |
| P4 | `/workspace/work/sol2-job18/arms/P4xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 287714 | `791a4fc172886cb28c5648c0d7a808d23814786bd67e340c3cb8b242a8df4573` |
| P8 | `/workspace/work/sol2-job18/arms/P8xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 287785 | `7b2c2b2a4807680d4d17ca3e32f037ada215edc9cdf251d2c4d4060a6a637c1d` |
| P10 | `/workspace/work/sol2-job18/arms/P10xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 287787 | `dee47b3cd9135abb2c52eb58a741c0e7d65875e08d525c1438d72f1f88a390ad` |
| K_1 | `/workspace/work/sol2-job16/arms/K_1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 280452 | `da5df215a6aa255261d4e5574474da7c82aad1a9e95df83e15d5b38963ef439d` |

Each engine receives `LC_ALL=C` and `TZ=UTC`, 16 bytes, SHA-256 `4d41c4c11fcc6efa3bd339441ec9b26e6a1442056205420dc4b11e93dbff2570`. [Arms](sol2/job18/arms.txt)

## Prediction graded

The prediction was committed alone at `453e1e8d8019ff64e813e80bfe2b8035cab1a081` after Step 1 and before L1.

| Comparison | Predicted CPU B/A | Observed pooled CPU B/A | Ratio in range | Expected reading | Observed reading | Reading met |
|---|---:|---:|---|---|---|---|
| L1 | 0.955–1.020 | 0.9999 | Yes | NOT SEEN | NOT SEEN | Yes |
| L2 | 0.940–1.015 | 0.9957 | Yes | PAYS | NOT SEEN | No |
| L3 | 0.960–1.035 | 0.9714 | Yes | NOT SEEN | PAYS | No |
| L4 | 0.945–1.025 | 0.9756 | Yes | NOT SEEN | PAYS | No |

[Original prediction](sol2/job18/prediction.txt) · [UTC checkpoints](sol2/job18/stamps.txt)

## Step 2 — timing comparisons

Every run started a fresh engine on logical CPU 2 with workload W and the fixed replacement environment. Each arm used a 72-character executable path. Odd blocks used ABBA and even blocks used BAAB. One recorded warm-up preceded each block, and only its four timed runs entered the ratio. A run outside the W signature gate excluded its block. Engine CPU is the reaped engine process's user plus system time. Wall is the full driver call interval. Each complete comparison reports B/A with a Student t interval from the 16 block ratios and 15 degrees of freedom. [Timing commands](sol2/job18/run_campaign.sh.txt) · [Independent readback](sol2/job18/timing_readback.py.txt)

| Comparison | A | B | Metric | Blocks | Median | Pooled B/A | Mean | 95% t interval, df 15 | Below 1 |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| L1 | r15d | P4 | Engine CPU | 16/16 | 1.0067 | 0.9999 | 1.0006 | [0.9758, 1.0255] | 8/16 |
| L1 | r15d | P4 | Wall | 16/16 | 1.0073 | 1.0006 | 1.0014 | [0.9758, 1.0271] | 8/16 |
| L2 | P4 | P8 | Engine CPU | 16/16 | 0.9920 | 0.9957 | 0.9975 | [0.9642, 1.0309] | 10/16 |
| L2 | P4 | P8 | Wall | 16/16 | 0.9914 | 0.9963 | 0.9982 | [0.9644, 1.0320] | 9/16 |
| L3 | P8 | P10 | Engine CPU | 16/16 | 0.9722 | 0.9714 | 0.9733 | [0.9476, 0.9990] | 11/16 |
| L3 | P8 | P10 | Wall | 16/16 | 0.9756 | 0.9721 | 0.9742 | [0.9478, 1.0006] | 11/16 |
| L4 | P10 | K_1 | Engine CPU | 16/16 | 0.9788 | 0.9756 | 0.9763 | [0.9574, 0.9951] | 11/16 |
| L4 | P10 | K_1 | Wall | 16/16 | 0.9798 | 0.9784 | 0.9790 | [0.9597, 0.9984] | 11/16 |

## Declared readings and arithmetic

| Step | Engine CPU reading | Wall interval, descriptive |
|---|---|---|
| L1 | NOT SEEN | Interval contains 1 |
| L2 | NOT SEEN | Interval contains 1 |
| L3 | PAYS | Interval contains 1 |
| L4 | PAYS | Interval wholly below 1 |

A step PAYS when its engine CPU t interval lies wholly below 1 and COSTS when it lies wholly above 1. A completed interval that contains 1 gives NOT SEEN.

The four pooled CPU ratios multiply to 0.943557172 (0.999888239 × 0.995710409 × 0.971396885 × 0.975634178). The Job 15 weighted one-engine r15d-to-kF mean was 0.950211932 (0.9502 rounded). The descriptive difference is -0.006654760. [L1](sol2/job18/L1/summary.txt#L112-L129) · [L2](sol2/job18/L2/summary.txt#L112-L129) · [L3](sol2/job18/L3/summary.txt#L112-L129) · [L4](sol2/job18/L4/summary.txt#L112-L129) · [U40](sol2/job15/U40/summary.txt#L112-L129) · [U56](sol2/job15/U56/summary.txt#L112-L129) · [U72](sol2/job15/U72/summary.txt#L112-L129) · [U88](sol2/job15/U88/summary.txt#L112-L129)

### L1

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9817 | 0.9811 |
| 2 | BAAB | 1.0308 | 1.0333 |
| 3 | ABBA | 1.0341 | 1.0374 |
| 4 | BAAB | 0.9958 | 0.9966 |
| 5 | ABBA | 1.0351 | 1.0404 |
| 6 | BAAB | 0.9368 | 0.9343 |
| 7 | ABBA | 0.9676 | 0.9657 |
| 8 | BAAB | 0.9040 | 0.9016 |
| 9 | ABBA | 0.9628 | 0.9651 |
| 10 | BAAB | 1.0223 | 1.0255 |
| 11 | ABBA | 1.0555 | 1.0552 |
| 12 | BAAB | 1.0707 | 1.0734 |
| 13 | ABBA | 1.0492 | 1.0497 |
| 14 | BAAB | 1.0176 | 1.0180 |
| 15 | ABBA | 0.9560 | 0.9551 |
| 16 | BAAB | 0.9903 | 0.9908 |

[Inputs](sol2/job18/L1/inputs.txt) · [Raw runs](sol2/job18/L1/runs.jsonl.txt) · [Summary](sol2/job18/L1/summary.txt) · [Command](sol2/job18/L1-command.raw.txt)

### L2

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9573 | 0.9577 |
| 2 | BAAB | 0.9857 | 0.9859 |
| 3 | ABBA | 0.9995 | 1.0020 |
| 4 | BAAB | 0.9904 | 0.9901 |
| 5 | ABBA | 1.0139 | 1.0187 |
| 6 | BAAB | 1.0381 | 1.0379 |
| 7 | ABBA | 0.9936 | 0.9927 |
| 8 | BAAB | 0.9129 | 0.9134 |
| 9 | ABBA | 0.9880 | 0.9879 |
| 10 | BAAB | 1.0191 | 1.0242 |
| 11 | ABBA | 0.9830 | 0.9826 |
| 12 | BAAB | 1.0513 | 1.0531 |
| 13 | ABBA | 1.1721 | 1.1716 |
| 14 | BAAB | 1.0112 | 1.0130 |
| 15 | ABBA | 0.9547 | 0.9569 |
| 16 | BAAB | 0.8896 | 0.8837 |

[Inputs](sol2/job18/L2/inputs.txt) · [Raw runs](sol2/job18/L2/runs.jsonl.txt) · [Summary](sol2/job18/L2/summary.txt) · [Command](sol2/job18/L2-command.raw.txt)

### L3

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9811 | 0.9839 |
| 2 | BAAB | 0.9501 | 0.9493 |
| 3 | ABBA | 0.9375 | 0.9358 |
| 4 | BAAB | 1.0650 | 1.0679 |
| 5 | ABBA | 1.0101 | 1.0159 |
| 6 | BAAB | 1.0045 | 1.0078 |
| 7 | ABBA | 0.9523 | 0.9527 |
| 8 | BAAB | 0.9120 | 0.9115 |
| 9 | ABBA | 0.9985 | 0.9984 |
| 10 | BAAB | 0.9633 | 0.9673 |
| 11 | ABBA | 1.0015 | 1.0012 |
| 12 | BAAB | 0.9910 | 0.9932 |
| 13 | ABBA | 0.8991 | 0.8974 |
| 14 | BAAB | 0.9083 | 0.9070 |
| 15 | ABBA | 0.9484 | 0.9476 |
| 16 | BAAB | 1.0501 | 1.0499 |

[Inputs](sol2/job18/L3/inputs.txt) · [Raw runs](sol2/job18/L3/runs.jsonl.txt) · [Summary](sol2/job18/L3/summary.txt) · [Command](sol2/job18/L3-command.raw.txt)

### L4

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 1.0180 | 1.0230 |
| 2 | BAAB | 0.9543 | 0.9530 |
| 3 | ABBA | 1.0245 | 1.0291 |
| 4 | BAAB | 0.9789 | 0.9801 |
| 5 | ABBA | 0.9908 | 0.9965 |
| 6 | BAAB | 0.9170 | 0.9173 |
| 7 | ABBA | 0.9504 | 0.9539 |
| 8 | BAAB | 0.9499 | 0.9534 |
| 9 | ABBA | 0.9944 | 0.9975 |
| 10 | BAAB | 0.9669 | 0.9697 |
| 11 | ABBA | 0.9787 | 0.9796 |
| 12 | BAAB | 0.9204 | 0.9248 |
| 13 | ABBA | 0.9391 | 0.9401 |
| 14 | BAAB | 1.0011 | 1.0045 |
| 15 | ABBA | 1.0256 | 1.0299 |
| 16 | BAAB | 1.0103 | 1.0122 |

[Inputs](sol2/job18/L4/inputs.txt) · [Raw runs](sol2/job18/L4/runs.jsonl.txt) · [Summary](sol2/job18/L4/summary.txt) · [Command](sol2/job18/L4-command.raw.txt)

## Facts

The 4 complete comparisons contain 256 timed runs and 64 warm-ups. The independent readback verifies each W signature and recomputes ratios from the receipts. [Independent readback](sol2/job18/timing_readback.py.txt) Procfs verified 320 of 320 complete raw run records. [Launch arms](sol2/job18/arms.txt)

## Suspicions

Pieces that change a shared hot path may interact. Each measured ratio reflects the pieces added in the context of the preceding prefix. [Build identities](sol2/job18/builds.txt)

## What this check cannot see

> The PC's Windows loader, its clang 23, its Zen 5 processor with 16 engines at once, its trained net (net768 is
synthetic), its own self-play openings; one build per prefix (two builds of one source differed by up to 1.5 % on
the PC), so a step under about 1.5 % is not separated from build noise.

## What I did not do

The comparison used one build per prefix, the fixed W workload and one pinned cloud worker. Patch application was confined to scratch source copies. [Publication layout](sol2/job18/publication-layout.raw.txt)

## What I am not sure about

The contribution of each individual piece within a prefix step remains unresolved. W records moves and last-info node counts in its trace and verifies final soft-node counts in aggregate.
