# VERIFY t19

Branch `grok47/t19-wide-net-parity` at `d5e60c9dcbabff4fe6a16a095f5ed0bb8d9bc92e`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Previously checked commit `d133b998a15fe0829062f19c2c3a4d0e7cf1b1ec`.
Verdict: **FIX NEEDED**.

## Rule check

`git diff --name-status 16833ecc...d5e60c9d`:

```
M	forge-combo29/CMakeLists.txt
A	forge-combo29/REPORT_t19.md
M	forge-combo29/src/nnue.cpp
A	forge-combo29/tests_t19/eval_parity.cpp
A	forge-combo29/tests_t19/nnue_weights_512.inc
A	forge-combo29/tests_t19/wide_eval.cpp
A	forge-combo29/tests_t19/wide_eval.hpp
A	forge-combo29/tests_t19/widen_nnue.cpp
```

New files are mode 100644. No executable, archive, script, workflow, or Python file is in the diff. Engine source is `src/nnue.cpp`, 6 insertions and 1 deletion. The commit since `d133b998` changes only `REPORT_t19.md`, `tests_t19/eval_parity.cpp`, and `tests_t19/widen_nnue.cpp`.

Outside the allowed set: `forge-combo29/CMakeLists.txt` (3 insertions, 1 deletion). `src/nnue.cpp` includes a test file when the macro is 512:

```
#if FORGE_NNUE_HIDDEN == 512
#include "../tests_t19/nnue_weights_512.inc"
#define FORGE_HAS_NNUE 1
#elif __has_include("nnue_weights.inc")
```

`src/nnue.cpp` lines 31-34. The default in `CMakeLists.txt` is still 256 (`CMakeLists.txt:20` and the `FORGE_NNUE_HIDDEN=${FORGE_NNUE_HIDDEN}` definition at line 28).

## Safety

No network use, process start, registry or environment access, or obfuscated code. `widen_nnue` writes the path it is given, after refusing the lock weights file and an output that is the same file as the input (`tests_t19/widen_nnue.cpp:132-134` and `:170`):

```
if (is_lock_weights(output_path) || same_target(input_path, output_path)) {
    std::cerr << "widen_nnue: refusing to overwrite the lock weights\n";
    return 2;
}
```

```
std::ofstream out(output_path, std::ios::binary);
```

The parity test does not write a file. The converter write is the widened net the test checks. This run wrote that file under `/tmp`, not into `src/`.

## Build

Clang 18.1.3 failed the stated cmake line with `cannot find -lstdc++` (see VERIFY_t12.md). Default g++ 13.3.0 Release and ASan/UBSan, `FORGE_NNUE_HIDDEN` left at 256:

```
cmake -S /tmp/wt-t19/forge-combo29 -B /tmp/wt-t19/build_rel -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/wt-t19/build_rel -j
cmake -S /tmp/wt-t19/forge-combo29 -B /tmp/wt-t19/build_san -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g"
cmake --build /tmp/wt-t19/build_san -j
```

Both ended `Built target forge` and `BUILD_EXIT:0`.

A third release build:

```
cmake -S /tmp/wt-t19/forge-combo29 -B /tmp/wt-t19/build_512 -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DFORGE_NNUE_HIDDEN=512
cmake --build /tmp/wt-t19/build_512 -j2
```

`BUILD_EXIT:0`. `flags.make` contains `-DFORGE_NNUE_HIDDEN=512`. Portable flags were not added. This machine has `avx512f`.

## Pins

Default 256, Threads 1, Hash 16, OwnBook false:

```
info string bench depth 11 nodes 312866 time 160 nps 1955412
info string bench depth 13 nodes 862329 time 423 nps 2038602
nodes 4865609
```

512 release build, same options:

```
info string bench depth 11 nodes 312866 time 185 nps 1691167
info string bench depth 13 nodes 862329 time 498 nps 1731584
nodes 4865609
```

Both exit 0. The lock release binary printed the same three counts.

## Task test

`widen_nnue` was compiled with `-std=c++20 -O1 -fsanitize=address,undefined -fno-omit-frame-pointer -g`.

```
/tmp/tests/widen_nnue /tmp/wt-t19/forge-combo29/src/nnue_weights.inc /tmp/wt-t19/forge-combo29/src/nnue_weights.inc
/tmp/tests/widen_nnue /tmp/wt-t19/forge-combo29/src/nnue_weights.inc /tmp/wt-t19/forge-combo29/src/../src/nnue_weights.inc
/tmp/tests/widen_nnue /tmp/wt-t19/forge-combo29/src/nnue_weights.inc /tmp/nnue_weights_lock_link.inc
```

Each printed `widen_nnue: refusing to overwrite the lock weights` and exited 2. The third path was a symlink to `src/nnue_weights.inc`.

```
/tmp/tests/widen_nnue /tmp/wt-t19/forge-combo29/src/nnue_weights.inc /tmp/nnue_weights_512_review.inc
```

```
padding_zeros w1=196608 b1=256 w2=512
fingerprint w1=6227214367631889344 b1=10979643604819931428 w2=11500908642059936499
```

Exit 0. `cmp` against `tests_t19/nnue_weights_512.inc` exited 0. SHA-256:

```
a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638  src/nnue_weights.inc
ee99040640a1906c8f98f6e29a9d7c4d825cb6c42718362646ab9fea3746a4e5  /tmp/nnue_weights_512_review.inc
ee99040640a1906c8f98f6e29a9d7c4d825cb6c42718362646ab9fea3746a4e5  tests_t19/nnue_weights_512.inc
```

`eval_parity` was linked two ways. Both used a sanitizer `nnue.cpp` built with `-DFORGE_NNUE_HIDDEN=512 -Dnnue=nnue512`, plus `wide_eval.cpp`. One link used this commit's 256 sanitizer objects. The other used the lock's 256 sanitizer objects. `ASAN_OPTIONS=detect_leaks=0`. Both printed the same block and exited 0. Stderr was 0 bytes. No sanitizer diagnostic.

```
seed 20261110
positions 100000
unique 98914
resets 310
make_failures 0
residual_256 1
residual_512 1
start_static_256 38
start_static_512 38
static_equal 100000
static_differ 0
static_max_abs_diff 0
network_differ 0
network_max_abs_diff 0
hash_static_256 13290400224059203287
hash_static_512 13290400224059203287
```

The new `network_differ != 0` failure check therefore passes on the lock objects as well. The test does not fail on the base.

## Report claims

Reproduced on this commit: default pins, 512-build pins, `padding_zeros w1=196608 b1=256 w2=512`, the three fingerprints, refusal of the lock path, the `../src` spelling, and a symlink, `cmp` with the stored 512 net, lock SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`, and 100000 equal static and network evals with hash `13290400224059203287` and `network_differ 0`. The same parity numbers came from the lock's 256 objects.

Not run: a portable `-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3` 512 build, a Clang configure with `--gcc-install-dir`, and the Windows lock recipe. The report's bench times were not compared. No Elo or speed claim was checked.

## What to fix

Keep the widened net and the parity test under `tests_t19/`. Do not change `CMakeLists.txt`, and do not `#include` `tests_t19` from `src/nnue.cpp`. The 512 translation unit already builds from the test with `-DFORGE_NNUE_HIDDEN=512`. The parity test still passes when the 256 side is the lock.
