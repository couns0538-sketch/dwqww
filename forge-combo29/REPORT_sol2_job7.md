# sol2 — Job 7 GCC LTO and PGO speed comparison

## Step 0 — frozen build and node gates passed

On the frozen GCC Release r15d, the fresh-process gates returned **312,866** nodes for `bench 11`, **862,329** for `bench 13` and **4,865,609** for startpos perft 5. These gates used embedded AL1 s198 with UseNNUE true, Threads 1, Hash 16 MiB, MultiPV 1 and OwnBook false. [Raw commands and outputs](sol2/job7/step0-r15d-pins.raw.txt)

| GCC Release build | SHA-256 |
|---|---|
| r15d | `bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6` |
| k10 | `55fed57fadf76d5e861da3f9bf3601b43c6bf67e6d152d87edfcf648e26207ae` |
| k11 | `a7a34a148b40c14e5ea960dd2d3182fceef7023a38d12db47c2521a430fc1ea5` |
| k11v | `a9d4eef3de37cf74611c59a2f35b64f205cf95b7463e65554271e64d1ce01c80` |

r15d, k10 and k11 match the Job 6 hashes. For k11v I cloned the k11 scratch tree and applied Carbon2's archived `12_v3_refresh_fuse.patch.txt` from commit `8a70ec514de022e6873c55b8ae29529f2c5f763e` with `patch -p1 -F0`. The patch SHA-256 was `7989b1954ec7a101473c7da05ef9e0f3506a29866e21783a8de31044a367e65f`. The application completed with zero offsets, fuzz or rejects. This is Carbon2's NNUE refresh change on top of k11. Job 5's k12 used a different patch. [Frozen build receipts](sol2/job7/step0-frozen-identities.raw.txt) · [Patch source](sol2/job7/step0-patch-source.raw.txt) · [Patch command](sol2/job7/step0-command.raw.txt) · [k11v build](sol2/job7/step0-k11v-build.raw.txt)

With PC20 sent first and synthetic net768 loaded, fresh processes of **r15d**, **k11** and **k11v** all returned **882,074** for `bench 11` and **4,275,906** for `bench 13`. The raw setups use Threads 1, Hash 16 MiB, OwnBook false and default MultiPV 1. [r15d raw](sol2/job7/step0-r15d-net768.raw.txt) · [k11 raw](sol2/job7/step0-k11-net768.raw.txt) · [k11v raw](sol2/job7/step0-k11v-net768.raw.txt)

## Prediction graded

The prediction was published alone at `a4ccd4b5aed6c6f434083922b4bd11a10089e766` after Step 0 and before the PGO builds.

| Quantity | Prediction | Observed | Grade |
|---|---:|---:|---|
| Identical-binary CPU minimum | 0.970 | 0.9921 | Minimum higher by 0.0221 |
| Identical-binary CPU maximum | 1.045 | 1.0517 | Maximum higher by 0.0067 |
| Pooled k11-pgo/r15d-pgo CPU | 0.965 | 0.9392 | CPU ratio lower by 0.0258 |
| k11-pgo/r15d-pgo CPU blocks below one | 11/12 | 12/12 | One more block below one |
| Pooled k11v-pgo/k11-pgo CPU | 0.987 | 0.9726 | Absolute ratio error 0.0144 |

[Original prediction](sol2/job7/prediction.txt) · [UTC checkpoints](sol2/job7/stamps.txt)

## Step 1 — three separately trained builds passed identity

Compiler and libraries were GCC 14.2.0 (Debian 14.2.0-19), libstdc++ 6.0.33 and glibc 2.41. Job 6's CMake Release recipe selected C++20, `-O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4`, and the existing build definitions including v3, ZMM and the mate-alpha guard. Each arm got `-flto` and its own absolute directory for GCC counters, first using `-fprofile-generate` at compile and link time. After training once, each arm was reconfigured in the same build directory and rebuilt with `--clean-first`, using `-fprofile-use`, `-Werror=missing-profile` and `-Werror=coverage-mismatch`. Full expanded compiler and linker commands are in the build logs. Each counter inventory recorded one run and the counter hashes matched before and after the rebuild and holdout run. [Build script](sol2/job7/step1_build.sh.txt) · [r15d commands](sol2/job7/r15d-step1-command.raw.txt) · [k11 commands](sol2/job7/k11-step1-command.raw.txt) · [k11v commands](sol2/job7/k11v-step1-command.raw.txt)

