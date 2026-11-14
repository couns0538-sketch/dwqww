# Task 9: UCI `eval`

Branch `grok47/t9-eval`, from `lock/combo29-20261110` (`16833ecc`).

## What was wrong

The lock engine has no way to print the evaluation of the current position.

`main` in `forge-combo29/src/uci.cpp` reads one UCI line at a time and handles only `uci`, `isready`, `ucinewgame`, `setoption`, `position`, `go`, `bench`, `ponderhit`, `stop`, and `quit`. Any other word, including `eval`, is discarded. The program stays running and prints nothing for that line. A GUI, a training run, or a person at the console cannot ask for the score of the position that `position` just set.

The two numbers the command has to show already exist, and both are centipawns from the side to move. They are computed in different places and the engine never adds them together for output.

The hand-written score is `Evaluator::evaluate_uncached` in `forge-combo29/src/eval.cpp`. It calls `evaluate_position` with no pawn cache and no incremental piece-square table. That walk adds, from White's point of view, the piece-square table, pawn structure, piece mobility, king safety, threats, passed pawns, the bishop pair, and tempo for the side about to move. It tapers middlegame and endgame by the phase, then scales the endgame. The returned integer is that tapered score when White is to move, and the negation of it when Black is to move. Tempo is applied before the negation, so it is a bonus for the side to move in either case.

The network score is `nnue::evaluate` in `forge-combo29/src/nnue.cpp`. It needs a refreshed accumulator (`nnue::refresh` fills both perspectives from the compiled weights). The output layer takes the side-to-move accumulator and the opponent accumulator, applies SCReLU, and reduces sixteen lanes in a fixed order. The raw output is in sigmoid units. The conversion to centipawns is `out * 400 / SigmoidK` with `SigmoidK` equal to 2.25, then a cast to `int` after clamping the float to [-30000, 30000]. The header `forge-combo29/include/forge/nnue.hpp` states that this integer is the side-to-move evaluation in centipawns.

The compiled net is a residual, not a replacement for the hand-written eval. `forge-combo29/src/nnue_weights.inc` defines `FORGE_NNUE_RESIDUAL` as 1, and `nnue::residual()` is true when that flag and `FORGE_HAS_NNUE` are both set. `Worker::static_evaluate` in `forge-combo29/src/search.cpp` is the only place that combines them during a search. When the net is active and residual, it does three things the missing command must not be confused with:

1. It keeps an incremental accumulator on the search stack and refreshes it from the nearest valid ancestor.
2. It adds `nnue::evaluate` to `Evaluator::evaluate_runtime`, which is a private method. `evaluate_runtime` calls the same `evaluate_position` template, but it may take the piece-square term from the worker's incremental `RuntimePsqt` instead of recomputing it from the live parameter table. `evaluate_uncached` always recomputes that term and never reads the pawn cache.
3. It clamps the sum to `[-MateInMaxPly + 1, MateInMaxPly - 1]`. `MateValue` is 32000 and `MaxPly` is 128, so `MateInMaxPly` is 31872 and the clamp interval is [-31871, 31871].

That search function is not reachable from UCI, and it is not the sum the task asks for. The task asks for `Evaluator::evaluate_uncached`, the network output in centipawns, and the sum of those two, each from the side to move. Nothing in the lock prints those three numbers. Search, bench, and perft were left unchanged so their node counts stay on the lock pins.

## What the change does

`forge::eval_report` builds one line from the current board.

- `hce` is `Evaluator::evaluate_uncached(board)`.
- When `nnue::enabled` and `nnue::available()` are both true, the function refreshes a fresh accumulator and sets `nnue` to `nnue::evaluate`. `sum` is the C++ `int` sum of those two values, with no mate clamp.
- When the network is switched off (`setoption name UseNNUE value false`) or no net is compiled in, the line uses the token `off` and `sum` equals `hce`.

The line is:

```text
info string eval hce <cp> nnue <cp> sum <cp>
info string eval hce <cp> nnue off sum <cp>
```

The UCI loop handles the command `eval` by printing that line for the board `position` last set. Before any `position`, the board is the standard start position, because `Board::Board` calls `set_fen(StandardStartFen)`. `eval` does not stop a search, does not change the board, and does not add a UCI option.

Measured on this build, with the compiled residual net:

