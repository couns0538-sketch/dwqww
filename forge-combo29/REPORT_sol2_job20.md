# sol2 — Job 20 splitting the last two kF ladder steps

## Step 0 — machine and frozen identities

Debian Clang 19.1.7 was verified. The cloud VM reports AMD EPYC 9V74, five logical CPUs on five guest cores, shared 32 MiB L3 and four CPU equivalents in the cgroup. Each W replay uses one engine and its driver pinned to logical CPU 2. All six frozen engines matched the hashes from Jobs 16, 18 and 19 and independently passed W from their existing 72-character launch paths under the fixed environment. [Machine and gate receipts](sol2/job20/step0-command.raw.txt) · [Frozen hashes](sol2/job20/clang-executables.raw.txt) · [Reference launch arms](sol2/job20/reference-arms.txt)

All six Step 0 builds matched W with 20 games, 2,247 searches, 7,905,938 last-info nodes, 9,189,426 final nodes and trace `7f78d3aec021ab01`. W uses PC20, Threads 1, Hash 16 MiB, net768 and `go softnodes 2000` on book lines 7001–7020. [P8](sol2/job20/step0/P8.result.raw.txt#L2-L6) · [P10](sol2/job20/step0/P10.result.raw.txt#L2-L6) · [K_1](sol2/job20/step0/K_1.result.raw.txt#L2-L6) · [P8_2](sol2/job20/step0/P8_2.result.raw.txt#L2-L6) · [P10_2](sol2/job20/step0/P10_2.result.raw.txt#L2-L6) · [K_2](sol2/job20/step0/K_2.result.raw.txt#L2-L6) · [W signature](sol2/job20/known-answer.txt#L2-L6)

| Frozen build | SHA-256 | Fresh W games / searches / last-info / final / trace |
|---|---|---|
| P8 | [`7b2c2b2a4807680d4d17ca3e32f037ada215edc9cdf251d2c4d4060a6a637c1d`](sol2/job20/clang-executables.raw.txt#L1) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job20/step0/P8.result.raw.txt#L2-L6) |
| P10 | [`dee47b3cd9135abb2c52eb58a741c0e7d65875e08d525c1438d72f1f88a390ad`](sol2/job20/clang-executables.raw.txt#L2) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job20/step0/P10.result.raw.txt#L2-L6) |
| K_1 | [`da5df215a6aa255261d4e5574474da7c82aad1a9e95df83e15d5b38963ef439d`](sol2/job20/clang-executables.raw.txt#L3) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job20/step0/K_1.result.raw.txt#L2-L6) |
| P8_2 | [`04fc4c88cbe6841a0960eb194125725555ff11cc1fa4aac116668fe9cb937055`](sol2/job20/clang-executables.raw.txt#L4) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job20/step0/P8_2.result.raw.txt#L2-L6) |
| P10_2 | [`208b733ed56273edd1c607a86347e744588f4ea888076e7f3c51085d50e6d0fb`](sol2/job20/clang-executables.raw.txt#L5) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job20/step0/P10_2.result.raw.txt#L2-L6) |
| K_2 | [`2890d5b1cf4f332a87e572222d5a24ecdc014e0920a6ade776c4f22f3730187f`](sol2/job20/clang-executables.raw.txt#L6) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job20/step0/K_2.result.raw.txt#L2-L6) |

## Step 1 — four independently profiled builds and launch arms

Each build started from a fresh source copy and used its own profile run with the Clang recipe from Job 16. P9_1 and P9_2 apply pieces 01 through 09 in order. P12_1 and P12_2 apply pieces 01 through 12. The first builds and then the second builds ran sequentially before timing. Profiles, gate replays and timed engines each used CPU 2 in their respective phases. Every default pin used a fresh process with no UCI options. Each W entry links to a separate fresh process's games, searches, last-info nodes, final nodes and trace.

| Build | SHA-256 | bench 11 nodes | bench 13 nodes | go perft 5 nodes | W games / searches / last-info / final / trace | Timing gate |
|---|---|---:|---:|---:|---|---|
| P9_1 | [`77255518b6946b5c41aa458ea7b85f0c0c7194c3af8194d9420e6037c3df2846`](sol2/job20/step1-P9_1/clang-sha256.raw.txt#L1) | [312,866](sol2/job20/build-checks/P9_1/default-pins.raw.txt#L7) | [862,329](sol2/job20/build-checks/P9_1/default-pins.raw.txt#L14) | [4,865,609](sol2/job20/build-checks/P9_1/default-pins.raw.txt#L42) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job20/build-checks/P9_1/W.result.raw.txt#L2-L6) | Pass |
| P12_1 | [`0c9563efa7a1c28f8da5f902ae88c6d5cd0ee79af4c953d7981a4534fe671dbc`](sol2/job20/step1-P12_1/clang-sha256.raw.txt#L1) | [312,866](sol2/job20/build-checks/P12_1/default-pins.raw.txt#L7) | [862,329](sol2/job20/build-checks/P12_1/default-pins.raw.txt#L14) | [4,865,609](sol2/job20/build-checks/P12_1/default-pins.raw.txt#L42) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job20/build-checks/P12_1/W.result.raw.txt#L2-L6) | Pass |
| P9_2 | [`72f13e15e4cdb1bc4539d607dcb4c03cef175b3bcb851510ddadef35f7f7e4f6`](sol2/job20/step1-P9_2/clang-sha256.raw.txt#L1) | [312,866](sol2/job20/build-checks/P9_2/default-pins.raw.txt#L7) | [862,329](sol2/job20/build-checks/P9_2/default-pins.raw.txt#L14) | [4,865,609](sol2/job20/build-checks/P9_2/default-pins.raw.txt#L42) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job20/build-checks/P9_2/W.result.raw.txt#L2-L6) | Pass |
| P12_2 | [`e19f7d4cd3c480b32fb3c102d9c9b9f666d92b81b0227fd49608ecd28cd26f5e`](sol2/job20/step1-P12_2/clang-sha256.raw.txt#L1) | [312,866](sol2/job20/build-checks/P12_2/default-pins.raw.txt#L7) | [862,329](sol2/job20/build-checks/P12_2/default-pins.raw.txt#L14) | [4,865,609](sol2/job20/build-checks/P12_2/default-pins.raw.txt#L42) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job20/build-checks/P12_2/W.result.raw.txt#L2-L6) | Pass |

[Build identities and gate status](sol2/job20/builds.txt)
[Stack patch provenance and SHA-256](sol2/job20/prefix-patch-provenance.raw.txt) · [Resource schedule](sol2/job20/resource-schedule.raw.txt) · [Executable twin checks](sol2/job20/prefix-build-twins.raw.txt)
[P9_1 gates](sol2/job20/build-checks/P9_1/checks.raw.txt) · [P9_1 build commands](sol2/job20/step1-P9_1/commands.raw.txt)
[P12_1 gates](sol2/job20/build-checks/P12_1/checks.raw.txt) · [P12_1 build commands](sol2/job20/step1-P12_1/commands.raw.txt)
[P9_2 gates](sol2/job20/build-checks/P9_2/checks.raw.txt) · [P9_2 build commands](sol2/job20/step1-P9_2/commands.raw.txt)
[P12_2 gates](sol2/job20/build-checks/P12_2/checks.raw.txt) · [P12_2 build commands](sol2/job20/step1-P12_2/commands.raw.txt)

### P9_1 patch commands

```sh
cd /workspace/work/sol2-job20/.P9_1.partial
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/05_G1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/05_G1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/05_G1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/06_G2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/06_G2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/06_G2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/07_G3.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/07_G3.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/07_G3.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/08_G4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/08_G4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/08_G4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/09_W1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/09_W1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/09_W1.patch.txt
```

[P9_1 source receipt](sol2/job20/prefix-source/P9_1.git-apply.raw.txt#L34-L208) · [P9_1 source SHA-256 manifest](sol2/job20/prefix-source/P9_1-source-sha256.raw.txt)

### P12_1 patch commands

```sh
cd /workspace/work/sol2-job20/.P12_1.partial
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/05_G1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/05_G1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/05_G1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/06_G2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/06_G2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/06_G2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/07_G3.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/07_G3.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/07_G3.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/08_G4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/08_G4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/08_G4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/09_W1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/09_W1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/09_W1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/10_W2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/10_W2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/10_W2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/11_stop_hot.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/11_stop_hot.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/11_stop_hot.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/12_v3_refresh_fuse.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/12_v3_refresh_fuse.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/12_v3_refresh_fuse.patch.txt
```

[P12_1 source receipt](sol2/job20/prefix-source/P12_1.git-apply.raw.txt#L34-L270) · [P12_1 source SHA-256 manifest](sol2/job20/prefix-source/P12_1-source-sha256.raw.txt)

### P9_2 patch commands

```sh
cd /workspace/work/sol2-job20/.P9_2.partial
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/05_G1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/05_G1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/05_G1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/06_G2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/06_G2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/06_G2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/07_G3.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/07_G3.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/07_G3.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/08_G4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/08_G4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/08_G4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/09_W1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/09_W1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/09_W1.patch.txt
```

[P9_2 source receipt](sol2/job20/prefix-source/P9_2.git-apply.raw.txt#L34-L208) · [P9_2 source SHA-256 manifest](sol2/job20/prefix-source/P9_2-source-sha256.raw.txt) · [29 files match P9_1](sol2/job20/prefix-source/P9_2.git-apply.raw.txt#L281)

### P12_2 patch commands

```sh
cd /workspace/work/sol2-job20/.P12_2.partial
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/01_S4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/02_S5.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/03_S5_assert.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/05_G1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/05_G1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/05_G1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/06_G2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/06_G2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/06_G2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/07_G3.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/07_G3.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/07_G3.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/08_G4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/08_G4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/08_G4.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/09_W1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/09_W1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/09_W1.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/10_W2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/10_W2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/10_W2.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/11_stop_hot.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/11_stop_hot.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/11_stop_hot.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job20/patches/12_v3_refresh_fuse.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job20/patches/12_v3_refresh_fuse.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job20/patches/12_v3_refresh_fuse.patch.txt
```

[P12_2 source receipt](sol2/job20/prefix-source/P12_2.git-apply.raw.txt#L34-L270) · [P12_2 source SHA-256 manifest](sol2/job20/prefix-source/P12_2-source-sha256.raw.txt) · [29 files match P12_1](sol2/job20/prefix-source/P12_2.git-apply.raw.txt#L343)

| Arm | Engine argv[0] | Characters | Device | Inode | SHA-256 |
|---|---|---:|---:|---:|---|
| P8 | `/workspace/work/sol2-job18/arms/P8xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 287785 | `7b2c2b2a4807680d4d17ca3e32f037ada215edc9cdf251d2c4d4060a6a637c1d` |
| P9_1 | `/workspace/work/sol2-job20/arms/P9_1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 291374 | `77255518b6946b5c41aa458ea7b85f0c0c7194c3af8194d9420e6037c3df2846` |
| P10 | `/workspace/work/sol2-job18/arms/P10xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 287787 | `dee47b3cd9135abb2c52eb58a741c0e7d65875e08d525c1438d72f1f88a390ad` |
| P12_1 | `/workspace/work/sol2-job20/arms/P12_1xxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 291376 | `0c9563efa7a1c28f8da5f902ae88c6d5cd0ee79af4c953d7981a4534fe671dbc` |
| K_1 | `/workspace/work/sol2-job16/arms/K_1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 280452 | `da5df215a6aa255261d4e5574474da7c82aad1a9e95df83e15d5b38963ef439d` |
| P8_2 | `/workspace/work/sol2-job19/arms/P8_2xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 289521 | `04fc4c88cbe6841a0960eb194125725555ff11cc1fa4aac116668fe9cb937055` |
| P9_2 | `/workspace/work/sol2-job20/arms/P9_2xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 291378 | `72f13e15e4cdb1bc4539d607dcb4c03cef175b3bcb851510ddadef35f7f7e4f6` |
| P10_2 | `/workspace/work/sol2-job19/arms/P10_2xxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 289523 | `208b733ed56273edd1c607a86347e744588f4ea888076e7f3c51085d50e6d0fb` |
| P12_2 | `/workspace/work/sol2-job20/arms/P12_2xxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 291380 | `e19f7d4cd3c480b32fb3c102d9c9b9f666d92b81b0227fd49608ecd28cd26f5e` |
| K_2 | `/workspace/work/sol2-job16/arms/K_2xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 280458 | `2890d5b1cf4f332a87e572222d5a24ecdc014e0920a6ade776c4f22f3730187f` |

Each engine receives `LC_ALL=C` and `TZ=UTC`, 16 bytes, SHA-256 `4d41c4c11fcc6efa3bd339441ec9b26e6a1442056205420dc4b11e93dbff2570`. [Arms](sol2/job20/arms.txt)

## Prediction graded

The prediction was committed alone at `5f94d279b43ac66df762ab09df7989dd7b9c8c96` after the first two builds and before S1.

| Comparison | Predicted CPU B/A | Observed pooled CPU B/A | Ratio in range | Expected joint reading | Observed joint reading | Reading met |
|---|---:|---:|---|---|---|---|
| S1 | 0.955–1.025 | 0.9853 | Yes | NOT SEEN | NOT SEEN | Yes |
| S2 | 0.955–1.025 | 1.0015 | Yes | NOT SEEN | NOT SEEN | Yes |
| S3 | 0.940–1.015 | 1.0014 | Yes | PAYS | NOT SEEN | No |
| S4 | 0.965–1.025 | 0.9952 | Yes | NOT SEEN | NOT SEEN | Yes |
| S1b | 0.955–1.025 | 0.9899 | Yes | NOT SEEN | NOT SEEN | Yes |
| S2b | 0.955–1.025 | 1.0033 | Yes | NOT SEEN | NOT SEEN | Yes |
| S3b | 0.940–1.015 | 0.9940 | Yes | PAYS | NOT SEEN | No |
| S4b | 0.965–1.025 | 0.9907 | Yes | NOT SEEN | NOT SEEN | Yes |

[Original prediction](sol2/job20/prediction.txt) · [UTC checkpoints](sol2/job20/stamps.txt)

## Step 2 — timing comparisons

Every run started a fresh engine on logical CPU 2 with workload W and the fixed replacement environment. Each arm used a 72-character executable path. Odd blocks used ABBA and even blocks used BAAB. One recorded warm-up preceded each block, and only its four timed runs entered the ratio. A run outside the W signature gate excluded its block. Engine CPU is the reaped engine process's user plus system time. Wall is the full driver call interval. Each complete comparison reports B/A with a Student t interval from the 16 block ratios and 15 degrees of freedom. [Timing commands](sol2/job20/run_campaign.sh.txt) · [Independent readback](sol2/job20/timing_readback.py.txt)

| Comparison | A | B | Metric | Blocks | Median | Pooled B/A | Mean | 95% t interval, df 15 | Below 1 |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| S1 | P8 | P9_1 | Engine CPU | 16/16 | 0.9869 | 0.9853 | 0.9864 | [0.9604, 1.0125] | 11/16 |
| S1 | P8 | P9_1 | Wall | 16/16 | 0.9875 | 0.9861 | 0.9873 | [0.9606, 1.0141] | 11/16 |
| S2 | P9_1 | P10 | Engine CPU | 16/16 | 1.0049 | 1.0015 | 1.0022 | [0.9853, 1.0192] | 8/16 |
| S2 | P9_1 | P10 | Wall | 16/16 | 1.0055 | 1.0023 | 1.0030 | [0.9859, 1.0202] | 8/16 |
| S3 | P10 | P12_1 | Engine CPU | 16/16 | 0.9984 | 1.0014 | 1.0016 | [0.9882, 1.0151] | 8/16 |
| S3 | P10 | P12_1 | Wall | 16/16 | 0.9990 | 1.0026 | 1.0028 | [0.9894, 1.0162] | 8/16 |
| S4 | P12_1 | K_1 | Engine CPU | 16/16 | 0.9779 | 0.9952 | 0.9971 | [0.9477, 1.0465] | 12/16 |
| S4 | P12_1 | K_1 | Wall | 16/16 | 0.9781 | 0.9975 | 0.9995 | [0.9487, 1.0502] | 11/16 |
| S1b | P8_2 | P9_2 | Engine CPU | 16/16 | 1.0044 | 0.9899 | 0.9910 | [0.9655, 1.0165] | 8/16 |
| S1b | P8_2 | P9_2 | Wall | 16/16 | 1.0052 | 0.9902 | 0.9912 | [0.9656, 1.0168] | 8/16 |
| S2b | P9_2 | P10_2 | Engine CPU | 16/16 | 1.0008 | 1.0033 | 1.0039 | [0.9892, 1.0186] | 8/16 |
| S2b | P9_2 | P10_2 | Wall | 16/16 | 1.0031 | 1.0049 | 1.0055 | [0.9908, 1.0202] | 8/16 |
| S3b | P10_2 | P12_2 | Engine CPU | 16/16 | 0.9972 | 0.9940 | 0.9950 | [0.9707, 1.0193] | 8/16 |
| S3b | P10_2 | P12_2 | Wall | 16/16 | 0.9982 | 0.9943 | 0.9954 | [0.9701, 1.0206] | 8/16 |
| S4b | P12_2 | K_2 | Engine CPU | 16/16 | 0.9916 | 0.9907 | 0.9906 | [0.9777, 1.0035] | 11/16 |
| S4b | P12_2 | K_2 | Wall | 16/16 | 0.9957 | 0.9928 | 0.9927 | [0.9796, 1.0057] | 12/16 |

## Declared readings and arithmetic

Each step shows the pooled B/A ratio, the arithmetic mean and its 95% t interval. The joint reading uses CPU.

| Piece | First → second build | First CPU | Second CPU | First wall | Second wall | Joint CPU reading or available interval |
|---|---|---:|---:|---:|---:|---|
| 09 | [S1](sol2/job20/S1/summary.txt#L112-L146) → [S1b](sol2/job20/S1b/summary.txt#L112-L146) | 0.9853 / 0.9864 [0.9604, 1.0125] | 0.9899 / 0.9910 [0.9655, 1.0165] | 0.9861 / 0.9873 [0.9606, 1.0141] | 0.9902 / 0.9912 [0.9656, 1.0168] | NOT SEEN |
| 10 | [S2](sol2/job20/S2/summary.txt#L112-L146) → [S2b](sol2/job20/S2b/summary.txt#L112-L146) | 1.0015 / 1.0022 [0.9853, 1.0192] | 1.0033 / 1.0039 [0.9892, 1.0186] | 1.0023 / 1.0030 [0.9859, 1.0202] | 1.0049 / 1.0055 [0.9908, 1.0202] | NOT SEEN |
| 11 and 12 | [S3](sol2/job20/S3/summary.txt#L112-L146) → [S3b](sol2/job20/S3b/summary.txt#L112-L146) | 1.0014 / 1.0016 [0.9882, 1.0151] | 0.9940 / 0.9950 [0.9707, 1.0193] | 1.0026 / 1.0028 [0.9894, 1.0162] | 0.9943 / 0.9954 [0.9701, 1.0206] | NOT SEEN |
| 13 and tidy | [S4](sol2/job20/S4/summary.txt#L112-L146) → [S4b](sol2/job20/S4b/summary.txt#L112-L146) | 0.9952 / 0.9971 [0.9477, 1.0465] | 0.9907 / 0.9906 [0.9777, 1.0035] | 0.9975 / 0.9995 [0.9487, 1.0502] | 0.9928 / 0.9927 [0.9796, 1.0057] | NOT SEEN |

A step PAYS when both CPU intervals lie wholly below 1 and COSTS when both lie wholly above 1. Other complete pairs give NOT SEEN. Wall intervals are descriptive.

| Build | Split comparisons | Metric | Pooled factors | Product | Earlier pooled ratio | Product minus earlier | Sources |
|---|---|---|---|---:|---:|---:|---|
| First | S1 × S2 | Engine CPU | 0.985317479 × 1.001496123 | 0.986791635 | 0.971396885 | +0.015394749 | [S1](sol2/job20/S1/summary.txt#L112-L146) · [S2](sol2/job20/S2/summary.txt#L112-L146) · [L3](sol2/job18/L3/summary.txt#L112-L146) |
| First | S1 × S2 | Wall | 0.986130661 × 1.002275734 | 0.988374832 | 0.972146930 | +0.016227902 | [S1](sol2/job20/S1/summary.txt#L112-L146) · [S2](sol2/job20/S2/summary.txt#L112-L146) · [L3](sol2/job18/L3/summary.txt#L112-L146) |
| First | S3 × S4 | Engine CPU | 1.001390885 × 0.995247581 | 0.996631856 | 0.975634178 | +0.020997678 | [S3](sol2/job20/S3/summary.txt#L112-L146) · [S4](sol2/job20/S4/summary.txt#L112-L146) · [L4](sol2/job18/L4/summary.txt#L112-L146) |
| First | S3 × S4 | Wall | 1.002588698 × 0.997524568 | 1.000106858 | 0.978374565 | +0.021732293 | [S3](sol2/job20/S3/summary.txt#L112-L146) · [S4](sol2/job20/S4/summary.txt#L112-L146) · [L4](sol2/job18/L4/summary.txt#L112-L146) |
| Second | S1b × S2b | Engine CPU | 0.989900661 × 1.003313647 | 0.993180842 | 0.984610506 | +0.008570336 | [S1b](sol2/job20/S1b/summary.txt#L112-L146) · [S2b](sol2/job20/S2b/summary.txt#L112-L146) · [L3b](sol2/job19/L3b/summary.txt#L112-L146) |
| Second | S1b × S2b | Wall | 0.990177767 × 1.004901737 | 0.995031358 | 0.986427702 | +0.008603657 | [S1b](sol2/job20/S1b/summary.txt#L112-L146) · [S2b](sol2/job20/S2b/summary.txt#L112-L146) · [L3b](sol2/job19/L3b/summary.txt#L112-L146) |
| Second | S3b × S4b | Engine CPU | 0.994042785 × 0.990695691 | 0.984793904 | 0.967885323 | +0.016908580 | [S3b](sol2/job20/S3b/summary.txt#L112-L146) · [S4b](sol2/job20/S4b/summary.txt#L112-L146) · [L4b](sol2/job19/L4b/summary.txt#L112-L146) |
| Second | S3b × S4b | Wall | 0.994317129 × 0.992794142 | 0.987152221 | 0.970574080 | +0.016578141 | [S3b](sol2/job20/S3b/summary.txt#L112-L146) · [S4b](sol2/job20/S4b/summary.txt#L112-L146) · [L4b](sol2/job19/L4b/summary.txt#L112-L146) |

Each product uses the two completed split comparisons. Differences from the earlier ladder ratios are descriptive.

### S1

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 1.0267 | 1.0279 |
| 2 | BAAB | 1.0880 | 1.0916 |
| 3 | ABBA | 0.9589 | 0.9608 |
| 4 | BAAB | 0.9905 | 0.9912 |
| 5 | ABBA | 0.9967 | 0.9947 |
| 6 | BAAB | 0.9797 | 0.9817 |
| 7 | ABBA | 0.9529 | 0.9561 |
| 8 | BAAB | 0.9833 | 0.9838 |
| 9 | ABBA | 0.9266 | 0.9255 |
| 10 | BAAB | 0.9957 | 0.9949 |
| 11 | ABBA | 0.9001 | 0.8973 |
| 12 | BAAB | 0.9478 | 0.9503 |
| 13 | ABBA | 0.9500 | 0.9497 |
| 14 | BAAB | 1.0694 | 1.0764 |
| 15 | ABBA | 1.0095 | 1.0103 |
| 16 | BAAB | 1.0073 | 1.0053 |

[Inputs](sol2/job20/S1/inputs.txt) · [Raw runs](sol2/job20/S1/runs.jsonl.txt) · [Summary](sol2/job20/S1/summary.txt) · [Command](sol2/job20/S1-command.raw.txt)

### S2

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9697 | 0.9695 |
| 2 | BAAB | 0.9634 | 0.9652 |
| 3 | ABBA | 0.9443 | 0.9446 |
| 4 | BAAB | 1.0491 | 1.0493 |
| 5 | ABBA | 0.9969 | 0.9945 |
| 6 | BAAB | 0.9717 | 0.9715 |
| 7 | ABBA | 1.0308 | 1.0317 |
| 8 | BAAB | 1.0244 | 1.0278 |
| 9 | ABBA | 0.9964 | 0.9990 |
| 10 | BAAB | 0.9678 | 0.9687 |
| 11 | ABBA | 1.0163 | 1.0193 |
| 12 | BAAB | 1.0476 | 1.0505 |
| 13 | ABBA | 0.9944 | 0.9954 |
| 14 | BAAB | 1.0128 | 1.0121 |
| 15 | ABBA | 1.0177 | 1.0158 |
| 16 | BAAB | 1.0321 | 1.0340 |

[Inputs](sol2/job20/S2/inputs.txt) · [Raw runs](sol2/job20/S2/runs.jsonl.txt) · [Summary](sol2/job20/S2/summary.txt) · [Command](sol2/job20/S2-command.raw.txt)

### S3

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 1.0664 | 1.0691 |
| 2 | BAAB | 1.0080 | 1.0082 |
| 3 | ABBA | 0.9713 | 0.9726 |
| 4 | BAAB | 1.0017 | 1.0015 |
| 5 | ABBA | 0.9697 | 0.9750 |
| 6 | BAAB | 0.9900 | 0.9879 |
| 7 | ABBA | 1.0144 | 1.0149 |
| 8 | BAAB | 0.9777 | 0.9815 |
| 9 | ABBA | 0.9828 | 0.9841 |
| 10 | BAAB | 1.0347 | 1.0346 |
| 11 | ABBA | 0.9838 | 0.9822 |
| 12 | BAAB | 0.9894 | 0.9912 |
| 13 | ABBA | 1.0128 | 1.0147 |
| 14 | BAAB | 1.0061 | 1.0072 |
| 15 | ABBA | 0.9951 | 0.9965 |
| 16 | BAAB | 1.0223 | 1.0238 |

[Inputs](sol2/job20/S3/inputs.txt) · [Raw runs](sol2/job20/S3/runs.jsonl.txt) · [Summary](sol2/job20/S3/summary.txt) · [Command](sol2/job20/S3-command.raw.txt)

### S4

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9794 | 0.9784 |
| 2 | BAAB | 0.9516 | 0.9503 |
| 3 | ABBA | 0.9992 | 1.0012 |
| 4 | BAAB | 0.9653 | 0.9657 |
| 5 | ABBA | 1.0125 | 1.0149 |
| 6 | BAAB | 0.9300 | 0.9329 |
| 7 | ABBA | 0.9765 | 0.9779 |
| 8 | BAAB | 1.0250 | 1.0302 |
| 9 | ABBA | 0.9674 | 0.9699 |
| 10 | BAAB | 0.9929 | 0.9941 |
| 11 | ABBA | 0.9569 | 0.9583 |
| 12 | BAAB | 0.9067 | 0.9079 |
| 13 | ABBA | 0.9914 | 0.9960 |
| 14 | BAAB | 1.0125 | 1.0159 |
| 15 | ABBA | 1.3246 | 1.3359 |
| 16 | BAAB | 0.9612 | 0.9619 |

[Inputs](sol2/job20/S4/inputs.txt) · [Raw runs](sol2/job20/S4/runs.jsonl.txt) · [Summary](sol2/job20/S4/summary.txt) · [Command](sol2/job20/S4-command.raw.txt)

### S1b

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.8788 | 0.8790 |
| 2 | BAAB | 0.9810 | 0.9817 |
| 3 | ABBA | 0.9485 | 0.9481 |
| 4 | BAAB | 1.0271 | 1.0257 |
| 5 | ABBA | 1.0554 | 1.0586 |
| 6 | BAAB | 0.9806 | 0.9811 |
| 7 | ABBA | 1.0197 | 1.0181 |
| 8 | BAAB | 0.9633 | 0.9637 |
| 9 | ABBA | 1.0460 | 1.0439 |
| 10 | BAAB | 1.0179 | 1.0190 |
| 11 | ABBA | 0.9603 | 0.9615 |
| 12 | BAAB | 1.0301 | 1.0324 |
| 13 | ABBA | 0.9190 | 0.9179 |
| 14 | BAAB | 0.9976 | 0.9970 |
| 15 | ABBA | 1.0111 | 1.0134 |
| 16 | BAAB | 1.0192 | 1.0186 |

[Inputs](sol2/job20/S1b/inputs.txt) · [Raw runs](sol2/job20/S1b/runs.jsonl.txt) · [Summary](sol2/job20/S1b/summary.txt) · [Command](sol2/job20/S1b-command.raw.txt)

### S2b

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 1.0294 | 1.0326 |
| 2 | BAAB | 0.9960 | 0.9984 |
| 3 | ABBA | 0.9708 | 0.9717 |
| 4 | BAAB | 1.0241 | 1.0280 |
| 5 | ABBA | 1.0135 | 1.0095 |
| 6 | BAAB | 1.0075 | 1.0075 |
| 7 | ABBA | 1.0355 | 1.0377 |
| 8 | BAAB | 0.9775 | 0.9797 |
| 9 | ABBA | 1.0033 | 1.0062 |
| 10 | BAAB | 0.9847 | 0.9857 |
| 11 | ABBA | 0.9458 | 0.9474 |
| 12 | BAAB | 0.9944 | 0.9972 |
| 13 | ABBA | 0.9931 | 0.9952 |
| 14 | BAAB | 1.0362 | 1.0378 |
| 15 | ABBA | 1.0524 | 1.0532 |
| 16 | BAAB | 0.9982 | 0.9999 |

[Inputs](sol2/job20/S2b/inputs.txt) · [Raw runs](sol2/job20/S2b/runs.jsonl.txt) · [Summary](sol2/job20/S2b/summary.txt) · [Command](sol2/job20/S2b-command.raw.txt)

### S3b

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9736 | 0.9732 |
| 2 | BAAB | 1.0608 | 1.0619 |
| 3 | ABBA | 0.9014 | 0.8994 |
| 4 | BAAB | 1.0661 | 1.0673 |
| 5 | ABBA | 1.0156 | 1.0155 |
| 6 | BAAB | 1.0041 | 1.0029 |
| 7 | ABBA | 0.9618 | 0.9590 |
| 8 | BAAB | 1.0008 | 1.0018 |
| 9 | ABBA | 0.9927 | 0.9946 |
| 10 | BAAB | 0.9797 | 0.9816 |
| 11 | ABBA | 0.9936 | 0.9940 |
| 12 | BAAB | 0.9431 | 0.9403 |
| 13 | ABBA | 1.0678 | 1.0724 |
| 14 | BAAB | 1.0091 | 1.0133 |
| 15 | ABBA | 0.9451 | 0.9416 |
| 16 | BAAB | 1.0048 | 1.0071 |

[Inputs](sol2/job20/S3b/inputs.txt) · [Raw runs](sol2/job20/S3b/runs.jsonl.txt) · [Summary](sol2/job20/S3b/summary.txt) · [Command](sol2/job20/S3b-command.raw.txt)

### S4b

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9973 | 0.9991 |
| 2 | BAAB | 1.0105 | 1.0134 |
| 3 | ABBA | 0.9771 | 0.9796 |
| 4 | BAAB | 0.9720 | 0.9740 |
| 5 | ABBA | 0.9873 | 0.9874 |
| 6 | BAAB | 0.9728 | 0.9753 |
| 7 | ABBA | 0.9887 | 0.9922 |
| 8 | BAAB | 0.9724 | 0.9752 |
| 9 | ABBA | 0.9946 | 0.9994 |
| 10 | BAAB | 1.0345 | 1.0393 |
| 11 | ABBA | 0.9516 | 0.9533 |
| 12 | BAAB | 0.9980 | 1.0000 |
| 13 | ABBA | 1.0027 | 0.9998 |
| 14 | BAAB | 1.0009 | 1.0025 |
| 15 | ABBA | 0.9533 | 0.9552 |
| 16 | BAAB | 1.0353 | 1.0367 |

[Inputs](sol2/job20/S4b/inputs.txt) · [Raw runs](sol2/job20/S4b/runs.jsonl.txt) · [Summary](sol2/job20/S4b/summary.txt) · [Command](sol2/job20/S4b-command.raw.txt)

## Facts

The eight comparisons contain 512 timed runs and 128 warm-ups. Independent readback verified all 640 W signatures and recomputed the timing ratios. Procfs verified all 640 launch receipts. [Independent readback](sol2/job20/timing_readback.py.txt) · [Launch arms](sol2/job20/arms.txt)

## Suspicions

Pieces that change a shared hot path may interact. Each measured ratio reflects the patch or patch group added to the preceding prefix. [Build identities](sol2/job20/builds.txt)

## What this check cannot see

> The PC's Windows loader, its clang 23, its Zen 5 processor with 16 engines at once, its trained net (net768 is
synthetic), its own self-play openings; a single piece's gain near 1 % is close to what two builds of one source
differ by (up to 1.5 % on the PC).

## What I did not do

The comparisons used the fixed W workload and one pinned cloud worker. Patch application was confined to fresh scratch source copies. [Publication layout](sol2/job20/publication-layout.raw.txt)

## What I am not sure about

The pieces tested together may contribute differently when isolated. Each interval covers repeated measurements of its build pair. W records moves and last-info node counts in its trace and verifies final soft-node counts in aggregate.