| PGO build | SHA-256 | Profile workload searches / last-info nodes / trace | Held-out workload searches / last-info nodes / trace |
|---|---|---|---|
| r15d-pgo | `96f50b3eb6d4f05cfa8291eaab56ea9c943a8e98fb3b248fff3b9138fcce6808` | 2,482 / 8,391,013 / `c7d9520ffe04deda` | 8,612 / 29,333,343 / `5c705841c3ea17b4` |
| k11-pgo | `18cef37b7215446b25f40854fb2d41b06ca474e448f9be91f9f4ca12174b0275` | 2,482 / 8,391,013 / `c7d9520ffe04deda` | 8,612 / 29,333,343 / `5c705841c3ea17b4` |
| k11v-pgo | `95980ac637b41376245996617d537fd38ef54f223cc93f13673915bfb6f3079c` | 2,482 / 8,391,013 / `c7d9520ffe04deda` | 8,612 / 29,333,343 / `5c705841c3ea17b4` |

Both workloads used the pinned Carbon2 startpos driver SHA-256 `c79b95bf45762fa9869d23140ed7f946cfaf0cb6bc4f74325a18d5f934bf1c45`, PC20, Threads 1, Hash 16 MiB, OwnBook false, and synthetic v3 net768 SHA-256 `c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7`. They used `go softnodes 2000`, eight opening plies and an engine-play limit of 300 plies. The 20 profile games used seed `20261118`. The 60 identity and timing games used seed `20261117`. Across those opening sets each arm had zero shared eight-ply move vectors and zero shared post-opening keys of placement, side to move and castling rights. [PGO executable hashes](sol2/job7/pgo-executables.raw.txt) · [Opening-independence receipt](sol2/job7/opening-independence.raw.txt)

## Steps 2–4 — timing and decision

Each ABBA block divided the sum of the two B times by the sum of the two A times. The pooled ratio used all included times in each arm. The predeclared rule called a difference measured when the block median was outside the entire six-block identical-binary range and at least 10 of 12 ratios were on the same side of one. Engine CPU is the reaped Forge process's user plus system time. Wall covers the full driver call. The driver and each fresh engine were pinned to logical CPU 2. The Step 2 control used two different executable paths, identical by SHA-256 and byte-for-byte by `cmp`. [Control copy](sol2/job7/step2-copy.raw.txt) · [Timing harness](sol2/job7/abba_timing.py.txt) · [Independent readback](sol2/job7/timing_readback.py.txt)

All tables use PC20, Threads 1, Hash 16 MiB, net768, seed 20261117 and `go softnodes 2000`. Each eligible run records 8,612 searches, 29,333,343 nodes and trace `5c705841c3ea17b4`.

### Step 2 — identical-binary ABBA floor

B/A compares `copy` (`96f50b3eb6d4f05cfa8291eaab56ea9c943a8e98fb3b248fff3b9138fcce6808`) with `r15d-pgo` (`96f50b3eb6d4f05cfa8291eaab56ea9c943a8e98fb3b248fff3b9138fcce6808`).

| Block | Leg | Engine | CPU (s) | Wall (s) | Trace | Exit | Included |
|---:|---:|---|---:|---:|---|---:|---|
| 1 | 1 | r15d-pgo | 19.386 | 20.169 | `5c705841c3ea17b4` | 0 | yes |
| 1 | 2 | copy | 19.113 | 19.902 | `5c705841c3ea17b4` | 0 | yes |
| 1 | 3 | copy | 20.012 | 20.814 | `5c705841c3ea17b4` | 0 | yes |
| 1 | 4 | r15d-pgo | 19.953 | 20.797 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 1 | r15d-pgo | 19.143 | 19.927 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 2 | copy | 19.063 | 19.836 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 3 | copy | 18.932 | 19.724 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 4 | r15d-pgo | 18.863 | 19.614 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 1 | r15d-pgo | 19.032 | 19.786 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 2 | copy | 18.837 | 19.585 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 3 | copy | 19.545 | 20.379 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 4 | r15d-pgo | 19.248 | 20.044 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 1 | r15d-pgo | 19.960 | 20.804 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 2 | copy | 19.474 | 20.264 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 3 | copy | 19.273 | 20.059 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 4 | r15d-pgo | 19.096 | 19.867 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 1 | r15d-pgo | 19.334 | 20.136 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 2 | copy | 20.619 | 21.505 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 3 | copy | 20.048 | 20.890 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 4 | r15d-pgo | 19.335 | 20.131 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 1 | r15d-pgo | 20.010 | 20.853 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 2 | copy | 19.665 | 20.455 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 3 | copy | 19.396 | 20.183 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 4 | r15d-pgo | 18.604 | 19.333 | `5c705841c3ea17b4` | 0 | yes |

