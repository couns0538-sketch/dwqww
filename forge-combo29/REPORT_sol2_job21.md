# sol2 — Job 21 build variation and Carbon2's small stack

## Step 0 — machine and frozen identities

Debian Clang 19.1.7 was verified. The cloud VM reports AMD EPYC 9V74, five logical CPUs on five guest cores, shared 32 MiB L3 and four CPU equivalents in the cgroup. W runs one engine and driver pinned to logical CPU 2. The frozen r15d, K_1 and K_2 executables matched their Job 16 hashes and each passed fresh W from its existing 72-character path with the fixed launch environment. [Machine and gate receipts](sol2/job21/step0-command.raw.txt) · [Frozen hashes](sol2/job21/clang-executables.raw.txt) · [Reference launch arms](sol2/job21/reference-arms.txt)

All three Step 0 builds matched W with 20 games, 2,247 searches, 7,905,938 last-info nodes, 9,189,426 final nodes and trace `7f78d3aec021ab01`. W uses PC20, Threads 1, Hash 16 MiB, net768 and `go softnodes 2000` on book lines 7001–7020. [r15d](sol2/job21/step0/r15d.result.raw.txt#L2-L6) · [K_1](sol2/job21/step0/K_1.result.raw.txt#L2-L6) · [K_2](sol2/job21/step0/K_2.result.raw.txt#L2-L6) · [W signature](sol2/job21/known-answer.txt#L2-L6)

| Frozen build | SHA-256 | Fresh W games / searches / last-info / final / trace |
|---|---|---|
| r15d | [`540e63c0b7cf2512f1716657aded48b0558022b49c0fe8489596195cf2035834`](sol2/job21/clang-executables.raw.txt#L1) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job21/step0/r15d.result.raw.txt#L2-L6) |
| K_1 | [`da5df215a6aa255261d4e5574474da7c82aad1a9e95df83e15d5b38963ef439d`](sol2/job21/clang-executables.raw.txt#L2) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job21/step0/K_1.result.raw.txt#L2-L6) |
| K_2 | [`2890d5b1cf4f332a87e572222d5a24ecdc014e0920a6ade776c4f22f3730187f`](sol2/job21/clang-executables.raw.txt#L3) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job21/step0/K_2.result.raw.txt#L2-L6) |

## Step 1 — independently profiled builds and launch arms

The requested three-piece stack did not apply to r15d. The literal four-piece trial was also refused. The build named N uses Carbon2's pinned M artifact. Its source receipt lists `04_S7`, `08_G4`, `11_stop_hot`, `12_v3_refresh_fuse`, `13_tt_avx512_fast_probe`. Carbon2's M includes `08_G4` as a dependency of piece 12. The artifact also removes the S13 TT test-friend declaration. Every comparison using this fallback names the same independently profiled N build. [Source variant](sol2/job21/variant.txt)

Each new build used a fresh source tree and its own profile run with the Clang recipe from Job 16. Every default pin used a fresh process with no UCI options. Each W entry links to a separate fresh process's games, searches, last-info nodes, final nodes and trace.

| Build | SHA-256 | bench 11 nodes | bench 13 nodes | go perft 5 nodes | W games / searches / last-info / final / trace | Timing gate |
|---|---|---:|---:|---:|---|---|
| r15d_2 | [`012c707703f88b224eaf2f1de5a8cba442abd6f273556bbf7de4225f0d50222c`](sol2/job21/step1-r15d_2/clang-sha256.raw.txt#L1) | [312,866](sol2/job21/build-checks/r15d_2/default-pins.raw.txt#L7) | [862,329](sol2/job21/build-checks/r15d_2/default-pins.raw.txt#L14) | [4,865,609](sol2/job21/build-checks/r15d_2/default-pins.raw.txt#L42) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job21/build-checks/r15d_2/W.result.raw.txt#L2-L6) | Pass |
| N | [`4e732c754dde18cf11e364273c0edcfc7a8d69daa2c06c5d38b99d43e4e878f4`](sol2/job21/step1-N/clang-sha256.raw.txt#L1) | [312,866](sol2/job21/build-checks/N/default-pins.raw.txt#L7) | [862,329](sol2/job21/build-checks/N/default-pins.raw.txt#L14) | [4,865,609](sol2/job21/build-checks/N/default-pins.raw.txt#L42) | [20 / 2,247 / 7,905,938 / 9,189,426 / `7f78d3aec021ab01`](sol2/job21/build-checks/N/W.result.raw.txt#L2-L6) | Pass |

[Build identities and gate status](sol2/job21/builds.txt) · [Same-source executable comparisons](sol2/job21/placebo-build-twins.raw.txt)
[Stack patch provenance and SHA-256](sol2/job21/prefix-patch-provenance.raw.txt)
[r15d_2 gates](sol2/job21/build-checks/r15d_2/checks.raw.txt) · [r15d_2 build commands](sol2/job21/step1-r15d_2/commands.raw.txt)
[N gates](sol2/job21/build-checks/N/checks.raw.txt) · [N build commands](sol2/job21/step1-N/commands.raw.txt)

### r15d_2 source preparation

[r15d_2 source receipt](sol2/job21/prefix-source/r15d_2.git-apply.raw.txt) · [r15d_2 source SHA-256 manifest](sol2/job21/prefix-source/r15d_2-source-sha256.raw.txt)

### N_1 source preparation

```sh
cd /workspace/work/sol2-job21/.N_1.partial
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job21/patches/11_stop_hot.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job21/patches/11_stop_hot.patch.txt
```

Patch check output

```text
error: patch failed: include/forge/search.hpp:593
error: include/forge/search.hpp: patch does not apply
error: patch failed: src/search.cpp:3260
error: src/search.cpp: patch does not apply
error: patch failed: src/uci.cpp:64
error: src/uci.cpp: patch does not apply
exit=1
```

[Failed check and hunk](sol2/job21/prefix-source/N_1.git-apply.raw.txt#L52-L79)

[N_1 source receipt](sol2/job21/prefix-source/N_1.git-apply.raw.txt#L34-L42)

### N-literal-fallback source preparation

```sh
cd /workspace/work/sol2-job21/.N-literal-fallback.partial
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job21/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job21/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job21/patches/04_S7.patch.txt
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job21/patches/11_stop_hot.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job21/patches/11_stop_hot.patch.txt
```

Patch check output

```text
error: patch failed: include/forge/search.hpp:593
error: include/forge/search.hpp: patch does not apply
error: patch failed: src/search.cpp:3260
error: src/search.cpp: patch does not apply
exit=1
```

[Failed check and hunk](sol2/job21/prefix-source/N-literal-fallback.git-apply.raw.txt#L73-L89)

[N-literal-fallback source receipt](sol2/job21/prefix-source/N-literal-fallback.git-apply.raw.txt#L34-L63)

### N source preparation

```sh
cd /workspace/work/sol2-job21/.N.partial
git apply --no-index -p1 --whitespace=nowarn --stat /workspace/work/sol2-job21/patches/stack_M_on_r15d.patch.txt
git apply --no-index -p1 --whitespace=nowarn --check --verbose /workspace/work/sol2-job21/patches/stack_M_on_r15d.patch.txt
git apply --no-index -p1 --whitespace=nowarn --verbose /workspace/work/sol2-job21/patches/stack_M_on_r15d.patch.txt
```

[N source receipt](sol2/job21/prefix-source/N.git-apply.raw.txt#L34-L53) · [N source SHA-256 manifest](sol2/job21/prefix-source/N-source-sha256.raw.txt)

| Arm | Engine argv[0] | Characters | Device | Inode | SHA-256 |
|---|---|---:|---:|---:|---|
| r15d | `/workspace/work/sol2-job16/arms/r15dxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 280450 | `540e63c0b7cf2512f1716657aded48b0558022b49c0fe8489596195cf2035834` |
| K_1 | `/workspace/work/sol2-job16/arms/K_1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 280452 | `da5df215a6aa255261d4e5574474da7c82aad1a9e95df83e15d5b38963ef439d` |
| K_2 | `/workspace/work/sol2-job16/arms/K_2xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 280458 | `2890d5b1cf4f332a87e572222d5a24ecdc014e0920a6ade776c4f22f3730187f` |
| r15d_2 | `/workspace/work/sol2-job21/arms/r15d_2xxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 284994 | `012c707703f88b224eaf2f1de5a8cba442abd6f273556bbf7de4225f0d50222c` |
| N | `/workspace/work/sol2-job21/arms/Nxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/forge` | 72 | 27 | 285039 | `4e732c754dde18cf11e364273c0edcfc7a8d69daa2c06c5d38b99d43e4e878f4` |

Each engine receives `LC_ALL=C` and `TZ=UTC`, 16 bytes, SHA-256 `4d41c4c11fcc6efa3bd339441ec9b26e6a1442056205420dc4b11e93dbff2570`. [Arms](sol2/job21/arms.txt)

## Prediction graded

The prediction was committed alone at `cb0ad7a34432beb9b902b7e3a2c0e990173831ad` after Step 1 and before P1.

| Comparison | Predicted CPU B/A | Observed pooled CPU B/A | Ratio in range | Expected reading | Observed reading | Reading met |
|---|---:|---:|---|---|---|---|
| P1 | 0.960–1.040 | 0.9959 | Yes | NOT SEEN | NOT SEEN | Yes |
| P2 | 0.965–1.035 | 1.0089 | Yes | NOT SEEN | NOT SEEN | Yes |
| N1 | 0.975–1.045 | 1.0302 | Yes | KEEPS | OTHER PIECES PAY | No |
| N2 | 0.975–1.045 | 1.0223 | Yes | KEEPS | OTHER PIECES PAY | No |
| R1 | 0.930–1.010 | 0.9625 | Yes | DESCRIPTIVE | Descriptive (less cpu) | Yes |
| R2 | 0.930–1.010 | 0.9618 | Yes | DESCRIPTIVE | Descriptive (less cpu) | Yes |

[Original prediction](sol2/job21/prediction.txt) · [UTC checkpoints](sol2/job21/stamps.txt)

## Step 2 — timing comparisons

Every run started a fresh engine on logical CPU 2 with workload W and the fixed replacement environment. Each arm used a 72-character executable path. Odd blocks used ABBA and even blocks used BAAB. One recorded warm-up preceded each block, and only its four timed runs entered the ratio. A run outside the W signature gate excluded its block. Engine CPU is the reaped engine process's user plus system time. Wall is the full driver call interval. Each complete comparison reports B/A with a Student t interval from the 16 block ratios and 15 degrees of freedom. [Timing commands](sol2/job21/run_campaign.sh.txt) · [Independent readback](sol2/job21/timing_readback.py.txt)

| Comparison | A | B | Metric | Blocks | Median | Pooled B/A | Mean | 95% t interval, df 15 | Below 1 |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| P1 | r15d | r15d_2 | Engine CPU | 16/16 | 0.9975 | 0.9959 | 0.9961 | [0.9833, 1.0090] | 11/16 |
| P1 | r15d | r15d_2 | Wall | 16/16 | 0.9964 | 0.9958 | 0.9961 | [0.9825, 1.0097] | 10/16 |
| P2 | K_1 | K_2 | Engine CPU | 16/16 | 1.0043 | 1.0089 | 1.0090 | [0.9965, 1.0214] | 6/16 |
| P2 | K_1 | K_2 | Wall | 16/16 | 1.0049 | 1.0104 | 1.0105 | [0.9969, 1.0240] | 5/16 |
| N1 | K_1 | N | Engine CPU | 16/16 | 1.0302 | 1.0302 | 1.0307 | [1.0155, 1.0460] | 1/16 |
| N1 | K_1 | N | Wall | 16/16 | 1.0291 | 1.0275 | 1.0281 | [1.0122, 1.0441] | 3/16 |
| N2 | K_2 | N | Engine CPU | 16/16 | 1.0278 | 1.0223 | 1.0228 | [1.0069, 1.0388] | 4/16 |
| N2 | K_2 | N | Wall | 16/16 | 1.0267 | 1.0202 | 1.0208 | [1.0043, 1.0372] | 4/16 |
| R1 | r15d | N | Engine CPU | 16/16 | 0.9601 | 0.9625 | 0.9629 | [0.9474, 0.9783] | 13/16 |
| R1 | r15d | N | Wall | 16/16 | 0.9630 | 0.9657 | 0.9661 | [0.9500, 0.9822] | 13/16 |
| R2 | r15d_2 | N | Engine CPU | 16/16 | 0.9640 | 0.9618 | 0.9620 | [0.9448, 0.9793] | 14/16 |
| R2 | r15d_2 | N | Wall | 16/16 | 0.9687 | 0.9650 | 0.9652 | [0.9472, 0.9833] | 14/16 |

## Declared readings and arithmetic

Pool and mean report B/A. Percentages are time differences for B relative to A, shown as pooled / mean [95% t interval]. Negative values favor B.

| Comparison | A | B | Metric | Pooled / mean [95% t interval] | Time difference | Reading |
|---|---|---|---|---:|---:|---|
| [P1](sol2/job21/P1/summary.txt#L112-L146) | r15d | r15d_2 | Engine CPU | 0.9959 / 0.9961 [0.9833, 1.0090] | -0.41% / -0.39% [-1.67%, +0.90%] | NOT SEEN |
| [P1](sol2/job21/P1/summary.txt#L112-L146) | r15d | r15d_2 | Wall | 0.9958 / 0.9961 [0.9825, 1.0097] | -0.42% / -0.39% [-1.75%, +0.97%] | NOT SEEN |
| [P2](sol2/job21/P2/summary.txt#L112-L146) | K_1 | K_2 | Engine CPU | 1.0089 / 1.0090 [0.9965, 1.0214] | +0.89% / +0.90% [-0.35%, +2.14%] | NOT SEEN |
| [P2](sol2/job21/P2/summary.txt#L112-L146) | K_1 | K_2 | Wall | 1.0104 / 1.0105 [0.9969, 1.0240] | +1.04% / +1.05% [-0.31%, +2.40%] | NOT SEEN |
| [N1](sol2/job21/N1/summary.txt#L112-L146) | K_1 | N | Engine CPU | 1.0302 / 1.0307 [1.0155, 1.0460] | +3.02% / +3.07% [+1.55%, +4.60%] | COSTS |
| [N1](sol2/job21/N1/summary.txt#L112-L146) | K_1 | N | Wall | 1.0275 / 1.0281 [1.0122, 1.0441] | +2.75% / +2.81% [+1.22%, +4.41%] | COSTS |
| [N2](sol2/job21/N2/summary.txt#L112-L146) | K_2 | N | Engine CPU | 1.0223 / 1.0228 [1.0069, 1.0388] | +2.23% / +2.28% [+0.69%, +3.88%] | COSTS |
| [N2](sol2/job21/N2/summary.txt#L112-L146) | K_2 | N | Wall | 1.0202 / 1.0208 [1.0043, 1.0372] | +2.02% / +2.08% [+0.43%, +3.72%] | COSTS |
| [R1](sol2/job21/R1/summary.txt#L112-L146) | r15d | N | Engine CPU | 0.9625 / 0.9629 [0.9474, 0.9783] | -3.75% / -3.71% [-5.26%, -2.17%] | DESCRIPTIVE |
| [R1](sol2/job21/R1/summary.txt#L112-L146) | r15d | N | Wall | 0.9657 / 0.9661 [0.9500, 0.9822] | -3.43% / -3.39% [-5.00%, -1.78%] | DESCRIPTIVE |
| [R2](sol2/job21/R2/summary.txt#L112-L146) | r15d_2 | N | Engine CPU | 0.9618 / 0.9620 [0.9448, 0.9793] | -3.82% / -3.80% [-5.52%, -2.07%] | DESCRIPTIVE |
| [R2](sol2/job21/R2/summary.txt#L112-L146) | r15d_2 | N | Wall | 0.9650 / 0.9652 [0.9472, 0.9833] | -3.50% / -3.48% [-5.28%, -1.67%] | DESCRIPTIVE |

A complete interval wholly below 1 gives PAYS. An interval wholly above 1 gives COSTS. An interval containing 1 gives NOT SEEN.

Small stack versus kF **OTHER PIECES PAY**. Both CPU intervals read COSTS.

N1 and N2 compare the same fallback N build against the two kF builds. R1 and R2 also use that same N executable. [Variant receipt](sol2/job21/variant.txt)

Both same-source CPU intervals contain parity. The measurements leave room for build-to-build differences within the intervals shown above.

### P1

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 1.0028 | 1.0033 |
| 2 | BAAB | 1.0192 | 1.0256 |
| 3 | ABBA | 0.9999 | 1.0007 |
| 4 | BAAB | 0.9977 | 0.9959 |
| 5 | ABBA | 0.9922 | 0.9905 |
| 6 | BAAB | 0.9830 | 0.9815 |
| 7 | ABBA | 0.9874 | 0.9862 |
| 8 | BAAB | 0.9879 | 0.9856 |
| 9 | ABBA | 0.9472 | 0.9440 |
| 10 | BAAB | 1.0191 | 1.0203 |
| 11 | ABBA | 1.0389 | 1.0393 |
| 12 | BAAB | 0.9585 | 0.9577 |
| 13 | ABBA | 1.0324 | 1.0332 |
| 14 | BAAB | 0.9980 | 0.9988 |
| 15 | ABBA | 0.9769 | 0.9772 |
| 16 | BAAB | 0.9972 | 0.9969 |

[Inputs](sol2/job21/P1/inputs.txt) · [Raw runs](sol2/job21/P1/runs.jsonl.txt) · [Summary](sol2/job21/P1/summary.txt) · [Command](sol2/job21/P1-command.raw.txt)

### P2

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 1.0040 | 1.0038 |
| 2 | BAAB | 0.9962 | 0.9937 |
| 3 | ABBA | 1.0045 | 1.0060 |
| 4 | BAAB | 0.9812 | 0.9820 |
| 5 | ABBA | 1.0284 | 1.0269 |
| 6 | BAAB | 1.0140 | 1.0161 |
| 7 | ABBA | 1.0333 | 1.0368 |
| 8 | BAAB | 1.0677 | 1.0750 |
| 9 | ABBA | 0.9991 | 1.0002 |
| 10 | BAAB | 0.9811 | 0.9809 |
| 11 | ABBA | 1.0005 | 1.0034 |
| 12 | BAAB | 1.0137 | 1.0155 |
| 13 | ABBA | 0.9797 | 0.9795 |
| 14 | BAAB | 1.0335 | 1.0431 |
| 15 | ABBA | 0.9925 | 0.9930 |
| 16 | BAAB | 1.0138 | 1.0120 |

[Inputs](sol2/job21/P2/inputs.txt) · [Raw runs](sol2/job21/P2/runs.jsonl.txt) · [Summary](sol2/job21/P2/summary.txt) · [Command](sol2/job21/P2-command.raw.txt)

### N1

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 1.0027 | 1.0016 |
| 2 | BAAB | 1.0625 | 1.0600 |
| 3 | ABBA | 1.0722 | 1.0721 |
| 4 | BAAB | 1.0648 | 1.0646 |
| 5 | ABBA | 1.0321 | 1.0318 |
| 6 | BAAB | 1.0396 | 1.0375 |
| 7 | ABBA | 0.9747 | 0.9707 |
| 8 | BAAB | 1.0033 | 0.9977 |
| 9 | ABBA | 1.0006 | 0.9934 |
| 10 | BAAB | 1.0138 | 1.0120 |
| 11 | ABBA | 1.0258 | 1.0247 |
| 12 | BAAB | 1.0626 | 1.0623 |
| 13 | ABBA | 1.0364 | 1.0315 |
| 14 | BAAB | 1.0110 | 1.0045 |
| 15 | ABBA | 1.0613 | 1.0592 |
| 16 | BAAB | 1.0283 | 1.0267 |

[Inputs](sol2/job21/N1/inputs.txt) · [Raw runs](sol2/job21/N1/runs.jsonl.txt) · [Summary](sol2/job21/N1/summary.txt) · [Command](sol2/job21/N1-command.raw.txt)

### N2

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 1.0537 | 1.0537 |
| 2 | BAAB | 1.0231 | 1.0175 |
| 3 | ABBA | 0.9759 | 0.9754 |
| 4 | BAAB | 0.9866 | 0.9830 |
| 5 | ABBA | 1.0389 | 1.0391 |
| 6 | BAAB | 1.0428 | 1.0404 |
| 7 | ABBA | 1.0150 | 1.0090 |
| 8 | BAAB | 1.0839 | 1.0839 |
| 9 | ABBA | 1.0325 | 1.0316 |
| 10 | BAAB | 0.9915 | 0.9886 |
| 11 | ABBA | 1.0223 | 1.0231 |
| 12 | BAAB | 1.0089 | 1.0091 |
| 13 | ABBA | 1.0466 | 1.0460 |
| 14 | BAAB | 0.9737 | 0.9692 |
| 15 | ABBA | 1.0376 | 1.0323 |
| 16 | BAAB | 1.0329 | 1.0302 |

[Inputs](sol2/job21/N2/inputs.txt) · [Raw runs](sol2/job21/N2/runs.jsonl.txt) · [Summary](sol2/job21/N2/summary.txt) · [Command](sol2/job21/N2-command.raw.txt)

### R1

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 1.0013 | 1.0072 |
| 2 | BAAB | 1.0138 | 1.0182 |
| 3 | ABBA | 0.9282 | 0.9325 |
| 4 | BAAB | 0.9298 | 0.9309 |
| 5 | ABBA | 0.9745 | 0.9787 |
| 6 | BAAB | 0.9814 | 0.9863 |
| 7 | ABBA | 0.9606 | 0.9644 |
| 8 | BAAB | 0.9529 | 0.9559 |
| 9 | ABBA | 0.9596 | 0.9640 |
| 10 | BAAB | 0.9799 | 0.9833 |
| 11 | ABBA | 0.9606 | 0.9621 |
| 12 | BAAB | 1.0129 | 1.0182 |
| 13 | ABBA | 0.9301 | 0.9321 |
| 14 | BAAB | 0.9390 | 0.9395 |
| 15 | ABBA | 0.9504 | 0.9517 |
| 16 | BAAB | 0.9311 | 0.9330 |

[Inputs](sol2/job21/R1/inputs.txt) · [Raw runs](sol2/job21/R1/runs.jsonl.txt) · [Summary](sol2/job21/R1/summary.txt) · [Command](sol2/job21/R1-command.raw.txt)

### R2

Logical CPU 2. 80 attempted runs, 16 included blocks, 64 included timed runs.

| Block | Timed order | B/A CPU | B/A wall |
|---:|---|---:|---:|
| 1 | ABBA | 0.9190 | 0.9185 |
| 2 | BAAB | 0.9553 | 0.9567 |
| 3 | ABBA | 0.9335 | 0.9343 |
| 4 | BAAB | 0.9412 | 0.9430 |
| 5 | ABBA | 0.9020 | 0.9045 |
| 6 | BAAB | 0.9888 | 0.9920 |
| 7 | ABBA | 0.9444 | 0.9478 |
| 8 | BAAB | 0.9829 | 0.9888 |
| 9 | ABBA | 0.9395 | 0.9414 |
| 10 | BAAB | 0.9638 | 0.9669 |
| 11 | ABBA | 0.9877 | 0.9909 |
| 12 | BAAB | 1.0307 | 1.0387 |
| 13 | ABBA | 0.9650 | 0.9710 |
| 14 | BAAB | 0.9642 | 0.9704 |
| 15 | ABBA | 0.9745 | 0.9747 |
| 16 | BAAB | 1.0001 | 1.0040 |

[Inputs](sol2/job21/R2/inputs.txt) · [Raw runs](sol2/job21/R2/runs.jsonl.txt) · [Summary](sol2/job21/R2/summary.txt) · [Command](sol2/job21/R2-command.raw.txt)

## Facts

The six comparisons contain 384 timed runs and 96 warm-ups. Independent readback verified all 480 W signatures and recomputed the timing ratios. Procfs verified all 480 launch receipts. [Independent readback](sol2/job21/timing_readback.py.txt) · [Launch arms](sol2/job21/arms.txt)

## Suspicions

Separately profiled builds can arrange the same hot paths differently. The placebo rows measure the size of that variation under W. [Build identities](sol2/job21/builds.txt)

## What this check cannot see

> The PC's Windows loader, its clang 23, its Zen 5 processor with 16 engines at once, its trained net (net768 is
synthetic), its own self-play openings.

## What I did not do

The timing scope was one pinned cloud worker with W. Patch application was confined to fresh scratch source copies. [Publication layout](sol2/job21/publication-layout.raw.txt)

## What I am not sure about

The pieces tested together may contribute differently when isolated. Each interval covers repeated measurements of its build pair. The W trace covers moves and last-info node counts, with aggregate checks on final soft-node counts.
