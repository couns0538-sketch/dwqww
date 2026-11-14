# t19: 512-wide net parity

## What I found

The lock net is 768 inputs, 256 hidden units per side, and one output. `FORGE_NNUE_HIDDEN` was a fixed compile definition of 256. The accumulator, the feature updates, and the output kernel already loop to `HiddenSize` and require only that the width is a multiple of 16. 512 satisfies that. Nothing in the SIMD loops, the alignment, or the `static_assert`s was hardcoded to 256 hidden units, so the 512 build compiled with no further engine change.

The lock file `src/nnue_weights.inc` is a different matter. Its arrays are sized for 256 and it asserts `HiddenSize == 256`. A 512 build cannot include that file. The converter writes a second file in which units 0..255 of each side are the lock units and units 256..511 are zero. With that file, the 512 engine computes the same function as the lock.

On this machine, after the change:

- default `FORGE_NNUE_HIDDEN=256`: `bench 11` = 312866, `bench 13` = 862329, `go perft 5` from the start position = 4865609
- `FORGE_NNUE_HIDDEN=512` with the widened net, same portable flags: the same three numbers
- the same 512 net built with the AVX-512 output kernel (`FORGE_SPD_NNUE_ZMM=1`, `-march=x86-64-v4`): the same three numbers
- 100000 static evaluations, fixed seed `20261110`: 0 positions differ, largest absolute difference 0, under both the AVX2 kernel and the AVX-512 kernel. The two hashes are equal (`13290400224059203287`). Address and undefined sanitizers printed nothing and the test exited 0.

`/usr/bin/c++` on this machine is Clang 18.1.3. A plain configure with it fails: the driver selects GCC 14, whose C++ headers are not installed, and the link cannot find `-lstdc++`. The numbers above were produced with g++ 13.3.0. The same default (256) source, compiled with Clang 18.1.3 and `--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`, prints the same three numbers.

## Change

`FORGE_NNUE_HIDDEN` is now a CMake cache variable with default 256, passed through as the same compile definition. When the macro is 512, `src/nnue.cpp` includes `tests_t19/nnue_weights_512.inc` instead of the lock weights. The 256 build still includes `src/nnue_weights.inc`. The widened file is produced by `tests_t19/widen_nnue.cpp`. The parity test links two copies of `src/nnue.cpp` (hidden 256, and hidden 512 renamed to `forge::nnue512`) and compares their static evaluations. Engine source diff is 6 added lines and 1 removed line in `src/nnue.cpp`, plus the CMake cache variable.

## Weight layout

From `src/nnue.cpp`. `H` is `HiddenSize`.

- `NnueW1` has length `768 * H`. Index is `feature * H + hidden`. The hidden index runs fastest: one input feature owns a contiguous column of `H` weights. `refresh` adds the column at `w1 + feature_index(...) * H`.
- `NnueB1` has length `H`, one bias per hidden unit.
- `NnueW2` has length `2 * H`. Indices `[0, H)` are the side to move. Indices `[H, 2H)` are the opponent. The output kernel multiplies SCReLU of the side-to-move unit `h` by `w2[h]` and SCReLU of the opponent unit `h` by `w2[H + h]`.
- `NnueB2` is one int16. The lock value is 127. Scale of `W1` and `B1` is 4096. Scale of `W2` and `B2` is 4096. The net is residual (`FORGE_NNUE_RESIDUAL` is 1).

Widening `H` from 256 to 512 copies lock units 0..255 and writes zeros for units 256..511:

- In `NnueW1` the zeros are the second half of each feature column, not an extra block of features. `new[feature * 512 + h] = old[feature * 256 + h]` for `h < 256`, else 0.
- `NnueB1[0..255]` is copied and `NnueB1[256..511]` is 0.
- In `NnueW2` the opponent block starts at index `H`, so the zeros are inserted in the middle. `new[0..255]` is the lock's own side, `new[256..511]` is 0, `new[512..767]` is the lock's opponent side (`old[256..511]`), and `new[768..1023]` is 0.
- `NnueB2` is unchanged.

The converter checked those indices and wrote 196608 padding zeros in `W1`, 256 in `B1`, and 512 in `W2`. The lock columns already contained 125 zeros; those are original weights, not padding.

The output kernel keeps 16 lanes. Lane `j` sums hidden units `j, j+16, j+32, ...`. The extra units are exact zeros, so each lane is summed with extra `+0` terms. On these builds that did not change any of the 100000 integer evaluations, and it did not change the bench node counts.

## Static evaluation that was compared

For each position the test refreshes the accumulator from scratch and takes `nnue::evaluate`. Both copies are residual, so the static evaluation is

`clamp(Evaluator::evaluate_uncached(board) + network, -MateInMaxPly + 1, MateInMaxPly - 1)`