| Block | B/A CPU | B/A wall |
|---:|---:|---:|
| 1 | 0.9945 | 0.9939 |
| 2 | 0.9997 | 1.0005 |
| 3 | 1.0027 | 1.0033 |
| 4 | 0.9921 | 0.9915 |
| 5 | 1.0517 | 1.0528 |
| 6 | 1.0116 | 1.0112 |

| Metric | Median | Pooled | Block range | Below 1 | Above 1 | Reading |
|---|---:|---:|---:|---:|---:|---|
| Engine CPU | 1.0012 | 1.0087 | 0.9921–1.0517 | 3/6 | 3/6 | Identical-binary floor |
| Wall | 1.0019 | 1.0088 | 0.9915–1.0528 | 2/6 | 4/6 | Identical-binary floor |

[Raw runs](sol2/job7/step2/runs.jsonl.txt) · [Summary](sol2/job7/step2/summary.txt) · [Command](sol2/job7/step2-command.raw.txt)

### Step 3 — k11-pgo against r15d-pgo

B/A compares `k11-pgo` (`18cef37b7215446b25f40854fb2d41b06ca474e448f9be91f9f4ca12174b0275`) with `r15d-pgo` (`96f50b3eb6d4f05cfa8291eaab56ea9c943a8e98fb3b248fff3b9138fcce6808`).

| Block | Leg | Engine | CPU (s) | Wall (s) | Trace | Exit | Included |
|---:|---:|---|---:|---:|---|---:|---|
| 1 | 1 | r15d-pgo | 18.679 | 19.419 | `5c705841c3ea17b4` | 0 | yes |
| 1 | 2 | k11-pgo | 17.729 | 18.485 | `5c705841c3ea17b4` | 0 | yes |
| 1 | 3 | k11-pgo | 17.747 | 18.501 | `5c705841c3ea17b4` | 0 | yes |
| 1 | 4 | r15d-pgo | 21.583 | 22.523 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 1 | r15d-pgo | 21.655 | 22.602 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 2 | k11-pgo | 19.853 | 20.741 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 3 | k11-pgo | 19.655 | 20.534 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 4 | r15d-pgo | 20.323 | 21.183 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 1 | r15d-pgo | 20.458 | 21.324 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 2 | k11-pgo | 19.433 | 20.286 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 3 | k11-pgo | 19.546 | 20.416 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 4 | r15d-pgo | 21.019 | 21.922 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 1 | r15d-pgo | 20.682 | 21.556 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 2 | k11-pgo | 18.101 | 18.866 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 3 | k11-pgo | 17.345 | 18.072 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 4 | r15d-pgo | 18.091 | 18.803 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 1 | r15d-pgo | 18.531 | 19.276 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 2 | k11-pgo | 17.628 | 18.371 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 3 | k11-pgo | 18.159 | 18.903 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 4 | r15d-pgo | 18.860 | 19.625 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 1 | r15d-pgo | 18.906 | 19.667 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 2 | k11-pgo | 18.670 | 19.452 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 3 | k11-pgo | 17.912 | 18.644 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 4 | r15d-pgo | 20.869 | 21.754 | `5c705841c3ea17b4` | 0 | yes |
| 7 | 1 | r15d-pgo | 19.791 | 20.585 | `5c705841c3ea17b4` | 0 | yes |
| 7 | 2 | k11-pgo | 19.121 | 19.919 | `5c705841c3ea17b4` | 0 | yes |
| 7 | 3 | k11-pgo | 19.089 | 19.891 | `5c705841c3ea17b4` | 0 | yes |
| 7 | 4 | r15d-pgo | 18.568 | 19.336 | `5c705841c3ea17b4` | 0 | yes |
| 8 | 1 | r15d-pgo | 17.843 | 18.543 | `5c705841c3ea17b4` | 0 | yes |
| 8 | 2 | k11-pgo | 17.171 | 17.888 | `5c705841c3ea17b4` | 0 | yes |
| 8 | 3 | k11-pgo | 17.569 | 18.284 | `5c705841c3ea17b4` | 0 | yes |
| 8 | 4 | r15d-pgo | 18.748 | 19.527 | `5c705841c3ea17b4` | 0 | yes |
| 9 | 1 | r15d-pgo | 19.629 | 20.443 | `5c705841c3ea17b4` | 0 | yes |
| 9 | 2 | k11-pgo | 18.256 | 19.065 | `5c705841c3ea17b4` | 0 | yes |
| 9 | 3 | k11-pgo | 17.162 | 17.859 | `5c705841c3ea17b4` | 0 | yes |
| 9 | 4 | r15d-pgo | 18.962 | 19.754 | `5c705841c3ea17b4` | 0 | yes |
| 10 | 1 | r15d-pgo | 18.037 | 18.745 | `5c705841c3ea17b4` | 0 | yes |
| 10 | 2 | k11-pgo | 17.830 | 18.585 | `5c705841c3ea17b4` | 0 | yes |
| 10 | 3 | k11-pgo | 18.481 | 19.253 | `5c705841c3ea17b4` | 0 | yes |
| 10 | 4 | r15d-pgo | 20.088 | 20.926 | `5c705841c3ea17b4` | 0 | yes |
| 11 | 1 | r15d-pgo | 19.968 | 20.781 | `5c705841c3ea17b4` | 0 | yes |
| 11 | 2 | k11-pgo | 18.182 | 18.952 | `5c705841c3ea17b4` | 0 | yes |
| 11 | 3 | k11-pgo | 18.238 | 19.005 | `5c705841c3ea17b4` | 0 | yes |
| 11 | 4 | r15d-pgo | 18.635 | 19.373 | `5c705841c3ea17b4` | 0 | yes |
| 12 | 1 | r15d-pgo | 18.741 | 19.481 | `5c705841c3ea17b4` | 0 | yes |
| 12 | 2 | k11-pgo | 17.993 | 18.755 | `5c705841c3ea17b4` | 0 | yes |
| 12 | 3 | k11-pgo | 18.479 | 19.263 | `5c705841c3ea17b4` | 0 | yes |
| 12 | 4 | r15d-pgo | 19.133 | 19.907 | `5c705841c3ea17b4` | 0 | yes |

