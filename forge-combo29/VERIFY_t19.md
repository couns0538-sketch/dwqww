# VERIFY t19

Branch `grok47/t19-wide-net-parity` at `d133b998a15fe0829062f19c2c3a4d0e7cf1b1ec`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **FIX NEEDED**.

## Rule check

Allowed engine change: `src/nnue.cpp`, 6 insertions, 1 deletion. `tests_t19/` and `REPORT_t19.md` are allowed. All mode 100644. No executable, archive, script, workflow, or Python.

Outside the allowed set: `forge-combo29/CMakeLists.txt` (a `FORGE_NNUE_HIDDEN` cache variable). `src/nnue.cpp` also includes a test file when the macro is 512:

```
#if FORGE_NNUE_HIDDEN == 512
#include "../tests_t19/nnue_weights_512.inc"
```

## Safety

`widen_nnue.cpp` reads `nnue_weights.inc` and writes the path it is given:

```
std::ofstream out(output_path, std::ios::binary);
```

No network, process start, registry, or environment access. The parity test does not write a file.

## Build

Clang configure failed (`cannot find -lstdc++`). Default g++ Release and ASan/UBSan (`FORGE_NNUE_HIDDEN` left at 256) both `Built target forge`.

A second release build with `-DFORGE_NNUE_HIDDEN=512` also `Built target forge`.

## Pins

Default 256:

```
info string bench depth 11 nodes 312866 time 182 nps 1719043
info string bench depth 13 nodes 862329 time 504 nps 1710970
nodes 4865609
```

512 release build, same options:

```
info string bench depth 11 nodes 312866 time 182 nps 1719043
info string bench depth 13 nodes 862329 time 532 nps 1620919
nodes 4865609
```

## Task test

`widen_nnue` compiled and exited 0. It printed `padding_zeros w1=196608 b1=256 w2=512`.

`eval_parity` linked the 256 sanitizer objects of this commit with a second `nnue.cpp` built as `forge::nnue512` (`-DFORGE_NNUE_HIDDEN=512 -Dnnue=nnue512`). Exit 0, no sanitizer report:

```
seed 20261110
positions 100000
static_equal 100000
static_differ 0
static_max_abs_diff 0
start_static_256 38
start_static_512 38
hash_static_256 13290400224059203287
hash_static_512 13290400224059203287
```

The same 512 objects linked to the lock's 256 sanitizer objects printed the same numbers, exit 0. The parity test does not fail on the lock. The 256 engine does not need the CMake or include change for that result.

## Report claims

Reproduced: default pins, 512-build pins, and 100000 equal evals with hash `13290400224059203287` under the AVX-512 build (`-march=x86-64-v4`, `FORGE_SPD_NNUE_ZMM=1`). Not reproduced: a separate portable (`-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`) 512 build. This machine has AVX-512, so that configure was not required. No Elo or speed claim was checked.

## What to fix

Keep the widened net and the parity test under `tests_t19/`. Do not change `CMakeLists.txt`, and do not `#include` `tests_t19` from `src/nnue.cpp`. The 512 translation unit already builds from the test directory with `-DFORGE_NNUE_HIDDEN=512`.