with `MateInMaxPly = 32000 - 128`. Search uses `evaluate_runtime` plus the same network. The classical term does not depend on the hidden width, and the network values themselves also matched (`network_differ 0`). The bench runs use the real search path, including incremental accumulator updates.

The generator is `std::mt19937` seeded with `20261110`. From the start position it plays `rng() % legal_move_count` until mate, stalemate, the 50-move rule, threefold repetition, insufficient material, or 400 plies, then returns to the start position. 100000 visits, 98914 distinct position keys, 310 resets.

## Files changed

- `forge-combo29/CMakeLists.txt` — `FORGE_NNUE_HIDDEN` cache variable, default 256
- `forge-combo29/src/nnue.cpp` — include the widened weights when the macro is 512
- `forge-combo29/tests_t19/widen_nnue.cpp` — converter
- `forge-combo29/tests_t19/nnue_weights_512.inc` — generated widened net
- `forge-combo29/tests_t19/wide_eval.hpp`
- `forge-combo29/tests_t19/wide_eval.cpp`
- `forge-combo29/tests_t19/eval_parity.cpp`
- `forge-combo29/REPORT_t19.md`

No file under `include/` changed. The diff of engine source (`src/` and `include/`) is 7 lines in `src/nnue.cpp`.

## Commands and output

Machine: 4 vCPU, AVX-512 present (`avx512f` and the rest of the set). g++ is `g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`. Clang is `Ubuntu clang version 18.1.3`. The Start command was run as written, with `-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`, even though the CPU has AVX-512. A separate AVX-512 build is recorded below.

### Compiler: plain `/usr/bin/c++` does not configure

```
cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3
```

First attempt, link of the compiler test:

```
/usr/bin/ld: cannot find -lstdc++: No such file or directory
c++: error: linker command failed with exit code 1 (use -v to see invocation)
```

After pointing `LIBRARY_PATH` at `/usr/lib/gcc/x86_64-linux-gnu/13`, configure got past the link and the build failed in every source file:

```
forge-combo29/include/forge/bitboard.hpp:3:10: fatal error: 'array' file not found
    3 | #include <array>
```

Clang's `-v` trace selects `/usr/lib/gcc/x86_64-linux-gnu/14`, and `/usr/include/c++` contains only `13`. `clang++ --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13` can compile. The builds below use `CXX=g++` unless a command says Clang.

### Baseline, before any source change

`CXX=g++`, then:

```
cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3
cmake --build build -j
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build/forge
```

Build completed (`Built target forge`). Engine output:

```
info string bench depth 11 nodes 312866 time 207 nps 1511429
info string bench depth 13 nodes 862329 time 454 nps 1899403
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609
```

### Default build after the change

Same cmake and build commands again (`CXX=g++`). `flags.make` contains `-DFORGE_NNUE_HIDDEN=256`. Only `nnue.cpp` rebuilt. Then the same `printf | ./build/forge` command:

```
info string bench depth 11 nodes 312866 time 194 nps 1612711
info string bench depth 13 nodes 862329 time 1111 nps 776173
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609
```

### Clang, default hidden size, after the change

```
unset CXX
cmake -S forge-combo29 -B build-clang -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 -DCMAKE_CXX_COMPILER=clang++ -DCMAKE_CXX_FLAGS="--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13"
cmake --build build-clang -j
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build-clang/forge
```

`Built target forge`. Output:

```
info string bench depth 11 nodes 312866 time 181 nps 1728541
info string bench depth 13 nodes 862329 time 433 nps 1991521
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609
```

### Converter

```
g++ -std=c++20 -O2 -o /tmp/widen_nnue forge-combo29/tests_t19/widen_nnue.cpp
/tmp/widen_nnue forge-combo29/src/nnue_weights.inc /tmp/nnue_weights_512_again.inc
cmp forge-combo29/tests_t19/nnue_weights_512.inc /tmp/nnue_weights_512_again.inc && echo NONASAN_CMP_OK
```

```
input forge-combo29/src/nnue_weights.inc
output /tmp/nnue_weights_512_again.inc
read w1=196608 b1=256 w2=512 b2=127
write w1=393216 b1=512 w2=1024 b2=127
padding_zeros w1=196608 b1=256 w2=512
lock_column_zeros w1=125
fingerprint w1=6227214367631889344 b1=10979643604819931428 w2=11500908642059936499
NONASAN_CMP_OK
```

The file in `tests_t19/nnue_weights_512.inc` is that output. The first column starts `-18, 62, 73, -3`, matching the lock file, and the weights after hidden unit 255 of feature 0 are zeros until feature 1, which starts `50, -2, 20, -185`.

### 512 engine, portable, same flags as the lock check

