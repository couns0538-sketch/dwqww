# sol2 — Job 8 AVX-512 transposition-table timing

## Step 0 — exact patch and node pins passed

The two frozen Job 7 GCC LTO+PGO executables were present and matched their archived hashes. I reused them for timing. The r15d-pgo and plain r15d builds each returned **312,866** for `bench 11`, **862,329** for `bench 13` and **4,865,609** for startpos `go perft 5` in fresh processes with zero UCI option overrides. [Frozen hashes and toolchain](sol2/job8/step0-frozen-identities.raw.txt) · [r15d-pgo pins](sol2/job8/step0-r15d-pgo-pins.raw.txt) · [Plain r15d pins](sol2/job8/step0-r15d-pins.raw.txt)

I verified Carbon2's `13_tt_avx512_fast_probe.patch.txt` at commit `6d4876d281db74f6a0b851db81d9ab1f01db2761`. Its SHA-256 was **`a6d66722e690c5fe3f1fb397405a3f8470b8dd1bd300887a5e2442ae132e02eb`**. I applied it with `patch --batch -p1 -F0` to a scratch copy of k11v. The patch exited zero with exact context, zero offsets or fuzz, and zero rejects. Its complete output follows. [Pinned patch retrieval](sol2/job8/step0-patch-source.raw.txt) · [Command and build](sol2/job8/step0-build-command.raw.txt) · [Patch output](sol2/job8/step0-patch.raw.txt)

```text
patching file include/forge/search.hpp
patching file src/search.cpp
```

The plain GCC Release k13 executable SHA-256 was `0a54e59a8500958605476814d424e00f9d392fa719e706284ef61ecc70c096a3`. Fresh default-option processes matched all three base pins, including byte-identical counts for all 20 startpos perft root moves against r15d-pgo. Fresh PC20 processes with net768 activated matched **882,074** and **4,275,906** for bench 11 and 13, respectively. The net768 bench used Threads 1, Hash 16 MiB, and OwnBook false. [Plain build lines](sol2/job8/step0-k13-build.raw.txt) · [Executable hash](sol2/job8/step0-k13-release-sha256.raw.txt) · [Default pins](sol2/job8/step0-k13-pins.raw.txt) · [PC20/net768 pins](sol2/job8/step0-k13-net768.raw.txt)

## Prediction graded

The prediction was published alone at `470c95ae436dfb36d1a0c7ee7a528f3cf410b82b` after Step 0 and before Step 1.

| Quantity | Prediction | Observed | Observed minus prediction |
|---|---:|---:|---:|
| Identical-binary CPU minimum | 0.974 | 0.9456 | -0.0284 |
| Identical-binary CPU maximum | 1.042 | 0.9924 | -0.0496 |
| Pooled k13-pgo/k11v-pgo CPU | 0.984 | 0.9812 | -0.0028 |
| k13-pgo/k11v-pgo CPU blocks below 1 | 10/12 | 9/12 | -1 blocks |
| Pooled k13-pgo/r15d-pgo CPU | 0.902 | 0.9119 | +0.0099 |

[Original prediction](sol2/job8/prediction.txt) · [UTC checkpoints](sol2/job8/stamps.txt)

## Step 1 — k13's own profile and held-out identity passed

k13 used CMake Release, GCC 14.2.0 (Debian 14.2.0-19), libstdc++ 6.0.33, glibc 2.41, C++20, `-O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4`, and the same build definitions as k11v. The generate compile and link lines added `-flto -fprofile-generate=/workspace/work/sol2-job8/pgo-data-k13`. The use build ran `--clean-first` in the same build directory with `-flto -fprofile-use=/workspace/work/sol2-job8/pgo-data-k13 -Werror=missing-profile -Werror=coverage-mismatch`. The command and verbose logs show every compile and link line. The nine GCC counter receipts each show one recorded run, and their hashes matched after both rebuild and identity. [Commands](sol2/job8/k13-step1-command.raw.txt) · [Generate lines](sol2/job8/k13-pgo-generate-build.raw.txt) · [Use lines](sol2/job8/k13-pgo-use-build.raw.txt) · [Counter inventory](sol2/job8/k13-gcda-inventory.raw.txt)