| Block | B/A CPU | B/A wall |
|---:|---:|---:|
| 1 | 0.8811 | 0.8818 |
| 2 | 0.9412 | 0.9426 |
| 3 | 0.9398 | 0.9412 |
| 4 | 0.9142 | 0.9152 |
| 5 | 0.9571 | 0.9582 |
| 6 | 0.9197 | 0.9198 |
| 7 | 0.9961 | 0.9972 |
| 8 | 0.9494 | 0.9501 |
| 9 | 0.9178 | 0.9186 |
| 10 | 0.9524 | 0.9538 |
| 11 | 0.9434 | 0.9453 |
| 12 | 0.9630 | 0.9652 |

| Metric | Median | Pooled | Block range | Below 1 | Above 1 | Reading |
|---|---:|---:|---:|---:|---:|---|
| Engine CPU | 0.9423 | 0.9392 | 0.8811–0.9961 | 12/12 | 0/12 | MEASURED |
| Wall | 0.9440 | 0.9403 | 0.8818–0.9972 | 12/12 | 0/12 | MEASURED |

[Raw runs](sol2/job7/step3/runs.jsonl.txt) · [Summary](sol2/job7/step3/summary.txt) · [Command](sol2/job7/step3-command.raw.txt)

### k11 against r15d with and without GCC LTO and PGO

| Build | Metric | Block median | Pooled B/A | Blocks below 1 | Reading |
|---|---|---:|---:|---:|---|
| Job 6 GCC Release | Engine CPU | 0.9470 | 0.9457 | 12/12 | MEASURED |
| Job 6 GCC Release | Wall | 0.9491 | 0.9469 | 12/12 | MEASURED |
| Job 7 GCC Release with LTO and PGO | Engine CPU | 0.9423 | 0.9392 | 12/12 | MEASURED |
| Job 7 GCC Release with LTO and PGO | Wall | 0.9440 | 0.9403 | 12/12 | MEASURED |

The two sessions used separate identical-binary ABBA floors. The second session changes both LTO and PGO. [Job 6 raw comparison](sol2/job6/step2/runs.jsonl.txt) · [Job 7 raw comparison](sol2/job7/step3/runs.jsonl.txt)

