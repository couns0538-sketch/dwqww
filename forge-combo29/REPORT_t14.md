# t14: UCI `eval`

## What was wrong

The training tools need the engine's static evaluation split into parts. The locked engine had no way to ask for it.

`src/uci.cpp` accepted `uci`, `isready`, `ucinewgame`, `setoption`, `position`, `go`, `bench`, `ponderhit`, `stop`, and `quit`. Anything else, including `eval`, was ignored. A position could be set, and the search could run, but nothing printed the hand-crafted score, the network score, and the static score the search actually adds together.

That gap is not fixed by calling the public helper that looks like evaluation. `Searcher::evaluate` (`include/forge/search.hpp`) returns only `Evaluator::evaluate_uncached`. That is the hand-crafted score with the pawn cache bypassed. With the shipped network turned on, the search does not use that number by itself.

The function the search calls is private: `Worker::static_evaluate` in `src/search.cpp`. It does three different things:

1. NNUE off, or no network compiled in: return `Evaluator::evaluate`. That is the hand-crafted score, and it may use the worker's pawn cache.
2. Network present but not a residual: return `nnue::evaluate` alone. The hand-crafted score is not added.
3. Residual network, which is this binary (`src/nnue_weights.inc` defines `FORGE_NNUE_RESIDUAL 1`): refresh the accumulator, take `nnue::evaluate` (already centipawns), add `Evaluator::evaluate_runtime`, and clamp into `[-MateInMaxPly + 1, MateInMaxPly - 1]`. `MateInMaxPly` is 31872, so the clamp range is -31871 to 31871.

`nnue::evaluate` is the integer the search adds. It is not a raw sigmoid and it is not a white-relative score. Both the hand-crafted eval and the network are already from the side to move.

Two nearby numbers are not that static score, and printing either of them would be wrong:

- After `static_evaluate`, a normal node stores `corrected_eval`, which adds the correction history. That history changes during a search. At the start of a search it is zero, so the two numbers match, but an `eval` command that read it would depend on earlier searches.
- On a transposition-table hit the search can then replace that value with the stored score. That is a search result, not the static evaluation.

In check, the search does not use the static evaluation as the node score. Around the static-evaluation block in `search`, `in_check` sets `static_eval`, `raw_eval`, and the local `eval` to `ValueNone` (32002) and does not call `static_evaluate`. The function itself still has a defined result. Printing `ValueNone`, or printing nothing, would hide a real score. The command has to print the three numbers and add ` incheck 1`.

Calling `static_evaluate` on the live search worker would also be wrong for this command. `evaluate` and `evaluate_runtime` write that worker's pawn cache. The task required that `eval` not change search state: no hash writes and no history changes. A thousand `eval` calls followed by `bench 11` had to still be 312866 nodes. The command therefore uses a temporary evaluator and a temporary accumulator. It does not touch the searcher's transposition table, histories, pawn cache, or stack.

One more existing detail, not changed here because changing it would move the node counts. In `scale_factor` (`src/eval.cpp`), a white-relative endgame score of exactly 0 treats Black as the strong side (`eg > 0 ? White : Black`). A colour-flipped position with a zero endgame score can therefore scale differently. The first 10 test positions still matched after a colour flip (swap colours, flip ranks). That check did not find a mismatch. It is not a proof for every position.

## What I found

Before any source edit, with `Threads 1`, `Hash 16`, `OwnBook false`, the portable build printed bench 11 = 312866, bench 13 = 862329, and `go perft 5` from the start position = 4865609. The same three numbers came back after the command was added. The full pin script also matched, including NNUE off (see below).

On all 30 test positions, with this residual network, `total` was exactly `hce + nnue`. The clamp did not change the sum. With NNUE switched off, `nnue` was 0 and `total` equalled the hand-crafted score, which equalled `Worker::static_evaluate` on a cleared pawn cache.

A first pass over candidate FENs had one illegal position: `8/8/8/4k3/8/8/8/Q3K3 w - - 0 1`. The queen on a1 checks the black king on e5, so the side that has just moved is in check. `set_fen` rejects that with `side that moved left its king in check`. It was replaced by `8/8/8/4k3/8/8/8/3QK3 w - - 0 1` (queen on d1, king on e1), which is legal. Two other FENs look like a pawn on the promotion rank but have no legal promotion: the push square is occupied and the pawn's capture squares are empty (`1n1k4/1P6/...` and its colour flip). Legal promotions in the set are `a7a8`, `e7e8`, and `a2a1`. Three positions are in check and print ` incheck 1`.

`ctest -N` on the original `CMakeLists.txt` listed no tests. The new C++ test was only a source file, so a normal configure/build/test run would stay green while `eval` bit-rotted. That is fixed by the `t14_eval` test.

A review comment asked to rebuild `windows/forge_clang_combo29_trial_w6.exe` and rewrite `windows_build/SOURCE_INPUTS.sha256`. Those files are the frozen lock named in `LOCK.md`. This branch does not replace them. The Linux engine source is what changed, and the pin counts above are the check that the search still walks the same tree.

## What changed

`eval` prints one line for the current position, all values from the side to move, in centipawns:

`info string eval hce <a> nnue <b> total <c>`

`a` is `Evaluator::evaluate_uncached`. `b` is `nnue::evaluate` after a fresh `nnue::refresh`, or 0 when the network is off. `c` is the same combination `Worker::static_evaluate` returns for a fresh position. If the side to move is in check, the line continues with ` incheck 1`.

`Worker::static_evaluate` was not edited. The new code is `Evaluator::static_eval_components` plus the `eval` branch in `uci.cpp`. Engine source grew by 47 lines and nothing was deleted.

The test file `tests_t14/eval_cases.txt` holds 30 FENs and the expected lines. `tests_t14/test_eval.cpp` checks those lines, checks `a` against `evaluate_uncached`, checks `b` against `nnue::evaluate`, checks `c` against `Worker::static_evaluate`, checks the colour flip of the first 10, and repeats the `c` check with NNUE off. `CMakeLists.txt` builds that program as `test_t14_eval` with the same flags as `forge` and registers it as the CTest name `t14_eval`. `README.md` names the command and `ctest`.

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