| Executable | SHA-256 | Profile searches / last-info nodes / trace | Held-out searches / last-info nodes / trace |
|---|---|---|---|
| r15d-pgo | `96f50b3eb6d4f05cfa8291eaab56ea9c943a8e98fb3b248fff3b9138fcce6808` | 2,482 / 8,391,013 / `c7d9520ffe04deda` | 8,612 / 29,333,343 / `5c705841c3ea17b4` |
| k11v-pgo | `95980ac637b41376245996617d537fd38ef54f223cc93f13673915bfb6f3079c` | 2,482 / 8,391,013 / `c7d9520ffe04deda` | 8,612 / 29,333,343 / `5c705841c3ea17b4` |
| k13-pgo | `4d7b70e42fc0074ea40c6cf240ebef5701bdd49417d0b18a8e7bd5bf00cf177b` | 2,482 / 8,391,013 / `c7d9520ffe04deda` | 8,612 / 29,333,343 / `5c705841c3ea17b4` |

Every workload used the pinned Carbon2 driver SHA-256 `c79b95bf45762fa9869d23140ed7f946cfaf0cb6bc4f74325a18d5f934bf1c45`, PC20, Threads 1, Hash 16 MiB, OwnBook false and the v3 synthetic net768 SHA-256 `c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7`. Both workloads used `go softnodes 2000`, eight opening plies and a 300-ply ceiling. The 20 profile games used seed `20261118`. The 60 timing and identity games used seed `20261117`. Each of k13's opening receipts was byte-identical to k11v's receipt for the same workload in Job 7. The profile and timing opening suites share zero eight-ply move vectors and zero post-opening keys of placement, side to move and castling rights. [Opening readback](sol2/job8/opening-independence.raw.txt) · [k13 training JSON](sol2/job8/k13-training.raw.txt) · [k13 identity JSON](sol2/job8/k13-identity.raw.txt) · [Job 7 frozen build receipts](REPORT_sol2_job7.md)

## Steps 2–4 — timing and decision

The ABBA block ratio divides the two B times by the two A times after summing each arm separately. The pooled ratio uses all included times in each arm. The timing rule requires a median beyond the full six-block identical-binary range and at least 10 of 12 complete blocks on the same side of one. Engine CPU is the reaped engine's user plus system time. Wall covers the driver call, including setup, warm-up and teardown. Each driver ran on logical CPU 2 with a fresh engine. The control used a distinct k11v-pgo path with a matching SHA-256 and a byte-identical `cmp`. [Copy receipt](sol2/job8/step2-copy.raw.txt) · [Timing harness](sol2/job8/abba_timing.py.txt) · [Independent readback](sol2/job8/timing_readback.py.txt)

All tables use PC20, Threads 1, Hash 16 MiB, net768, seed 20261117 and `go softnodes 2000`. Each eligible run records 8,612 searches, 29,333,343 nodes and trace `5c705841c3ea17b4`.

### Step 2 — identical-binary ABBA floor

B/A compares `copy` (`95980ac637b41376245996617d537fd38ef54f223cc93f13673915bfb6f3079c`) with `k11v-pgo` (`95980ac637b41376245996617d537fd38ef54f223cc93f13673915bfb6f3079c`).

| Block | Leg | Engine | CPU (s) | Wall (s) | Trace | Exit | Included |
|---:|---:|---|---:|---:|---|---:|---|
| 1 | 1 | k11v-pgo | 19.235 | 20.040 | `5c705841c3ea17b4` | 0 | yes |
| 1 | 2 | copy | 17.493 | 18.244 | `5c705841c3ea17b4` | 0 | yes |
| 1 | 3 | copy | 18.560 | 19.338 | `5c705841c3ea17b4` | 0 | yes |
| 1 | 4 | k11v-pgo | 18.715 | 19.493 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 1 | k11v-pgo | 17.461 | 18.202 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 2 | copy | 17.351 | 18.084 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 3 | copy | 17.539 | 18.284 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 4 | k11v-pgo | 17.734 | 18.486 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 1 | k11v-pgo | 17.575 | 18.324 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 2 | copy | 17.359 | 18.090 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 3 | copy | 17.642 | 18.394 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 4 | k11v-pgo | 17.694 | 18.434 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 1 | k11v-pgo | 17.731 | 18.453 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 2 | copy | 17.597 | 18.353 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 3 | copy | 19.963 | 20.880 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 4 | k11v-pgo | 20.297 | 21.223 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 1 | k11v-pgo | 20.250 | 21.185 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 2 | copy | 19.362 | 20.235 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 3 | copy | 19.029 | 19.862 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 4 | k11v-pgo | 20.348 | 21.263 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 1 | k11v-pgo | 19.602 | 20.482 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 2 | copy | 18.922 | 19.731 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 3 | copy | 19.678 | 20.564 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 4 | k11v-pgo | 19.508 | 20.409 | `5c705841c3ea17b4` | 0 | yes |