| Position | Side to move | hce | nnue | sum |
| --- | --- | ---: | ---: | ---: |
| start position | White | 18 | 20 | 38 |
| after `e2e4` | Black | -52 | 63 | 11 |
| after `e2e4`, `UseNNUE false` | Black | -52 | off | -52 |

`38 = 18 + 20` and `11 = -52 + 63`. These are the printed terms. This report does not claim they equal `Worker::static_evaluate`, because that function was not called.

## Files changed

Engine source, 22 insertions and 0 deletions:

- `forge-combo29/include/forge/eval.hpp` declares `forge::eval_report`.
- `forge-combo29/src/eval.cpp` defines it.
- `forge-combo29/src/uci.cpp` prints it for the command `eval`.

Tests and this report, new files only:

- `forge-combo29/tests_t9/eval_test.cpp` calls `eval_report`. It checks the start position and the position after `e2e4`. For each, the printed `hce` must equal `Evaluator::evaluate_uncached`, the printed `nnue` must equal `nnue::refresh` plus `nnue::evaluate`, and `sum` must equal those two integers added. It then sets `nnue::enabled` to false and checks the `nnue off` line, where `sum` equals `hce`.
- `forge-combo29/tests_t9/eval_commands.txt` is the UCI transcript.
- `forge-combo29/tests_t9/eval_expected.txt` is the three `eval` lines measured from the release binary.

`eval_report` is not declared on the lock, so this test does not compile against the lock headers.

## Commands and output

Host compiler for the successful build: `g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`. `lscpu` reports `avx512f`, so the build uses the lock default `-march=x86-64-v4` and `FORGE_SPD_NNUE_ZMM=1`. `FORGE_PORTABLE` was left off.

The first configure attempt used `/usr/bin/c++`, which is Clang 18.1.3. It failed before any engine source was compiled, because the link of CMake's compiler test could not find `-lstdc++`. The engine was then configured with `g++`.

```text
cmake -S /agent/repos/dwqww/forge-combo29 -B /tmp/forge-t9-rel -DCMAKE_BUILD_TYPE=Release
```

```text
-- The CXX compiler identification is Clang 18.1.3
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - failed
-- Check for working CXX compiler: /usr/bin/c++
-- Check for working CXX compiler: /usr/bin/c++ - broken
-- Configuring incomplete, errors occurred!
CMake Error at /usr/share/cmake-3.28/Modules/CMakeTestCXXCompiler.cmake:60 (message):
  The C++ compiler

    "/usr/bin/c++"

  is not able to compile a simple test program.

  It fails with the following output:

    Change Dir: '/tmp/forge-t9-rel/CMakeFiles/CMakeScratch/TryCompile-h2tQhd'

    Run Build Command(s): /usr/bin/cmake -E env VERBOSE=1 /usr/bin/gmake -f Makefile cmTC_1151d/fast
    /usr/bin/gmake  -f CMakeFiles/cmTC_1151d.dir/build.make CMakeFiles/cmTC_1151d.dir/build
    gmake[1]: Entering directory '/tmp/forge-t9-rel/CMakeFiles/CMakeScratch/TryCompile-h2tQhd'
    Building CXX object CMakeFiles/cmTC_1151d.dir/testCXXCompiler.cxx.o
    /usr/bin/c++    -MD -MT CMakeFiles/cmTC_1151d.dir/testCXXCompiler.cxx.o -MF CMakeFiles/cmTC_1151d.dir/testCXXCompiler.cxx.o.d -o CMakeFiles/cmTC_1151d.dir/testCXXCompiler.cxx.o -c /tmp/forge-t9-rel/CMakeFiles/CMakeScratch/TryCompile-h2tQhd/testCXXCompiler.cxx
    Linking CXX executable cmTC_1151d
    /usr/bin/cmake -E cmake_link_script CMakeFiles/cmTC_1151d.dir/link.txt --verbose=1
    /usr/bin/c++ CMakeFiles/cmTC_1151d.dir/testCXXCompiler.cxx.o -o cmTC_1151d
    /usr/bin/ld: cannot find -lstdc++: No such file or directory
    c++: error: linker command failed with exit code 1 (use -v to see invocation)
    gmake[1]: *** [CMakeFiles/cmTC_1151d.dir/build.make:100: cmTC_1151d] Error 1
    gmake[1]: Leaving directory '/tmp/forge-t9-rel/CMakeFiles/CMakeScratch/TryCompile-h2tQhd'
    gmake: *** [Makefile:127: cmTC_1151d/fast] Error 2
```

