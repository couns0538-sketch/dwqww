# VERIFY t19

Branch `grok47/t19-wide-net-parity` at `29b90257924de9947ce17486ae4e4f876b74b9d4`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **FIX NEEDED**.

The commit since `d5e60c9d` adds `KRK_FINDINGS.md` only. The engine and the parity test were built and run again.

## Rule check

Files: `CMakeLists.txt`, `KRK_FINDINGS.md`, `REPORT_t19.md`, `src/nnue.cpp`, `tests_t19/eval_parity.cpp`, `nnue_weights_512.inc`, `wide_eval.cpp`, `wide_eval.hpp`, `widen_nnue.cpp`. All mode 100644. No executable, archive, script, workflow, or Python. Engine source is `src/nnue.cpp`, 6 insertions and 1 deletion.

Outside the allowed set: `forge-combo29/CMakeLists.txt` and `forge-combo29/KRK_FINDINGS.md`. `src/nnue.cpp` includes a test file when the macro is 512:

```
src/nnue.cpp:32
#include "../tests_t19/nnue_weights_512.inc"
```

The default in the changed `CMakeLists.txt` is still 256.

## Safety

No network, process start, registry, or environment access. `widen_nnue` writes the path it is given, after refusing the lock weights file and an output that is the same file as the input (`tests_t19/widen_nnue.cpp:170`). The parity test does not write a file. This run wrote `/tmp/nnue_weights_512_review.inc`.

## Build

The stated cmake line without a compiler override failed on the lock tree (`/usr/bin/ld: cannot find -lstdc++: No such file or directory`, Clang 18.1.3). `/proc/cpuinfo` has `avx512f`, so portable march flags were not added. g++ 13.3.0:

```
cmake -S /tmp/wt-t19-wide-net-parity/forge-combo29 -B /tmp/wt-t19-wide-net-parity/build_rel -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/wt-t19-wide-net-parity/build_rel -j4
cmake -S /tmp/wt-t19-wide-net-parity/forge-combo29 -B /tmp/wt-t19-wide-net-parity/build_san -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g"
cmake --build /tmp/wt-t19-wide-net-parity/build_san -j4
```

Both ended `Built target forge`.


A third Release build, hidden size 512:

```
cmake -S /tmp/wt-t19-wide-net-parity/forge-combo29 -B /tmp/wt-t19-wide-net-parity/build_512 -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DFORGE_NNUE_HIDDEN=512
cmake --build /tmp/wt-t19-wide-net-parity/build_512 -j2
```

`flags.make` contains `-DFORGE_NNUE_HIDDEN=512`. The build ended `Built target forge`.

## Pins

Default 256 build:

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/wt-t19-wide-net-parity/build_rel/forge
```

Exit 0.

```
info string bench depth 11 nodes 312866 time 165 nps 1896157
info string bench depth 13 nodes 862329 time 430 nps 2005416
nodes 4865609
```


512 build, same command, exit 0:

```
info string bench depth 11 nodes 312866 time 185 nps 1691167
info string bench depth 13 nodes 862329 time 492 nps 1752701
nodes 4865609
```

## Task test

`widen_nnue` compiled with `-std=c++20 -O1 -fsanitize=address,undefined -fno-omit-frame-pointer -g`.

The lock path, the `../src` spelling, and a symlink to `src/nnue_weights.inc` each printed `widen_nnue: refusing to overwrite the lock weights` and exited 2.

```
/tmp/tests/widen_nnue .../src/nnue_weights.inc /tmp/nnue_weights_512_review.inc
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

`eval_parity` was linked two ways. Both used a sanitizer `nnue.cpp` built with `-DFORGE_NNUE_HIDDEN=512 -Dnnue=nnue512`, plus `wide_eval.cpp`. One link used this commit's 256 sanitizer objects. The other used the lock's 256 sanitizer objects. Both printed the same block and exited 0. Stderr was 0 bytes.

```
positions 100000
static_equal 100000
static_differ 0
network_differ 0
hash_static_256 13290400224059203287
hash_static_512 13290400224059203287
```

The test passes on the lock objects as well. It does not fail on the base.

## Report claims

Reproduced: default pins, 512-build pins, the padding and fingerprint lines, refusal of the lock path, `cmp` with the stored 512 net, the lock SHA-256 above, and 100000 equal evals with that hash on both this commit's objects and the lock's. Not run: the KRK depth table in `KRK_FINDINGS.md` (mate 17, mate 13, mate 9, and the threads-2 centipawn line). Those figures stay unread measurements. No Elo or speed claim was checked.

## What to fix

Keep the widened net and the parity test under `tests_t19/`. Do not change `CMakeLists.txt`, do not add `KRK_FINDINGS.md` at the `forge-combo29/` root, and do not `#include` `tests_t19` from `src/nnue.cpp`. The 512 translation unit already builds from the test with `-DFORGE_NNUE_HIDDEN=512`.