| Block | B/A CPU | B/A wall |
|---:|---:|---:|
| 1 | 0.9500 | 0.9507 |
| 2 | 0.9913 | 0.9913 |
| 3 | 0.9924 | 0.9925 |
| 4 | 0.9877 | 0.9889 |
| 5 | 0.9456 | 0.9446 |
| 6 | 0.9870 | 0.9854 |

| Metric | Median | Pooled | Block range | Below 1 | Above 1 | Reading |
|---|---:|---:|---:|---:|---:|---|
| Engine CPU | 0.9873 | 0.9750 | 0.9456–0.9924 | 6/6 | 0/6 | Identical-binary floor |
| Wall | 0.9872 | 0.9749 | 0.9446–0.9925 | 6/6 | 0/6 | Identical-binary floor |

[Inputs](sol2/job8/step2/inputs.txt) · [Raw runs](sol2/job8/step2/runs.jsonl.txt) · [Summary](sol2/job8/step2/summary.txt) · [Command](sol2/job8/step2-command.raw.txt)

### Step 3 — k13-pgo against k11v-pgo

B/A compares `k13-pgo` (`4d7b70e42fc0074ea40c6cf240ebef5701bdd49417d0b18a8e7bd5bf00cf177b`) with `k11v-pgo` (`95980ac637b41376245996617d537fd38ef54f223cc93f13673915bfb6f3079c`).

| Block | Leg | Engine | CPU (s) | Wall (s) | Trace | Exit | Included |
|---:|---:|---|---:|---:|---|---:|---|
| 1 | 1 | k11v-pgo | 17.840 | 18.603 | `5c705841c3ea17b4` | 0 | yes |
| 1 | 2 | k13-pgo | 16.880 | 17.594 | `5c705841c3ea17b4` | 0 | yes |
| 1 | 3 | k13-pgo | 17.695 | 18.443 | `5c705841c3ea17b4` | 0 | yes |
| 1 | 4 | k11v-pgo | 17.934 | 18.705 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 1 | k11v-pgo | 17.938 | 18.701 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 2 | k13-pgo | 17.549 | 18.310 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 3 | k13-pgo | 18.033 | 18.811 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 4 | k11v-pgo | 18.049 | 18.823 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 1 | k11v-pgo | 17.428 | 18.153 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 2 | k13-pgo | 16.648 | 17.344 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 3 | k13-pgo | 18.144 | 18.961 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 4 | k11v-pgo | 18.453 | 19.263 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 1 | k11v-pgo | 18.337 | 19.140 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 2 | k13-pgo | 18.649 | 19.465 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 3 | k13-pgo | 17.969 | 18.737 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 4 | k11v-pgo | 17.451 | 18.191 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 1 | k11v-pgo | 17.417 | 18.134 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 2 | k13-pgo | 17.093 | 17.811 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 3 | k13-pgo | 17.349 | 18.100 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 4 | k11v-pgo | 17.914 | 18.682 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 1 | k11v-pgo | 17.502 | 18.233 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 2 | k13-pgo | 18.488 | 19.275 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 3 | k13-pgo | 18.077 | 18.859 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 4 | k11v-pgo | 17.858 | 18.613 | `5c705841c3ea17b4` | 0 | yes |
| 7 | 1 | k11v-pgo | 18.300 | 19.104 | `5c705841c3ea17b4` | 0 | yes |
| 7 | 2 | k13-pgo | 17.468 | 18.226 | `5c705841c3ea17b4` | 0 | yes |
| 7 | 3 | k13-pgo | 18.084 | 18.864 | `5c705841c3ea17b4` | 0 | yes |
| 7 | 4 | k11v-pgo | 18.188 | 18.970 | `5c705841c3ea17b4` | 0 | yes |
| 8 | 1 | k11v-pgo | 19.079 | 19.908 | `5c705841c3ea17b4` | 0 | yes |
| 8 | 2 | k13-pgo | 18.111 | 18.890 | `5c705841c3ea17b4` | 0 | yes |
| 8 | 3 | k13-pgo | 17.212 | 17.959 | `5c705841c3ea17b4` | 0 | yes |
| 8 | 4 | k11v-pgo | 18.516 | 19.307 | `5c705841c3ea17b4` | 0 | yes |
| 9 | 1 | k11v-pgo | 18.835 | 19.670 | `5c705841c3ea17b4` | 0 | yes |
| 9 | 2 | k13-pgo | 17.028 | 17.755 | `5c705841c3ea17b4` | 0 | yes |
| 9 | 3 | k13-pgo | 17.290 | 18.027 | `5c705841c3ea17b4` | 0 | yes |
| 9 | 4 | k11v-pgo | 17.965 | 18.740 | `5c705841c3ea17b4` | 0 | yes |
| 10 | 1 | k11v-pgo | 19.644 | 20.525 | `5c705841c3ea17b4` | 0 | yes |
| 10 | 2 | k13-pgo | 18.668 | 19.495 | `5c705841c3ea17b4` | 0 | yes |
| 10 | 3 | k13-pgo | 18.253 | 19.062 | `5c705841c3ea17b4` | 0 | yes |
| 10 | 4 | k11v-pgo | 18.073 | 18.851 | `5c705841c3ea17b4` | 0 | yes |
| 11 | 1 | k11v-pgo | 18.020 | 18.809 | `5c705841c3ea17b4` | 0 | yes |
| 11 | 2 | k13-pgo | 18.158 | 18.946 | `5c705841c3ea17b4` | 0 | yes |
| 11 | 3 | k13-pgo | 18.249 | 19.044 | `5c705841c3ea17b4` | 0 | yes |
| 11 | 4 | k11v-pgo | 17.448 | 18.192 | `5c705841c3ea17b4` | 0 | yes |
| 12 | 1 | k11v-pgo | 17.538 | 18.286 | `5c705841c3ea17b4` | 0 | yes |
| 12 | 2 | k13-pgo | 16.709 | 17.393 | `5c705841c3ea17b4` | 0 | yes |
| 12 | 3 | k13-pgo | 17.301 | 18.057 | `5c705841c3ea17b4` | 0 | yes |
| 12 | 4 | k11v-pgo | 17.545 | 18.302 | `5c705841c3ea17b4` | 0 | yes |