```text
rm -rf /tmp/forge-t9-rel && cmake -S /agent/repos/dwqww/forge-combo29 -B /tmp/forge-t9-rel -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ && cmake --build /tmp/forge-t9-rel -j"$(nproc)"
```

```text
-- The CXX compiler identification is GNU 13.3.0
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Check for working CXX compiler: /usr/bin/g++ - skipped
-- Detecting CXX compile features
-- Detecting CXX compile features - done
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD - Success
-- Found Threads: TRUE
-- Configuring done (0.2s)
-- Generating done (0.0s)
-- Build files have been written to: /tmp/forge-t9-rel
[ 11%] Building CXX object CMakeFiles/forge.dir/src/bitboard.cpp.o
[ 22%] Building CXX object CMakeFiles/forge.dir/src/book.cpp.o
[ 33%] Building CXX object CMakeFiles/forge.dir/src/board.cpp.o
[ 44%] Building CXX object CMakeFiles/forge.dir/src/eval.cpp.o
[ 55%] Building CXX object CMakeFiles/forge.dir/src/eval_params.cpp.o
[ 66%] Building CXX object CMakeFiles/forge.dir/src/nnue.cpp.o
[ 77%] Building CXX object CMakeFiles/forge.dir/src/search.cpp.o
[ 88%] Building CXX object CMakeFiles/forge.dir/src/uci.cpp.o
[100%] Linking CXX executable forge
[100%] Built target forge
```

`bench` constructs `Searcher(16)`, which is a 16 MB hash and the default of 1 thread. The `setoption` lines are sent anyway. `OwnBook` is false. The `nps` field is the engine's printout for that process; it is not a comparison with another build.

```text
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nquit\n' | /tmp/forge-t9-rel/forge
```

```text
info string bench depth 11 nodes 312866 time 161 nps 1943267
```

The lock pin is 312866 nodes. This run printed 312866.

```text
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 13\nquit\n' | /tmp/forge-t9-rel/forge
```

```text
info string bench depth 13 nodes 862329 time 427 nps 2019505
```

The lock pin is 862329 nodes. This run printed 862329.

```text
printf 'position startpos\ngo perft 5\nquit\n' | /tmp/forge-t9-rel/forge
```

