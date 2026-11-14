# t14: UCI `eval`

## What I found

`forge-combo29` had no `eval` command. `src/uci.cpp` handles `uci`, `isready`, `ucinewgame`, `setoption`, `position`, `go`, `bench`, `ponderhit`, `stop`, and `quit`.

The static evaluation the search uses is `Worker::static_evaluate` (`src/search.cpp`):

- If NNUE is off or not compiled in, it returns `Evaluator::evaluate` (hand-crafted eval, pawn cache allowed).
- Otherwise it refreshes the accumulator and takes `nnue::evaluate`, which is already an integer centipawn value (`src/nnue.cpp`).
- This binary's network is residual (`src/nnue_weights.inc` defines `FORGE_NNUE_RESIDUAL 1`). The search then returns `clamp(evaluate_runtime + network, -MateInMaxPly + 1, MateInMaxPly - 1)`.
- If the network were not residual, the search would return the network value alone.
- A node in check does not use that value as the node score (`static_eval` is set to `ValueNone`), but `static_evaluate` itself still returns a number.

`Evaluator::evaluate_uncached` is the hand-crafted eval with no pawn cache. On this network, for every position in the test file, the search total was exactly the uncached hand-crafted score plus the network score (the clamp did not change it).

Before any source edit, with `Threads 1`, `Hash 16`, `OwnBook false`, the portable build printed bench 11 = 312866, bench 13 = 862329, and `go perft 5` from the start position = 4865609.

## The change

`eval` prints one line for the current position, from the side to move: `info string eval hce <a> nnue <b> total <c>`. `a` is `Evaluator::evaluate_uncached`, `b` is the network term the search adds (0 when NNUE is off), and `c` is the same combination `Worker::static_evaluate` returns for a fresh position. The calculation uses a temporary evaluator and accumulator, so it does not write the searcher's transposition table, history, or pawn cache. If the side to move is in check, the same numbers are printed and ` incheck 1` is appended.

Engine source grew by 47 lines and nothing was deleted. `Worker::static_evaluate` was not edited.

## Files changed

- `forge-combo29/include/forge/eval.hpp` — `EvalComponents` and `Evaluator::static_eval_components`
- `forge-combo29/src/eval.cpp` — implementation of that split
- `forge-combo29/src/uci.cpp` — `eval` command
- `forge-combo29/tests_t14/eval_cases.txt` — 30 FENs and the expected lines
- `forge-combo29/tests_t14/test_eval.cpp` — checks those lines, checks `total` against `Worker::static_evaluate`, and checks the colour-flip of the first 10
- `forge-combo29/CMakeLists.txt` — `test_t14_eval` target and the `t14_eval` CTest entry
- `forge-combo29/README.md` — `eval` and `ctest`
- `forge-combo29/REPORT_t14.md` — this report

`git diff --numstat` on the engine sources:

```
13	0	forge-combo29/include/forge/eval.hpp
27	0	forge-combo29/src/eval.cpp
7	0	forge-combo29/src/uci.cpp
```

## Commands and output

The CPU advertises AVX-512. The build below is still the Start command, including `-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`.

The first `cmake` failed because Clang 18 links with GCC 14's driver and `libstdc++.so` was not installed (`ld: cannot find -lstdc++`). `sudo apt-get install -y libstdc++-14-dev g++-14` fixed that. A later sanitizer link failed the same way for compiler-rt (`cannot find libclang_rt.asan-x86_64.a`); `sudo apt-get install -y libclang-rt-18-dev` fixed that. Those install logs are not copied here.

### Configure and build, before any source edit

```
rm -rf build && cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 && cmake --build build -j
```

CMake configured with Clang 18.1.3 and the build ended with `[100%] Built target forge`.

### Rule 7, before any source edit

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build/forge
```

```
info string bench depth 11 nodes 312866 time 184 nps 1700358
info string bench depth 13 nodes 862329 time 549 nps 1570726
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

### Rebuild after the source edit

```
cmake --build build -j
```

Recompiled `eval.cpp`, `eval_params.cpp`, `uci.cpp`, and `search.cpp` (the eval header changed), then linked. `[100%] Built target forge`.

### Rule 7, after the change

Same `printf` command as above.