```
CXX=g++ cmake -S forge-combo29 -B build512 -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 -DFORGE_NNUE_HIDDEN=512
cmake --build build512 -j
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build512/forge
```

`flags.make`: `-DFORGE_NNUE_HIDDEN=512` and `-DFORGE_SPD_NNUE_ZMM=0`. `Built target forge`. Output:

```
info string bench depth 11 nodes 312866 time 199 nps 1572190
info string bench depth 13 nodes 862329 time 527 nps 1636297
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609
```

### 100000-position comparison (release, AVX2 kernel)

Objects were compiled with the same `-O3 -ffp-contract=off -fno-fast-math -march=x86-64-v3` and the same `FORGE_*` defines as `build/CMakeFiles/forge.dir/flags.make`. The 512 copy adds `-DFORGE_NNUE_HIDDEN=512 -Dnnue=nnue512`. The 256 copy uses `-DFORGE_NNUE_HIDDEN=256`.

```
g++ -std=c++20 -O3 -DNDEBUG -ffp-contract=off -fno-fast-math -march=x86-64-v3 \
  -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_NNUE_ZMM=0 \
  -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=0 \
  -DFORGE_SPD_TT_NOTLS=1 -I forge-combo29/include -I forge-combo29/tests_t19 \
  -DFORGE_NNUE_HIDDEN=256 -c forge-combo29/src/bitboard.cpp -o /tmp/t19/bitboard.o
g++ ... -DFORGE_NNUE_HIDDEN=256 -c forge-combo29/src/board.cpp -o /tmp/t19/board.o
g++ ... -DFORGE_NNUE_HIDDEN=256 -c forge-combo29/src/eval.cpp -o /tmp/t19/eval.o
g++ ... -DFORGE_NNUE_HIDDEN=256 -c forge-combo29/src/eval_params.cpp -o /tmp/t19/eval_params.o
g++ ... -DFORGE_NNUE_HIDDEN=256 -c forge-combo29/src/nnue.cpp -o /tmp/t19/nnue256.o
g++ ... -DFORGE_NNUE_HIDDEN=512 -Dnnue=nnue512 -c forge-combo29/src/nnue.cpp -o /tmp/t19/nnue512.o
g++ ... -DFORGE_NNUE_HIDDEN=512 -Dnnue=nnue512 -c forge-combo29/tests_t19/wide_eval.cpp -o /tmp/t19/wide_eval.o
g++ ... -DFORGE_NNUE_HIDDEN=256 -c forge-combo29/tests_t19/eval_parity.cpp -o /tmp/t19/eval_parity.o
g++ ... -o /tmp/t19/eval_parity /tmp/t19/bitboard.o /tmp/t19/board.o /tmp/t19/eval.o /tmp/t19/eval_params.o /tmp/t19/nnue256.o /tmp/t19/nnue512.o /tmp/t19/wide_eval.o /tmp/t19/eval_parity.o
/tmp/t19/eval_parity
```

The `...` stands for the same leading flags as the first `g++` line. Link printed `LINK_OK`. Program output, exit 0:

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
worst_fen -
worst_static_256 0
worst_static_512 0
network_differ 0
network_max_abs_diff 0
worst_network_256 0
worst_network_512 0
hash_static_256 13290400224059203287
hash_static_512 13290400224059203287
```

### Same tests with `-fsanitize=address,undefined`

Every object and the link used the flags above plus `-fsanitize=address,undefined -fno-omit-frame-pointer -g`. The converter was compiled the same way.

```
g++ -std=c++20 -O3 -DNDEBUG -ffp-contract=off -fno-fast-math -march=x86-64-v3 \
  -fsanitize=address,undefined -fno-omit-frame-pointer -g \
  -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_NNUE_ZMM=0 \
  -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=0 \
  -DFORGE_SPD_TT_NOTLS=1 -I forge-combo29/include -I forge-combo29/tests_t19 \
  (same -c steps as above, outputs under /tmp/t19asan, same -D pairs)
g++ ... -fsanitize=address,undefined -o /tmp/t19asan/eval_parity (the eight objects)
/tmp/t19asan/eval_parity
g++ -std=c++20 -O2 -fsanitize=address,undefined -fno-omit-frame-pointer -g \
  -o /tmp/t19asan/widen_nnue forge-combo29/tests_t19/widen_nnue.cpp
/tmp/t19asan/widen_nnue forge-combo29/src/nnue_weights.inc /tmp/nnue_weights_512_asan.inc
cmp forge-combo29/tests_t19/nnue_weights_512.inc /tmp/nnue_weights_512_asan.inc && echo CMP_OK
```

No sanitizer diagnostic was printed. `eval_parity` exit 0:

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
worst_fen -
worst_static_256 0
worst_static_512 0
network_differ 0
network_max_abs_diff 0
worst_network_256 0
worst_network_512 0
hash_static_256 13290400224059203287
hash_static_512 13290400224059203287
```