| Block | B/A CPU | B/A wall |
|---:|---:|---:|
| 1 | 0.9665 | 0.9659 |
| 2 | 0.9887 | 0.9893 |
| 3 | 0.9696 | 0.9703 |
| 4 | 1.0232 | 1.0233 |
| 5 | 0.9748 | 0.9754 |
| 6 | 1.0341 | 1.0350 |
| 7 | 0.9743 | 0.9742 |
| 8 | 0.9396 | 0.9396 |
| 9 | 0.9326 | 0.9316 |
| 10 | 0.9789 | 0.9792 |
| 11 | 1.0265 | 1.0267 |
| 12 | 0.9694 | 0.9689 |

| Metric | Median | Pooled | Block range | Below 1 | Above 1 | Reading |
|---|---:|---:|---:|---:|---:|---|
| Engine CPU | 0.9746 | 0.9812 | 0.9326–1.0341 | 9/12 | 3/12 | not measurable here |
| Wall | 0.9748 | 0.9812 | 0.9316–1.0350 | 9/12 | 3/12 | not measurable here |

[Inputs](sol2/job8/step3/inputs.txt) · [Raw runs](sol2/job8/step3/runs.jsonl.txt) · [Summary](sol2/job8/step3/summary.txt) · [Command](sol2/job8/step3-command.raw.txt)

### Step 4 — k13-pgo against r15d-pgo

B/A compares `k13-pgo` (`4d7b70e42fc0074ea40c6cf240ebef5701bdd49417d0b18a8e7bd5bf00cf177b`) with `r15d-pgo` (`96f50b3eb6d4f05cfa8291eaab56ea9c943a8e98fb3b248fff3b9138fcce6808`).

