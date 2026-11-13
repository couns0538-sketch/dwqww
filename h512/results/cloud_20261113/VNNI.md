# AVX-512 VNNI output sum, kept when the compiler enables it

Date: 2026-11-13. This is a bit-exact change to the NNUE v3 output sum. It is not an Elo result.

## What changed

`output_sum_avx512` computes each SCReLU term as `vpmullw` of the clamped activation by `w2`, then `vpmaddwd`, then `vpaddd` into the lane. GCC 13 does not turn that sequence into `vpdpwssd` even with `-mavx512vnni` or `-march=znver4`. The new kernel writes `_mm512_dpwssd_epi32` for that madd-and-add.

The product stays inside int16: the activation is clamped to 0..255 and the loader rejects `|w2| > 127`, so `255 * 127 = 32385`. `vpdpwssd` adds the same pairwise products into the same int32 lanes. The int64 reduction is unchanged.

`output_sum` calls the VNNI kernel only when `__AVX512VNNI__` is defined. `-march=x86-64-v4` does not define it, so the CMake default stays on the madd kernel. This machine's g++ 13.3.0 and clang 18.1.3 have no `-march=znver5`. `-march=znver4` does define `__AVX512VNNI__`. A lock build that passes `-march=znver5` on a compiler that accepts that name gets the same macro.

## Source and binaries

- Branch: `cursor/forge-nnue-eval-20261113-22cc`, cut from `fable/standalone-h512-20261111` @ `efb2ff960037087299332bc6a44baea69441a17a`.
- Compiler for the timed objects: g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0.
- Flags: `-std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4 -mavx512vnni -DNDEBUG` and the same `FORGE_*` defines as `REFRESH_BIAS.md`.
- CPU: Intel Xeon family 6 model 207, 4 cores, `avx512_vnni` present. Output-sum loops pinned with `taskset -c 1`. Bench was not pinned. Not Zen 5, not ThinLTO, not PGO.
- Objects stayed in `/tmp/forge-nnue-build` and are not in git.
- VNNI `nnue_v3.o` sha256 `83c7090d8b42d7e54409239f14544fbfac181d0a549d2811ca6563c652f1e613`. Its `output_sum` is `vpmullw` then `vpdpwssd` for both perspectives.
- Portable v4 `nnue_v3.o` sha256 `8f498bfe2d16bd0abc0e3e8679433bd59e9a2dc23cb0e31b050443c695c8eb22`. Its `output_sum` is `vpmullw` then `vpmaddwd`. No `vpdpwssd` in the object.
- Speed tool sha256 `2c882c27522867ab2a5837806a414416ef45f181d00810869447c4a4373c9820`.
- Test exe, VNNI, sha256 `16c42614dfd3045c168effb5da0814381dc5b7557be319a112bd63f9a35b2003`.
- Test exe, v4, sha256 `4438c69f924c790d6405c17275b5a36a2c6266179634762570a75e6d877e2b9f`.
- Diag exe, VNNI, sha256 `492d14148540f94e2aca1612594ff18718cd4aced89584d4059df6ac6368fd22`.
- Diag exe, madd (the refresh build), sha256 `9eb5acc253d9f5bb3f4ec9bf9a5c289b76ac2702d755520fa975ef1c74adbfc5`.

Nets, already on disk from the parity run, not committed:

- H512 sha256 `80a533839051d08a3f6da51712ce6bf16a0c57a349fef573e9af2a4d28753d44`, checksum `b79d7c52a35b3ab5`.
- H1024 sha256 `97dfffa70e2c458d3f3c6a73ea6f45df2584ac8c36f3beaed08def9c6e28d755`, checksum `fd4052a28027225c`.

## Correctness

`forge_nnue_v3_tests` `/tmp/forge-nnue-vnni-scratch` and `/tmp/forge-nnue-v4-scratch`, 100000 plies:

- Both: 95960 checks, 0 failures. Walk totals match `h512/results/step3/nnue_v3_tests_combo29.log` (100000 plies, 64987 evaluations, 0 mismatches).
- v4 kernel line is that log's line: `kernel_checks 129974`, kernels `scalar, avx2, avx512`, best kernel `avx512`, 1200 bound sums.
- VNNI build adds the fourth kernel: `kernel_checks 194961`, best kernel `avx512-vnni`, 1600 bound sums, 0 kernel mismatches. The bound set includes accumulators at `32767` and `-32768` with `w2` at `±127`.

Search nodes, same nets, `NNUEArch` true, `Searcher(16)` inside `bench`. Madd diag and VNNI diag:

| Net | Depth | Nodes, both exes |
|---|---:|---:|
| H512 mirrored, 8 king buckets | 12 | 309106 |
| H512 mirrored, 8 king buckets | 16 | 21116907 |
| H1024, 1 king bucket | 8 | 27556 |

Those are the same counts as `REFRESH_BIAS.md`.

## Output-sum time

The speed tool times every compiled kernel through `output_sum_with`. The selector is a volatile int, so the switch is not compiled into one kernel. 200000 calls per pass, five passes, one start-position accumulator. Sums matched across scalar, AVX2, AVX-512, and AVX-512 VNNI: H512 `4558683`, H1024 `-982680`.

Pinned H512, nanoseconds per `output_sum_with`. Run 1 starts cold. Runs 2 and 3 are the steady pairs.

| Run | pass | avx512 | avx512-vnni |
|---:|---:|---:|---:|
| 1 | 0 | 33.398 | 30.838 |
| 1 | 1 | 33.298 | 31.842 |
| 1 | 2 | 34.428 | 31.286 |
| 1 | 3 | 33.393 | 25.905 |
| 1 | 4 | 24.642 | 23.505 |
| 2 | 0 | 23.977 | 23.187 |
| 2 | 1 | 24.226 | 22.365 |
| 2 | 2 | 24.734 | 22.474 |
| 2 | 3 | 23.903 | 22.905 |
| 2 | 4 | 24.552 | 22.446 |
| 3 | 0 | 23.942 | 22.912 |
| 3 | 1 | 23.911 | 22.976 |
| 3 | 2 | 24.423 | 22.408 |
| 3 | 3 | 23.949 | 22.943 |
| 3 | 4 | 23.957 | 22.960 |

Steady H512 (runs 2 and 3): avx512 23.903 to 24.734, VNNI 22.365 to 22.976. The ranges do not overlap. The direct `output_sum` after the hot path was switched, two later pinned runs: 21.547 and 21.744, sum still `4558683`. Before the switch the direct madd call on the warm runs was 24.720 and 24.485.

Pinned H1024, same tool:

| Run | pass | avx512 | avx512-vnni |
|---:|---:|---:|---:|
| 1 | 0 | 46.008 | 43.375 |
| 1 | 1 | 45.718 | 43.343 |
| 1 | 2 | 46.019 | 43.032 |
| 1 | 3 | 45.766 | 43.206 |
| 1 | 4 | 45.735 | 43.206 |
| 2 | 0 | 45.237 | 43.218 |
| 2 | 1 | 45.522 | 43.106 |
| 2 | 2 | 45.421 | 43.322 |
| 2 | 3 | 45.366 | 42.926 |
| 2 | 4 | 45.653 | 43.130 |
| 3 | 0 | 45.533 | 43.605 |
| 3 | 1 | 45.381 | 43.288 |
| 3 | 2 | 46.082 | 43.183 |
| 3 | 3 | 45.350 | 43.835 |
| 3 | 4 | 45.998 | 44.018 |

H1024 ranges do not overlap (avx512 45.237 to 46.082, VNNI 42.926 to 44.018). Direct `output_sum` after the switch: 41.471 and 41.264, sum still `-982680`. Warm direct madd calls before the switch were 46.530, 46.854, and 47.902.

A later five-pass switch comparison, after the hot path change, stayed in the same direction except one H512 pass where VNNI spiked to 31.665 against avx512 24.741. That pass is noise. The direct-call numbers above are the hot path.

## Bench time, not a speed claim

Depth-16 H512, three runs, nodes 21116907 every time. Milliseconds:

| Exe | times |
|---|---|
| madd diag | 9917, 9597, 9577 |
| VNNI diag | 9427, 9389, 9428 |

The VNNI times sit under the madd times. The closest pair is 149 ms (1.6 percent). `REFRESH_BIAS.md` already recorded a 388 ms gap between two madd runs of this same bench. Three samples on this VM are not a search-NPS result, and they are not an Elo result.

## Clang

Clang 18.1.3 compiles the same file. With `-march=x86-64-v4 -mavx512vnni` it jumps from `output_sum` into `output_sum_avx512_vnni` and emits `vpdpwssd`, then unrolls a second step as `vpmaddwd` plus `vpaddd`. Those two sequences are the same integer sum. The clang objects were not timed. sha256 with VNNI `71154f08a5b6c4456998f1b70a548ac4d2af7cc7cfead21c9966b5e42d97232e`, without `d90017dd4825772cbc8e404863bf3f3c41eabbc87315413d081adf031774c091`. The v4 clang object contains no `vpdpwssd`.

## What this does not say

A faster output sum on a synthetic net is not a stronger engine. Candidate 3 was not loaded. No match was played. Test set 3 was not scored.