### Step 4 — k11v-pgo against k11-pgo

B/A compares `k11v-pgo` (`95980ac637b41376245996617d537fd38ef54f223cc93f13673915bfb6f3079c`) with `k11-pgo` (`18cef37b7215446b25f40854fb2d41b06ca474e448f9be91f9f4ca12174b0275`).

| Block | Leg | Engine | CPU (s) | Wall (s) | Trace | Exit | Included |
|---:|---:|---|---:|---:|---|---:|---|
| 1 | 1 | k11-pgo | 17.671 | 18.393 | `5c705841c3ea17b4` | 0 | yes |
| 1 | 2 | k11v-pgo | 18.201 | 18.964 | `5c705841c3ea17b4` | 0 | yes |
| 1 | 3 | k11v-pgo | 17.903 | 18.657 | `5c705841c3ea17b4` | 0 | yes |
| 1 | 4 | k11-pgo | 19.059 | 19.904 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 1 | k11-pgo | 19.016 | 19.851 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 2 | k11v-pgo | 17.276 | 18.009 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 3 | k11v-pgo | 17.349 | 18.084 | `5c705841c3ea17b4` | 0 | yes |
| 2 | 4 | k11-pgo | 18.002 | 18.777 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 1 | k11-pgo | 20.134 | 21.035 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 2 | k11v-pgo | 19.194 | 20.056 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 3 | k11v-pgo | 19.358 | 20.208 | `5c705841c3ea17b4` | 0 | yes |
| 3 | 4 | k11-pgo | 20.103 | 21.001 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 1 | k11-pgo | 17.791 | 18.534 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 2 | k11v-pgo | 17.446 | 18.190 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 3 | k11v-pgo | 18.550 | 19.331 | `5c705841c3ea17b4` | 0 | yes |
| 4 | 4 | k11-pgo | 18.734 | 19.548 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 1 | k11-pgo | 19.279 | 20.096 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 2 | k11v-pgo | 18.946 | 19.744 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 3 | k11v-pgo | 18.831 | 19.636 | `5c705841c3ea17b4` | 0 | yes |
| 5 | 4 | k11-pgo | 18.334 | 19.107 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 1 | k11-pgo | 18.287 | 19.075 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 2 | k11v-pgo | 17.496 | 18.247 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 3 | k11v-pgo | 18.069 | 18.845 | `5c705841c3ea17b4` | 0 | yes |
| 6 | 4 | k11-pgo | 18.576 | 19.393 | `5c705841c3ea17b4` | 0 | yes |
| 7 | 1 | k11-pgo | 19.006 | 19.839 | `5c705841c3ea17b4` | 0 | yes |
| 7 | 2 | k11v-pgo | 17.063 | 17.770 | `5c705841c3ea17b4` | 0 | yes |
| 7 | 3 | k11v-pgo | 17.972 | 18.738 | `5c705841c3ea17b4` | 0 | yes |
| 7 | 4 | k11-pgo | 18.016 | 18.775 | `5c705841c3ea17b4` | 0 | yes |
| 8 | 1 | k11-pgo | 18.467 | 19.251 | `5c705841c3ea17b4` | 0 | yes |
| 8 | 2 | k11v-pgo | 18.097 | 18.867 | `5c705841c3ea17b4` | 0 | yes |
| 8 | 3 | k11v-pgo | 16.903 | 17.603 | `5c705841c3ea17b4` | 0 | yes |
| 8 | 4 | k11-pgo | 17.660 | 18.397 | `5c705841c3ea17b4` | 0 | yes |
| 9 | 1 | k11-pgo | 19.213 | 20.040 | `5c705841c3ea17b4` | 0 | yes |
| 9 | 2 | k11v-pgo | 18.358 | 19.139 | `5c705841c3ea17b4` | 0 | yes |
| 9 | 3 | k11v-pgo | 17.673 | 18.426 | `5c705841c3ea17b4` | 0 | yes |
| 9 | 4 | k11-pgo | 17.857 | 18.608 | `5c705841c3ea17b4` | 0 | yes |
| 10 | 1 | k11-pgo | 17.832 | 18.588 | `5c705841c3ea17b4` | 0 | yes |
| 10 | 2 | k11v-pgo | 17.769 | 18.533 | `5c705841c3ea17b4` | 0 | yes |
| 10 | 3 | k11v-pgo | 17.575 | 18.331 | `5c705841c3ea17b4` | 0 | yes |
| 10 | 4 | k11-pgo | 18.343 | 19.137 | `5c705841c3ea17b4` | 0 | yes |
| 11 | 1 | k11-pgo | 17.888 | 18.644 | `5c705841c3ea17b4` | 0 | yes |
| 11 | 2 | k11v-pgo | 17.628 | 18.387 | `5c705841c3ea17b4` | 0 | yes |
| 11 | 3 | k11v-pgo | 17.605 | 18.361 | `5c705841c3ea17b4` | 0 | yes |
| 11 | 4 | k11-pgo | 17.490 | 18.239 | `5c705841c3ea17b4` | 0 | yes |
| 12 | 1 | k11-pgo | 17.470 | 18.201 | `5c705841c3ea17b4` | 0 | yes |
| 12 | 2 | k11v-pgo | 18.159 | 18.915 | `5c705841c3ea17b4` | 0 | yes |
| 12 | 3 | k11v-pgo | 17.488 | 18.227 | `5c705841c3ea17b4` | 0 | yes |
| 12 | 4 | k11-pgo | 18.817 | 19.615 | `5c705841c3ea17b4` | 0 | yes |