```
info string bench depth 11 nodes 312866 time 197 nps 1588152
info string bench depth 13 nodes 862329 time 560 nps 1539873
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

bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609. The per-move perft counts match the run from before the edit. Only the reported times differ.

### `eval` on the 30 test positions

One candidate FEN (`8/8/8/4k3/8/8/8/Q3K3 w - - 0 1`) was rejected with `info string invalid FEN: side that moved left its king in check` and was replaced with `8/8/8/4k3/8/8/8/3QK3 w - - 0 1` before the case file was written. The committed file was then checked against a fresh engine run:

```
awk 'BEGIN{n=0} /^#/ || NF==0 {next} { if (n%2==0) printf "position fen %s\neval\n", $0; n++ }' forge-combo29/tests_t14/eval_cases.txt | ./build/forge > /tmp/t14_cli_eval.txt
awk 'BEGIN{n=0} /^#/ || NF==0 {next} { if (n%2==1) print; n++ }' forge-combo29/tests_t14/eval_cases.txt > /tmp/t14_expected_lines.txt
diff -u /tmp/t14_expected_lines.txt /tmp/t14_cli_eval.txt && echo "CLI matches expected lines"
```

```
CLI matches expected lines
```

`diff` produced no hunks. The 30 lines are the ones in `tests_t14/eval_cases.txt`. Three of them end in ` incheck 1`. Legal promotion moves exist for white (`a7a8q` and `e7e8q`) and black (`a2a1q`), from `go perft 1` on those FENs.

On all 30 lines, `hce + nnue == total` (30 matches, 0 mismatches).

### bench 11 after 1,000 `eval` calls

A throwaway program walked legal moves from 10 seeds and wrote 1,000 distinct `position fen` / `eval` pairs to `/tmp/t14_1000.uci` (2,000 lines; `grep -c '^eval$'` = 1000). That generator is not in the repository.

```
{
  echo "setoption name Threads value 1"
  echo "setoption name Hash value 16"
  echo "setoption name OwnBook value false"
  cat /tmp/t14_1000.uci
  echo "bench 11"
  echo quit
} | ./build/forge > /tmp/t14_1000.out
```

```
eval replies: 1000
invalid: 0
```

`wc -l /tmp/t14_1000.out` was 1001: 1,000 `info string eval` lines and this bench line. First reply: `info string eval hce 18 nnue 20 total 38`. Last eval reply: `info string eval hce 2117 nnue 1102 total 3219`.

```
info string bench depth 11 nodes 312866 time 187 nps 1673080
```

### C++ test

```
DEFS="-DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0"
c++ -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v3 $DEFS -I forge-combo29/include -pthread \
  forge-combo29/tests_t14/test_eval.cpp \
  forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp forge-combo29/src/book.cpp \
  forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp \
  -o /tmp/test_eval && /tmp/test_eval forge-combo29/tests_t14/eval_cases.txt
```

```
ok 30 positions, 10 mirrors, 3 in check, promotions white 2 black 1
```

For every case the test checks the printed line, `hce` against `Evaluator::evaluate_uncached`, `nnue` against `nnue::evaluate` after `nnue::refresh`, and `total` against `Worker::static_evaluate` on a worker whose pawn cache was cleared. The first 10 are colour-flipped (ranks flipped, colours swapped); the three numbers match, and flipping twice restores the position key. It also turns NNUE off and checks that `nnue` is 0 and `total` equals both the hand-crafted score and `static_evaluate`.

### Same test with `-fsanitize=address,undefined`

```
c++ -std=c++20 -O1 -g -ffp-contract=off -fno-fast-math -march=x86-64-v3 -fno-omit-frame-pointer -fsanitize=address,undefined $DEFS -I forge-combo29/include -pthread \
  forge-combo29/tests_t14/test_eval.cpp \
  forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp forge-combo29/src/book.cpp \
  forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp \
  -o /tmp/test_eval_asan && /tmp/test_eval_asan forge-combo29/tests_t14/eval_cases.txt
```

```
ok 30 positions, 10 mirrors, 3 in check, promotions white 2 black 1
```

Exit status 0. AddressSanitizer and UndefinedBehaviorSanitizer printed no diagnostics.

## Follow-up: CTest, and the full pin set

`ctest` did not know about `tests_t14/test_eval.cpp`, because `CMakeLists.txt` only built `forge`. The test executable is now `test_t14_eval`, compiled with the same flags as `forge` and registered as `t14_eval`. `forge`'s own compile lines did not change, and that target was not rebuilt.

The Windows lock executable and `windows_build/SOURCE_INPUTS.sha256` are the frozen snapshot named in `LOCK.md`. This branch does not replace that binary or rewrite those hashes.

### Full combo29 pins

```
/agent/repos/dwqww/forge-combo29/scripts/check_pins.sh /agent/repos/dwqww/build/forge
```

Run from `/tmp` so `pins_out.txt` was not written into the repository.

```
net-on : 312866 862329 3024920 12389307 34048354
net-off: 375354 907205 2448617 13573040 24506465
perft5 : 4865609
PINS MATCH combo29
```

### CTest

```
cmake --build build -j
ctest --test-dir build -N
ctest --test-dir build --output-on-failure
./build/test_t14_eval forge-combo29/tests_t14/eval_cases.txt
```

`ctest -N` listed `Test #1: t14_eval` (Total Tests: 1). `ctest` printed:

```
1/1 Test #1: t14_eval .........................   Passed    0.05 sec

100% tests passed, 0 tests failed out of 1
```

Direct run of the same binary:

```
ok 30 positions, 10 mirrors, 3 in check, promotions white 2 black 1
```

## What I could not verify

- The non-residual branch (`total` equals the network alone). This binary's network is residual, so that branch did not run.
- `eval` while a search thread is inside `search`. The command does not call `stop`, and it only reads the main-thread board, but I did not overlap it with a live search.
- Sanitizers on the `forge` executable. Only `tests_t14/test_eval.cpp` linked with the engine sources was built with `-fsanitize=address,undefined`.
- The colour-flip check on the other 20 positions. The test covers the first 10.
- `static_evaluate` with a warm pawn cache. The comparison clears the cache first. A cache hit is supposed to return the stored miss result; I did not hunt for a pawn-key collision.
- The Windows lock binary and `-march=znver5`. This run is the portable x86-64-v3 build from the Start command. The three node counts still matched.