| Block | Leg | Engine | CPU (s) | Wall (s) | Trace | Exit | Included |
|---:|---:|---|---:|---:|---|---:|---|
| 1 | 1 | r15d-pgo | 19.681 | 20.512 | `5c705841c3ea17b4` | 0 | yes |
| 1 | 2 | k13-pgo | 18.588 | 19.411 | `5c705841c3ea17b4` | 0 | yes |
| 1 | 3 | k13-pgo | 19.007 | 19.888 | `5c705841c3ea17b4` | 0 | yes |
| 1 | 4 | r15d-pgo | 19.960 | 20.801 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 1 | r15d-pgo | 19.798 | 20.667 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 2 | k13-pgo | 18.310 | 19.138 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 3 | k13-pgo | 18.102 | 18.900 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 4 | r15d-pgo | 19.341 | 20.125 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 1 | r15d-pgo | 19.915 | 20.735 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 2 | k13-pgo | 18.652 | 19.484 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 3 | k13-pgo | 19.305 | 20.169 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 4 | r15d-pgo | 19.690 | 20.531 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 1 | r15d-pgo | 19.457 | 20.259 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 2 | k13-pgo | 17.866 | 18.653 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 3 | k13-pgo | 17.369 | 18.127 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 4 | r15d-pgo | 19.287 | 20.093 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 1 | r15d-pgo | 19.123 | 19.881 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 2 | k13-pgo | 17.030 | 17.752 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 3 | k13-pgo | 17.495 | 18.257 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 4 | r15d-pgo | 20.632 | 21.509 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 1 | r15d-pgo | 19.869 | 20.694 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 2 | k13-pgo | 17.766 | 18.527 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 3 | k13-pgo | 17.460 | 18.209 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 4 | r15d-pgo | 18.901 | 19.677 | `5c705841c3ea17b4` | 0 | yes |
| 7 | 1 | r15d-pgo | 19.408 | 20.189 | `5c705841c3ea17b4` | 0 | yes |
| 7 | 2 | k13-pgo | 18.583 | 19.421 | `5c705841c3ea17b4` | 0 | yes |
| 7 | 3 | k13-pgo | 17.765 | 18.532 | `5c705841c3ea17b4` | 0 | yes |
| 7 | 4 | r15d-pgo | 19.783 | 20.606 | `5c705841c3ea17b4` | 0 | yes |
| 8 | 1 | r15d-pgo | 18.803 | 19.562 | `5c705841c3ea17b4` | 0 | yes |
| 8 | 2 | k13-pgo | 17.310 | 18.081 | `5c705841c3ea17b4` | 0 | yes |
| 8 | 3 | k13-pgo | 17.215 | 17.961 | `5c705841c3ea17b4` | 0 | yes |
| 8 | 4 | r15d-pgo | 19.504 | 20.315 | `5c705841c3ea17b4` | 0 | yes |
| 9 | 1 | r15d-pgo | 19.546 | 20.390 | `5c705841c3ea17b4` | 0 | yes |
| 9 | 2 | k13-pgo | 17.611 | 18.394 | `5c705841c3ea17b4` | 0 | yes |
| 9 | 3 | k13-pgo | 17.902 | 18.689 | `5c705841c3ea17b4` | 0 | yes |
| 9 | 4 | r15d-pgo | 20.432 | 21.307 | `5c705841c3ea17b4` | 0 | yes |
| 10 | 1 | r15d-pgo | 19.937 | 20.769 | `5c705841c3ea17b4` | 0 | yes |
| 10 | 2 | k13-pgo | 17.913 | 18.725 | `5c705841c3ea17b4` | 0 | yes |
| 10 | 3 | k13-pgo | 17.143 | 17.871 | `5c705841c3ea17b4` | 0 | yes |
| 10 | 4 | r15d-pgo | 19.241 | 20.024 | `5c705841c3ea17b4` | 0 | yes |
| 11 | 1 | r15d-pgo | 21.951 | 22.919 | `5c705841c3ea17b4` | 0 | yes |
| 11 | 2 | k13-pgo | 20.786 | 21.769 | `5c705841c3ea17b4` | 0 | yes |
| 11 | 3 | k13-pgo | 19.964 | 20.883 | `5c705841c3ea17b4` | 0 | yes |
| 11 | 4 | r15d-pgo | 21.440 | 22.377 | `5c705841c3ea17b4` | 0 | yes |
| 12 | 1 | r15d-pgo | 21.967 | 22.928 | `5c705841c3ea17b4` | 0 | yes |
| 12 | 2 | k13-pgo | 18.168 | 18.989 | `5c705841c3ea17b4` | 0 | yes |
| 12 | 3 | k13-pgo | 19.079 | 19.964 | `5c705841c3ea17b4` | 0 | yes |
| 12 | 4 | r15d-pgo | 20.894 | 21.779 | `5c705841c3ea17b4` | 0 | yes |