| Block | B/A CPU | B/A wall |
|---:|---:|---:|
| 1 | 0.9830 | 0.9824 |
| 2 | 0.9353 | 0.9344 |
| 3 | 0.9581 | 0.9578 |
| 4 | 0.9855 | 0.9853 |
| 5 | 1.0043 | 1.0045 |
| 6 | 0.9648 | 0.9642 |
| 7 | 0.9463 | 0.9455 |
| 8 | 0.9688 | 0.9687 |
| 9 | 0.9720 | 0.9720 |
| 10 | 0.9770 | 0.9772 |
| 11 | 0.9959 | 0.9963 |
| 12 | 0.9824 | 0.9822 |

| Metric | Median | Pooled | Block range | Below 1 | Above 1 | Reading |
|---|---:|---:|---:|---:|---:|---|
| Engine CPU | 0.9745 | 0.9726 | 0.9353–1.0043 | 11/12 | 1/12 | MEASURED |
| Wall | 0.9746 | 0.9723 | 0.9344–1.0045 | 11/12 | 1/12 | MEASURED |

[Raw runs](sol2/job7/step4/runs.jsonl.txt) · [Summary](sol2/job7/step4/summary.txt) · [Command](sol2/job7/step4-command.raw.txt)

## Facts

- All 120 timing passes exited cleanly and matched the 60-game PC20/net768 signature of 8,612 searches, 29,333,343 last-info nodes and trace `5c705841c3ea17b4`. The independent readback reconciled the raw driver records, executable and workload hashes, and both estimators. [Readback script](sol2/job7/timing_readback.py.txt)
- For the GCC LTO+PGO builds, k11 used **6.08% less engine CPU** and **5.97% less wall time** pooled against r15d. Both metrics met the rule with 12/12 blocks below one. The corresponding Job 6 unprofiled CPU reduction was 5.43%. [Job 6 report](REPORT_sol2_job6.md)
- The additional Carbon2 refresh patch on k11v-pgo used **2.74% less engine CPU** pooled against k11-pgo. The predeclared readings were **MEASURED** for CPU and **MEASURED** for wall. [Step 4 summary](sol2/job7/step4/summary.txt)
- GitHub CLI authentication returned HTTP 401 during Step 1 publication. I used the authorized GitHub connector for subsequent checkpoints, confirmed each remote tree SHA matched the local tree, and updated only the expected current head of `for-fable-and-opus/sol2-work` with force disabled. [UTC checkpoints](sol2/job7/stamps.txt) · [Publication layout](sol2/job7/publication-layout.raw.txt)

## Suspicions

The smaller pooled k11/r15d CPU ratio in Job 7 could reflect compiler optimization, host drift, or both. LTO and PGO changed together, and each session used its own noise control. This design establishes an advantage within each session. It leaves the change in advantage between sessions unresolved.

## What I did not do

The experiments used scratch Linux builds and the synthetic net. The owner's Windows Clang ThinLTO build, production training throughput, and match strength were outside the experimental scope. The branch contains text evidence and the archived diff.

## What I am not sure about

The PC gain remains unknown. The timing signature covers the pinned driver's game and ply indices, best moves, last-info scores and last-info node counts. Internal node order is beyond that signature's coverage.
