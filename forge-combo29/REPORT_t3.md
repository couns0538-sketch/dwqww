# Task 3: clock parsing

Base: `lock/combo29-20261110` at `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Branch: `grok47/t3-clock-parse`.

## What was wrong

`parse_limits` in `src/uci.cpp` read `wtime`, `btime`, `winc`, `binc`, and `movetime` with `std::from_chars` into a 32-bit `int`. `3000000000` is larger than `2147483647`, so the conversion failed and the parser returned 0. The search then used a 1 ms limit and answered `bestmove` at once. A leading `+` is also rejected by `std::from_chars`, so `movetime +80` took the same path and became 0.

## The fix

Clock tokens are parsed into a signed 64-bit integer. A single leading `+` is accepted. A leading `-` clamps to 0. A token that is not a complete integer is 0, which is what a bad clock already did. A magnitude that does not fit in 64 bits clamps to `kMaxClockMs` (`INT64_MAX / 256`) instead of becoming 0, so the later multiplications in time allocation stay inside a signed 64-bit integer. `3000000000` is below that ceiling and is kept as written. `depth`, `nodes`, `mate`, and `movestogo` still use the old 32-bit reader.

## Files

- `forge-combo29/include/forge/uci_clock.hpp` (new)
- `forge-combo29/include/forge/search.hpp` (`movetime_ms`, `time_ms`, `increment_ms` are `std::int64_t`)
- `forge-combo29/src/uci.cpp` (clock keywords call `parse_clock_ms`)
- `forge-combo29/tests_t3/clock_parse_test.cpp`
- `forge-combo29/tests_t3/clock_commands.txt`

Engine diff against the lock, not counting the new header: `search.hpp` 8 lines, `uci.cpp` 17 lines. The header is 38 lines.

## Commands and output

Build directory is `/tmp/forge-t3` so the source tree stays free of object files. The flags are the lock's default Release build. This host has AVX-512, so `-DFORGE_PORTABLE` was not used. Compiler: `g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`.

### Build

```text
cmake -S /agent/repos/dwqww/forge-combo29 -B /tmp/forge-t3 -DCMAKE_BUILD_TYPE=Release && cmake --build /tmp/forge-t3 -j
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
-- Build files have been written to: /tmp/forge-t3
[ 11%] Building CXX object CMakeFiles/forge.dir/src/bitboard.cpp.o
[ 22%] Building CXX object CMakeFiles/forge.dir/src/eval.cpp.o
[ 44%] Building CXX object CMakeFiles/forge.dir/src/board.cpp.o
[ 55%] Building CXX object CMakeFiles/forge.dir/src/eval_params.cpp.o
[ 33%] Building CXX object CMakeFiles/forge.dir/src/book.cpp.o
[ 66%] Building CXX object CMakeFiles/forge.dir/src/nnue.cpp.o
[ 77%] Building CXX object CMakeFiles/forge.dir/src/uci.cpp.o
[ 88%] Building CXX object CMakeFiles/forge.dir/src/search.cpp.o
[100%] Linking CXX executable forge
[100%] Built target forge
```

The unchanged lock was built the same way to `/tmp/forge-lock-t3` before the edit. That link also ended with `[100%] Built target forge`.

### bench 11, bench 13, perft 5

```text
printf 'uci\nsetoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nisready\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/forge-t3/forge
```

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
info string bench depth 11 nodes 312866 time 165 nps 1896157
info string bench depth 13 nodes 862329 time 449 nps 1920554
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

`bench 11` is 312866 nodes, `bench 13` is 862329 nodes, and `go perft 5` from the start position is 4865609 nodes. The same three node counts were printed by `/tmp/forge-lock-t3/forge` in an earlier session that also ran the clock commands.

### Parser test

```text
g++ -std=c++20 -Wall -Wextra -Werror -I /agent/repos/dwqww/forge-combo29/include /agent/repos/dwqww/forge-combo29/tests_t3/clock_parse_test.cpp -o /tmp/clock_parse_test && /tmp/clock_parse_test
```

```text
clock_parse_test passed
```

Exit code 0. The compiler printed nothing.

Against the lock headers (`git archive origin/lock/combo29-20261110 forge-combo29/include`):

```text
g++ -std=c++20 -Wall -Wextra -Werror -I /tmp/lock-t3-inc/forge-combo29/include /agent/repos/dwqww/forge-combo29/tests_t3/clock_parse_test.cpp -o /tmp/clock_parse_test_lock
```

```text
/agent/repos/dwqww/forge-combo29/tests_t3/clock_parse_test.cpp:6:10: fatal error: forge/uci_clock.hpp: No such file or directory
    6 | #include "forge/uci_clock.hpp"
      |          ^~~~~~~~~~~~~~~~~~~~~
compilation terminated.
```

Exit code 1.

### AddressSanitizer and UndefinedBehaviorSanitizer

```text
g++ -std=c++20 -Wall -Wextra -Werror -fsanitize=address,undefined -g -I /agent/repos/dwqww/forge-combo29/include /agent/repos/dwqww/forge-combo29/tests_t3/clock_parse_test.cpp -o /tmp/clock_parse_test_asan && /tmp/clock_parse_test_asan
```

```text
clock_parse_test passed
```

Exit code 0. No sanitizer report. The compiler printed nothing.

### UCI clocks

Both binaries were given `Threads 1`, `Hash 16`, `OwnBook false`. Move Overhead stayed at its default of 10. For a clock of `3000000000` the session waited 150 ms and then sent `stop`. Timestamps are seconds after `go`.

Fixed engine, `/tmp/forge-t3/forge`:

`go wtime 3000000000 btime 3000000000` was still searching at 150 ms (last completed info: depth 16, time 137, 267839 nodes). `bestmove e2e4` came back at 0.159 s, after `stop`.

`go movetime +80` returned `bestmove d2d4` at 0.070 s. The last info line was `time 68`.

`go movetime -5` returned `bestmove d2d4` at 0.001 s.

`go movetime abc` returned `bestmove d2d4` at 0.001 s.

`position startpos moves e2e4` then `go wtime 1 btime 3000000000` was still searching at 150 ms (last completed info: depth 17, time 100, 186178 nodes). `bestmove c7c5` came back at 0.162 s, after `stop`.

Lock engine, `/tmp/forge-lock-t3/forge`, same commands, no `stop` required:

`go wtime 3000000000 btime 3000000000` returned `bestmove c2c4` at 0.001 s (depth 5, time 1).

`go movetime +80` returned `bestmove d2d4` at 0.001 s (depth 7, time 1).

`go movetime -5` returned `bestmove d2d4` at 0.001 s.

`go movetime abc` returned `bestmove c2c4` at 0.001 s.

`go wtime 1 btime 3000000000` with Black to move returned `bestmove c7c5` at 0.001 s (depth 7, time 1).

The full info lines from that session are the output of `python3 /tmp/t3_measure.py <engine>` and match the timestamps above. `bench 11`, `bench 13`, and `perft 5` in that same session were 312866, 862329, and 4865609 on both binaries.

## Not verified

- The fixed engine was not left to run for 3000000000 ms. It was stopped at 150 ms while info lines were still arriving.
- AddressSanitizer and UndefinedBehaviorSanitizer were run on `clock_parse_test`, not on the whole `forge` binary.
- `depth`, `nodes`, `mate`, and `movestogo` were not switched to the 64-bit parser. A non-integer or out-of-range value for those keywords still becomes 0, then the old clamp.
- No Elo and no speed claim. The bench node counts match the lock; the recorded bench times were 165 ms and 449 ms on this run.