| Block | B/A CPU | B/A wall |
|---:|---:|---:|
| 1 | 0.9484 | 0.9512 |
| 2 | 0.9303 | 0.9325 |
| 3 | 0.9584 | 0.9609 |
| 4 | 0.9095 | 0.9115 |
| 5 | 0.8684 | 0.8700 |
| 6 | 0.9086 | 0.9100 |
| 7 | 0.9275 | 0.9303 |
| 8 | 0.9013 | 0.9038 |
| 9 | 0.8883 | 0.8893 |
| 10 | 0.8948 | 0.8971 |
| 11 | 0.9391 | 0.9416 |
| 12 | 0.8690 | 0.8713 |

| Metric | Median | Pooled | Block range | Below 1 | Above 1 | Reading |
|---|---:|---:|---:|---:|---:|---|
| Engine CPU | 0.9090 | 0.9119 | 0.8684–0.9584 | 12/12 | 0/12 | MEASURED |
| Wall | 0.9107 | 0.9141 | 0.8700–0.9609 | 12/12 | 0/12 | MEASURED |

[Inputs](sol2/job8/step4/inputs.txt) · [Raw runs](sol2/job8/step4/runs.jsonl.txt) · [Summary](sol2/job8/step4/summary.txt) · [Command](sol2/job8/step4-command.raw.txt)

### k13-pgo against r15d-pgo, direct and composed CPU ratios

| Basis | Pooled CPU B/A | Reading |
|---|---:|---|
| Job 7 factor 0.9135 × Step 3 (0.981156) | 0.896286 | Composed estimate. Step 3 was not measurable here. |
| Step 4 direct | 0.911882 | MEASURED |

The composed estimate multiplies pooled point estimates from three adjacent comparisons. The direct comparison uses its own matched ABBA blocks and the current floor. [Job 7 report](REPORT_sol2_job7.md)


## Facts

- All 120 timing passes exited zero with the pinned 60-game PC20/net768 signature of 8,612 searches, 29,333,343 last-info nodes and trace `5c705841c3ea17b4`. The independent readback reconciled each driver's output with the timing row and recomputed the two estimators from the raw observations. [Readback script](sol2/job8/timing_readback.py.txt)
- For patch 13 on the cloud GCC LTO+PGO stack, k13-pgo used **1.88% less engine CPU** pooled against k11v-pgo, with 9/12 CPU blocks below one. The readings were **not measurable here** for engine CPU and **not measurable here** for wall. [Adjacent comparison](sol2/job8/step3/summary.txt)
- The full stack k13-pgo used **8.81% less engine CPU** pooled against r15d-pgo, with 12/12 CPU blocks below one. The readings were **MEASURED** for engine CPU and **MEASURED** for wall. Direct minus composed pooled CPU was +1.56 percentage points. The composed ratio uses the rounded 0.9135 from the handoff and the Step 3 pooled point estimate. [Direct comparison](sol2/job8/step4/summary.txt) · [Opus handoff](https://github.com/couns0538-sketch/dwqww/blob/1a071fe726d1fca6f83fbe51e1b1aa6b7abe608e/forge-combo29/soak_all/FABLE_TO_sol2_8.md)

## Suspicions

The byte-identical B copy was below one in all 6 of 6 CPU blocks. The full control range was 0.9456–0.9924. The cause of the control imbalance is unresolved. [Identical-binary control](sol2/job8/step2/summary.txt)

The owned probe and store compare four keys at once. The cost of this change may depend on hit rate, cluster occupancy, and the compiler's code layout. The timing design estimates the patch's combined effect across the workload. It leaves the contributions of individual paths unresolved. [Archived patch](sol2/job8/13_tt_avx512_fast_probe.patch.txt)

## What this check cannot see

More than one thread (piece 13's locked paths, `probe_locked_fast` and `store_locked_fast`, run only when a worker
does not hold the table alone), Hash sizes other than 16, a game clock, the PC's own net, compiler (clang with
ThinLTO and a profile from self-play) and processor.

## What I did not do

The experiment used a scratch GCC build, synthetic net and one pinned self-play workload. The release k13 build was used for the node gates. The report and raw receipts are text, with the original candidate diff archived separately. [Publication layout](sol2/job8/publication-layout.raw.txt)

## What I am not sure about

The gain on the owner PC remains unknown. Deployment with multiple workers depends on the locked paths named above. The timing trace covers game and ply indices, best moves, last-info nodes and last-info scores. Internal node visitation order is outside its coverage.