Converter exit 0, and `CMP_OK`:

```
input forge-combo29/src/nnue_weights.inc
output /tmp/nnue_weights_512_asan.inc
read w1=196608 b1=256 w2=512 b2=127
write w1=393216 b1=512 w2=1024 b2=127
padding_zeros w1=196608 b1=256 w2=512
lock_column_zeros w1=125
fingerprint w1=6227214367631889344 b1=10979643604819931428 w2=11500908642059936499
```

### bench 13 time, three runs each

Each run is a new process. The `time` field is the engine's own millisecond timer around the fixed-depth search, not a claim about playing strength.

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 13\nquit\n' | ./build/forge
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 13\nquit\n' | ./build512/forge
```

Default, hidden 256:

```
info string bench depth 13 nodes 862329 time 533 nps 1617878
info string bench depth 13 nodes 862329 time 508 nps 1697498
info string bench depth 13 nodes 862329 time 483 nps 1785360
```

Hidden 512, portable:

```
info string bench depth 13 nodes 862329 time 566 nps 1523549
info string bench depth 13 nodes 862329 time 546 nps 1579357
info string bench depth 13 nodes 862329 time 526 nps 1639408
```

### AVX-512 output kernel, hidden 512

`FORGE_PORTABLE` left at its default OFF, so this build sets `FORGE_SPD_NNUE_ZMM=1` and `FORGE_SPD_SLIDER_PEXT=1`.

```
CXX=g++ cmake -S forge-combo29 -B build512zmm -DCMAKE_BUILD_TYPE=Release -DFORGE_NNUE_HIDDEN=512 -DFORGE_MARCH=x86-64-v4
cmake --build build512zmm -j
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build512zmm/forge
```

`flags.make` has `-DFORGE_NNUE_HIDDEN=512 -DFORGE_SPD_NNUE_ZMM=1` and `-march=x86-64-v4`. `Built target forge`. Output:

```
info string bench depth 11 nodes 312866 time 207 nps 1511429
info string bench depth 13 nodes 862329 time 550 nps 1567870
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609
```

The parity test was compiled again with `-march=x86-64-v4 -DFORGE_SPD_NNUE_ZMM=1` on both `nnue.cpp` copies and on `eval_parity.cpp` / `wide_eval.cpp`. `bitboard.o`, `board.o`, `eval.o`, and `eval_params.o` were the portable objects from `/tmp/t19` (those files do not contain the NNUE kernel). Output, exit 0, same hash as the AVX2 run:

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
worst_fen -
worst_static_256 0
worst_static_512 0
network_differ 0
network_max_abs_diff 0
worst_network_256 0
worst_network_512 0
hash_static_256 13290400224059203287
hash_static_512 13290400224059203287
```

## Review follow-up

`eval_parity` now exits 1 when `network_differ` is not 0, including when the clamped static scores still match. Rebuilt `/tmp/t19/eval_parity` from the existing release objects and the new `eval_parity.cpp`, then ran it. Exit 0. The printed block matches the release run above, including `network_differ 0` and both hashes `13290400224059203287`.

`widen_nnue` resolves the output path before writing. It refuses the lock file, a `..` spelling of that file, a symlink to it, and any output that is the same file as the input. The lock file's SHA-256 stayed `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`. A write to `/tmp/nnue_weights_512_review.inc` matched `tests_t19/nnue_weights_512.inc` (`cmp`, 1732702 bytes, same fingerprints as the earlier converter run).

```
g++ -std=c++20 -O2 -o /tmp/widen_nnue forge-combo29/tests_t19/widen_nnue.cpp
/tmp/widen_nnue forge-combo29/src/nnue_weights.inc forge-combo29/src/../src/nnue_weights.inc
```

```
widen_nnue: refusing to overwrite the lock weights
```

Exit 2. The same refusal, also exit 2, for the lock path itself and for `/tmp/nnue_weights_lock_link.inc` (a symlink to the lock file).

## What I could not verify

- A configure that uses `/usr/bin/c++` with no extra flag. That compiler does not see a C++ standard library on this machine. Clang 18.1.3 does match the three default numbers when given `--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`.
- The Windows lock recipe (clang ThinLTO, IR-PGO, `-march=znver5`).
- Hidden widths other than 256 and 512.
- Static-eval equality on any set of positions other than these 100000 playout visits and the positions search reaches inside `bench`.
- A lane-by-lane dump of incremental accumulators against `refresh`. Incremental updates were checked only by the bench node counts, which use that path.
- Playing strength. Nothing here is an Elo result. The `bench 13` times are one machine's timer on three runs.