```text
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

The lock pin is 4865609 nodes. This run printed 4865609.

```text
cat forge-combo29/tests_t9/eval_commands.txt | /tmp/forge-t9-rel/forge
```

`eval_commands.txt` contains:

```text
uci
isready
setoption name Threads value 1
setoption name Hash value 16
setoption name OwnBook value false
eval
position startpos moves e2e4
eval
setoption name UseNNUE value false
eval
quit
```

Full output:

```text
id name Chess Engine Forge 6.4.24 candidate
id author OpenAI
option name Hash type spin default 32 min 1 max 2048
option name Threads type spin default 1 min 1 max 256
option name Move Overhead type spin default 10 min 0 max 1000
option name Ponder type check default false
option name OwnBook type check default true
option name Book File type string default <empty>
option name Book Depth type spin default 30 min 0 max 100
option name Book Variety type spin default 30 min 0 max 100
option name UseNNUE type check default true
option name LmrQuietBase type spin default 85 min 0 max 300
option name LmrQuietDivisor type spin default 220 min 100 max 500
option name LmrNoisyBase type spin default 10 min 0 max 300
option name LmrNoisyDivisor type spin default 340 min 100 max 800
option name NullMoveMinDepth type spin default 3 min 1 max 10
option name NullMoveBase type spin default 3 min 1 max 6
option name NullMoveDepthDivisor type spin default 3 min 1 max 10
option name NullMoveEvalDivisor type spin default 200 min 50 max 1000
option name RfpDepth type spin default 8 min 0 max 15
option name RfpMargin type spin default 72 min 10 max 300
option name RfpImproving type spin default 40 min 0 max 200
option name RazorDepth type spin default 2 min 0 max 6
option name RazorBase type spin default 150 min 0 max 1000
option name RazorMultiplier type spin default 350 min 0 max 1000
option name FutilityDepth type spin default 7 min 0 max 15
option name FutilityBase type spin default 100 min 0 max 500
option name FutilityMultiplier type spin default 110 min 0 max 500
option name LmpBase type spin default 4 min 0 max 20
option name HistoryPruneDepth type spin default 3 min 0 max 10
option name HistoryPruneMultiplier type spin default 2048 min 0 max 20000
option name SeeQuietMultiplier type spin default 24 min 0 max 200
option name SeeNoisyMultiplier type spin default 150 min 0 max 1000
option name SingularDepth type spin default 7 min 2 max 20
option name SingularMargin type spin default 2 min 0 max 10
option name IirDepth type spin default 4 min 1 max 20
option name ProbcutDepth type spin default 5 min 1 max 20
option name ProbcutMargin type spin default 180 min 0 max 1000
option name QsFutilityMargin type spin default 160 min 0 max 1000
option name QsSeeMargin type spin default 40 min 0 max 500
option name AspirationDelta type spin default 18 min 4 max 200
option name HistoryBonusQuadratic type spin default 20 min 0 max 100
option name HistoryBonusLinear type spin default 48 min 0 max 500
option name HistoryBonusMax type spin default 2048 min 100 max 10000
option name LmrHistoryDivisor type spin default 6000 min 1000 max 30000
option name CheckExtensionDepth type spin default 2 min 1 max 30
option name LmrCutoffThreshold type spin default 3 min 0 max 20
option name MaterialCorrectionWeight type spin default 100 min 0 max 300
option name TmSoftDivisor type spin default 22 min 5 max 80
option name TmIncrementPercent type spin default 75 min 0 max 150
option name TmHardPercent type spin default 60 min 10 max 95
option name TmHardSoftMultiple type spin default 5 min 1 max 20
option name TmStableFactor type spin default 60 min 20 max 150
option name TmSemiStableFactor type spin default 80 min 20 max 150
option name TmUnstableFactor type spin default 140 min 50 max 300
option name TmEffortBase type spin default 155 min 100 max 250
option name TmFallingEvalPercent type spin default 100 min 0 max 400
option name TmMinFactorPercent type spin default 45 min 10 max 100
option name CaptureFutilityBase type spin default 0 min 0 max 1000
option name CaptureFutilityMultiplier type spin default 250 min 0 max 1000
option name CaptureFutilityDepth type spin default 6 min 0 max 15
option name FailLowContinuationBonus type spin default 0 min 0 max 300
option name Clear Hash type button
uciok
readyok
info string eval hce 18 nnue 20 sum 38
info string eval hce -52 nnue 63 sum 11
info string eval hce -52 nnue off sum -52
```

The same transcript was run on a binary built from `origin/lock/combo29-20261110` with the same `g++` Release command. The lock prints the `uci` banner and then nothing for `eval`, `position`, `setoption`, or `quit`. There is no `info string eval` line.

```text
git archive origin/lock/combo29-20261110 forge-combo29 | tar -x -C /tmp/lock-combo29
cmake -S /tmp/lock-combo29/forge-combo29 -B /tmp/lock-combo29/build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/lock-combo29/build -j"$(nproc)"
cat forge-combo29/tests_t9/eval_commands.txt | /tmp/lock-combo29/build/forge
```

Configure and build:

```text
-- The CXX compiler identification is GNU 13.3.0
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Check for working CXX compiler: /usr/bin/g++ - skipped
-- Detecting CXX compile features
-- Detecting CXX compile features - done
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD - Success
-- Found Threads: TRUE
-- Configuring done (0.2s)
-- Generating done (0.0s)
-- Build files have been written to: /tmp/lock-combo29/build
[ 11%] Building CXX object CMakeFiles/forge.dir/src/bitboard.cpp.o
[ 22%] Building CXX object CMakeFiles/forge.dir/src/board.cpp.o
[ 33%] Building CXX object CMakeFiles/forge.dir/src/eval.cpp.o
[ 44%] Building CXX object CMakeFiles/forge.dir/src/book.cpp.o
[ 55%] Building CXX object CMakeFiles/forge.dir/src/eval_params.cpp.o
[ 66%] Building CXX object CMakeFiles/forge.dir/src/nnue.cpp.o
[ 77%] Building CXX object CMakeFiles/forge.dir/src/search.cpp.o
[ 88%] Building CXX object CMakeFiles/forge.dir/src/uci.cpp.o
[100%] Linking CXX executable forge
[100%] Built target forge
```

Full lock transcript:

```text
id name Chess Engine Forge 6.4.24 candidate
id author OpenAI
option name Hash type spin default 32 min 1 max 2048
option name Threads type spin default 1 min 1 max 256
option name Move Overhead type spin default 10 min 0 max 1000
option name Ponder type check default false
option name OwnBook type check default true
option name Book File type string default <empty>
option name Book Depth type spin default 30 min 0 max 100
option name Book Variety type spin default 30 min 0 max 100
option name UseNNUE type check default true
option name LmrQuietBase type spin default 85 min 0 max 300
option name LmrQuietDivisor type spin default 220 min 100 max 500
option name LmrNoisyBase type spin default 10 min 0 max 300
option name LmrNoisyDivisor type spin default 340 min 100 max 800
option name NullMoveMinDepth type spin default 3 min 1 max 10
option name NullMoveBase type spin default 3 min 1 max 6
option name NullMoveDepthDivisor type spin default 3 min 1 max 10
option name NullMoveEvalDivisor type spin default 200 min 50 max 1000
option name RfpDepth type spin default 8 min 0 max 15
option name RfpMargin type spin default 72 min 10 max 300
option name RfpImproving type spin default 40 min 0 max 200
option name RazorDepth type spin default 2 min 0 max 6
option name RazorBase type spin default 150 min 0 max 1000
option name RazorMultiplier type spin default 350 min 0 max 1000
option name FutilityDepth type spin default 7 min 0 max 15
option name FutilityBase type spin default 100 min 0 max 500
option name FutilityMultiplier type spin default 110 min 0 max 500
option name LmpBase type spin default 4 min 0 max 20
option name HistoryPruneDepth type spin default 3 min 0 max 10
option name HistoryPruneMultiplier type spin default 2048 min 0 max 20000
option name SeeQuietMultiplier type spin default 24 min 0 max 200
option name SeeNoisyMultiplier type spin default 150 min 0 max 1000
option name SingularDepth type spin default 7 min 2 max 20
option name SingularMargin type spin default 2 min 0 max 10
option name IirDepth type spin default 4 min 1 max 20
option name ProbcutDepth type spin default 5 min 1 max 20
option name ProbcutMargin type spin default 180 min 0 max 1000
option name QsFutilityMargin type spin default 160 min 0 max 1000
option name QsSeeMargin type spin default 40 min 0 max 500
option name AspirationDelta type spin default 18 min 4 max 200
option name HistoryBonusQuadratic type spin default 20 min 0 max 100
option name HistoryBonusLinear type spin default 48 min 0 max 500
option name HistoryBonusMax type spin default 2048 min 100 max 10000
option name LmrHistoryDivisor type spin default 6000 min 1000 max 30000
option name CheckExtensionDepth type spin default 2 min 1 max 30
option name LmrCutoffThreshold type spin default 3 min 0 max 20
option name MaterialCorrectionWeight type spin default 100 min 0 max 300
option name TmSoftDivisor type spin default 22 min 5 max 80
option name TmIncrementPercent type spin default 75 min 0 max 150
option name TmHardPercent type spin default 60 min 10 max 95
option name TmHardSoftMultiple type spin default 5 min 1 max 20
option name TmStableFactor type spin default 60 min 20 max 150
option name TmSemiStableFactor type spin default 80 min 20 max 150
option name TmUnstableFactor type spin default 140 min 50 max 300
option name TmEffortBase type spin default 155 min 100 max 250
option name TmFallingEvalPercent type spin default 100 min 0 max 400
option name TmMinFactorPercent type spin default 45 min 10 max 100
option name CaptureFutilityBase type spin default 0 min 0 max 1000
option name CaptureFutilityMultiplier type spin default 250 min 0 max 1000
option name CaptureFutilityDepth type spin default 6 min 0 max 15
option name FailLowContinuationBonus type spin default 0 min 0 max 300
option name Clear Hash type button
uciok
readyok
```

The C++ test, compiled and linked with the same defines as the release engine (`NDEBUG`, `FORGE_NNUE_HIDDEN=256`, `FORGE_EXPOSE_TUNABLES=1`, `FORGE_SPD_TT_NOTLS=1`, `FORGE_SPD_NO_ZERO_MOVELISTS=2`, `FORGE_SEARCH_SPEED2=1`, `FORGE_SPD_PREFETCH_EARLY=1`, `FORGE_SPD_SLIDER_PEXT=1`, `FORGE_SPD_NNUE_ZMM=1`), `-O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4`, against every `src/*.cpp` except `uci.cpp`:

```text
g++ -std=c++20 -ffp-contract=off -fno-fast-math -march=x86-64-v4 -DNDEBUG -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_NNUE_HIDDEN=256 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_TT_NOTLS=1 -I/agent/repos/dwqww/forge-combo29/include -O3 /agent/repos/dwqww/forge-combo29/tests_t9/eval_test.cpp /agent/repos/dwqww/forge-combo29/src/bitboard.cpp /agent/repos/dwqww/forge-combo29/src/book.cpp /agent/repos/dwqww/forge-combo29/src/board.cpp /agent/repos/dwqww/forge-combo29/src/eval.cpp /agent/repos/dwqww/forge-combo29/src/eval_params.cpp /agent/repos/dwqww/forge-combo29/src/nnue.cpp /agent/repos/dwqww/forge-combo29/src/search.cpp -pthread -o /tmp/forge-t9-eval-test
/tmp/forge-t9-eval-test
```

The compiler printed nothing. The program printed:

```text
info string eval hce 18 nnue 20 sum 38
info string eval hce -52 nnue 63 sum 11
info string eval hce -52 nnue off sum -52
```

Exit status 0.

The same sources again with `-O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer`:

```text
g++ -std=c++20 -ffp-contract=off -fno-fast-math -march=x86-64-v4 -DNDEBUG -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_NNUE_HIDDEN=256 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_TT_NOTLS=1 -I/agent/repos/dwqww/forge-combo29/include -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer /agent/repos/dwqww/forge-combo29/tests_t9/eval_test.cpp /agent/repos/dwqww/forge-combo29/src/bitboard.cpp /agent/repos/dwqww/forge-combo29/src/book.cpp /agent/repos/dwqww/forge-combo29/src/board.cpp /agent/repos/dwqww/forge-combo29/src/eval.cpp /agent/repos/dwqww/forge-combo29/src/eval_params.cpp /agent/repos/dwqww/forge-combo29/src/nnue.cpp /agent/repos/dwqww/forge-combo29/src/search.cpp -pthread -o /tmp/forge-t9-eval-test-san
/tmp/forge-t9-eval-test-san
```

The compiler printed nothing. AddressSanitizer and UndefinedBehaviorSanitizer printed nothing. The program printed the same three lines and exited 0.

The same test file compiled against the lock headers fails, because `eval_report` does not exist there:

```text
g++ -std=c++20 -c /agent/repos/dwqww/forge-combo29/tests_t9/eval_test.cpp -I/tmp/lock-combo29/forge-combo29/include -o /tmp/lock-eval-test.o
```

```text
/agent/repos/dwqww/forge-combo29/tests_t9/eval_test.cpp: In function ‘int main()’:
/agent/repos/dwqww/forge-combo29/tests_t9/eval_test.cpp:63:38: error: ‘eval_report’ is not a member of ‘forge’
   63 |     const std::string start = forge::eval_report(board);
      |                                      ^~~~~~~~~~~
/agent/repos/dwqww/forge-combo29/tests_t9/eval_test.cpp:79:38: error: ‘eval_report’ is not a member of ‘forge’
   79 |     const std::string after = forge::eval_report(board);
      |                                      ^~~~~~~~~~~
/agent/repos/dwqww/forge-combo29/tests_t9/eval_test.cpp:92:36: error: ‘eval_report’ is not a member of ‘forge’
   92 |     const std::string off = forge::eval_report(board);
      |                                    ^~~~~~~~~~~
```

The compiler exit status was 1.

## What was not verified

- `Worker::static_evaluate` was not called, so the printed sum was not compared with the clamped `evaluate_runtime + network` value search uses.
- The Windows Clang ThinLTO+PGO recipe under `windows_build/` was not built. Bench and perft were measured with g++ 13.3.0 only.
- Clang 18 was not used for the engine. CMake's probe failed at link time with `cannot find -lstdc++` before any Forge file was compiled.
- No GUI was attached. The transcript was piped to the binary on this machine.
- No position other than the start position and the position after `e2e4` was printed. The test checks the arithmetic identity on those two, and the `UseNNUE false` line on the second.
