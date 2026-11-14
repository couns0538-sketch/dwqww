# t16: options report unknown names and bad values

## What was wrong

The whole `setoption` handler is in `forge-combo29/src/uci.cpp`. It already stopped a running search before touching an option, and it already built names that contain spaces (`Move Overhead`, `Book File`, `Clear Hash`) by reading tokens until the word `value`. Name matching was, and still is, case-sensitive. The bug was what happened after the name and the value had been read.

The handler was one long `if` / `else if` chain and that chain had no final `else`. If the name matched nothing, the function simply returned to the command loop. The engine printed nothing and stored nothing. A mistyped name in a match setup therefore left the previous setting in force, and the GUI had no line to show that the command had missed.

These commands were silent before the change. None of them altered an option:

- `setoption name hash value 16` — `hash` is not `Hash`. The hash stayed at its real size (the constructor default is 32 MB).
- `setoption name Not An Option value 1`
- `setoption name FooBar value true`
- `setoption name` — the `name` keyword is present and no name follows, so the parsed name is empty.
- `setoption` — the `name` keyword itself is missing, so the parser never reads a name. Same empty name, same silence.
- `setoption name value 1` — the next token is `value`, so the name stays empty.

A wrong-case option is the dangerous one. `Hash` is a real option. `hash` was treated as "not my problem" and the engine kept searching with the old hash.

The second fault was silent clamping of integers that do parse but sit outside the range printed by `uci`. For every spin, the old code did this: `std::from_chars` the token, and on success store `std::clamp(value, minimum, maximum)` with no test of whether `value` was already inside that range and with no `info` line. The `uci` answer advertises the min and max. The operator who typed a number outside that range got the clamped number and no warning.

What that did, option by option:

- `Hash` is advertised `min 1 max 2048`, default 32. `Hash 0` was stored as 1 and the table was resized to 1 MB. `Hash 2049` was stored as 2048. `Threads -1` was stored as 1 (the handler clamps, and `Searcher::set_threads` clamps again). `Threads 257` was stored as 256. `Move Overhead -1` became 0. `Move Overhead 1001` became 1000. No line was printed for any of those.
- `Book Depth -1` became 0. That is not a harmless clamp. Book moves are played only when `game_ply < book_depth`. The start position has ply 0, so depth 0 turns the book off even while `OwnBook` is still true. A negative depth typed by mistake silently stopped book moves. `Book Depth 101` became 100, which keeps the book on for a normal game and again printed nothing. `Book Variety -1` became 0, which forces the single heaviest book move. `Book Variety 101` became 100, which widens the random choice to almost every weighted move. Both were silent.
- The same pattern covered all 51 search tunables (`LmrQuietBase` through `FailLowContinuationBonus`). `LmrQuietBase` starts at 85, min 0, max 300. `setoption name LmrQuietBase value -1` wrote 0 and called `tune::refresh()`, which rebuilds the reduction tables used by every search, including `bench`. The command printed nothing. A later `uci` would show `default 0` for that tunable, because tunable lines print the live value in the `default` field, but the `setoption` that caused it was silent at the time.

Values that are not integers were already handled. `Hash abc`, `Threads 1x`, `Hash +16`, an empty value on a spin, and an integer that does not fit in `int` already printed `info string invalid value for option <name>` and did not store. `Ponder`, `OwnBook`, and `UseNNUE` already rejected anything other than the exact words `true` and `false` with that same line. `Book File` already printed `info string loaded book <path> with <n> entries` on success and `info string cannot load book <path>` on failure, and a failed load left the previous book in place. Those paths were not the bug. The bug was the missing message for an unknown name, and the missing message when a parsed integer fell outside the advertised range and was clamped.

Two rejected commands still changed engine state:

- `UseNNUE`. The flag was set only for `true` and `false`, and the invalid branch printed the message, but `searcher.clear_hash()` stood after the `if` / `else`. `setoption name UseNNUE value yes` printed `invalid value` and then wiped the transposition table and the evaluation caches anyway. The NNUE flag stayed at its old value. The search state did not.
- `Clear Hash`. It is a button. The UCI command for a button carries no value. The old handler ignored `value_text` and always called `searcher.clear_hash()`. `setoption name Clear Hash value nope` was not reported, and the table was cleared.

`setoption` during a search was not this bug. The handler's first action was already `stop_search()`, which sets the stop flag, wakes the search thread, and joins it before the option is applied. A `setoption` sent while `go infinite` or `go movetime` is running stops that search and then applies the option. That path did not crash. It was checked again after the edit.

## What I found

Compared with the `uci` answer, at startup of this build (`FORGE_EXPOSE_TUNABLES=1`, `nnue_weights.inc` present, `book_data.inc` present with 2616 entries) the names `setoption` accepts and the names `uci` prints are the same 61 options. The ranges in that printout are the same numbers the handler clamps to. The starting values match the advertised defaults: Hash 32 MB (`Searcher`'s default), Threads 1, Move Overhead 10, Ponder false, OwnBook true because an embedded book is compiled in, Book File empty (the embedded book is loaded, not a file), Book Depth 30, Book Variety 30, UseNNUE true. Each tunable's initializer in `src/search.cpp` matches the `default` / `min` / `max` printed below. There is no startup mismatch of a number.

These are the real differences between the printed list and the handler:

1. Tunables are printed only inside `#ifdef FORGE_EXPOSE_TUNABLES`. `setoption` accepts them whether or not that macro is set. This CMake build sets it to 1, so they appear in `uci` and they are accepted. A build without the macro would still apply them and would not list them.
2. `UseNNUE` is printed only when `nnue::available()` is true. `setoption` always accepts the name. This binary has the network, so the option is listed. Without the network the name would still be accepted and search would ignore the flag.
3. Hash, Threads, Move Overhead, Ponder, OwnBook, Book File, Book Depth, Book Variety, UseNNUE, and Clear Hash advertise fixed default words. A later `uci` still prints those words after the live value has changed. Tunable lines print the live integer in the `default` field, so a later `uci` shows the change. That is how `LmrQuietBase -1` can be seen afterwards as `default 0`.
4. `OwnBook`'s advertised default is `embedded_available()` (true here). The runtime flag starts at that same value. After `setoption name OwnBook value false` the next `uci` still says `default true`.
5. `Book File` advertises `default <empty>`. The path string starts empty and the book in memory is the embedded book. The value `<empty>`, or a `Book File` command with no value, clears the path and reloads the embedded book. A missing file prints `info string cannot load book <path>` and keeps the previous book. `Book::load_file` also returns false, without replacing the book, when the file is shorter than 16 bytes. A string option has no min/max, so that existing load line is the failure report. It was not replaced with `invalid value`.
6. `Clear Hash` is printed as `option name Clear Hash type button` with no default, min, or max. That matches a button.

`bench` builds its own `Searcher(16)` and does not read the Hash option, the Threads option, or the book. `go perft` does not either. The reference command still sets Threads 1, Hash 16, and OwnBook false. The three node counts were taken before the edit and again after it.

## What changed

Only `forge-combo29/src/uci.cpp` changed in the engine (44 insertions, 46 deletions).

- The chain now ends with an `else`. An unmatched name prints `info string unknown option <name>` and does not write any option. An empty name prints that line with an empty name (`info string unknown option `).
- Spin options go through one helper. If the token is not a complete integer, the helper prints `info string invalid value for option <name>` and returns without storing. If the integer is outside the advertised min/max, the helper prints that same line and then stores the clamped value, which is what the lock already did. Hash 0 still becomes 1 MB, and it now says so. Threads -1 still becomes 1, and it now says so. Book Depth -1 still becomes 0, and it now says so. The same helper covers the 51 tunables, so `LmrQuietBase -1` still writes 0 and still calls `tune::refresh()`, and it now prints the invalid line first.
- `Ponder`, `OwnBook`, and `UseNNUE` still accept only `true` and `false`. Anything else prints the invalid line and leaves the flag as it was.
- `UseNNUE` calls `clear_hash()` only after `true` or `false` has been accepted. A rejected token no longer wipes the table.
- `Clear Hash` with no value still clears the hash and prints nothing. A non-empty value prints the invalid line and does not clear.
- `Book File` is unchanged: spaces in the path still work, `<empty>` and an empty value reload the embedded book, a good file prints the loaded-book line, a bad path prints `cannot load book` and keeps the old book.
- Case rules are unchanged. `Move Overhead`, `Book File`, and `Clear Hash` still work.
- The comment above the tunable `uci` lines no longer says that builds without `FORGE_EXPOSE_TUNABLES` accept those options silently. They are still accepted. An out-of-range value is now reported.

In-range values behave as before: Hash 1, 16, and 2048, Threads 1, 2, and 256, Move Overhead 0, 10, and 1000, both states of each check, each tunable's own default, and Clear Hash with no value produce no error line. After every tunable was set out of range and then restored, a second `uci` matched the first `uci` byte for byte, so the advertised defaults were back where they started.

Reference numbers after the change, with Threads 1, Hash 16, OwnBook false: bench 11 = 312866, bench 13 = 862329, `go perft 5` from the start position = 4865609. Those are the same three counts as before the edit.

## What I found (option table)

This is the `uci` list captured before the edit. The options transcript prints `uci` again after every option has been set and restored, and the two blocks match, so the edit did not change the advertised list.

| Name | Type | Default | Min | Max |
| --- | --- | --- | --- | --- |
| Hash | spin | 32 | 1 | 2048 |
| Threads | spin | 1 | 1 | 256 |
| Move Overhead | spin | 10 | 0 | 1000 |
| Ponder | check | false | — | — |
| OwnBook | check | true | — | — |
| Book File | string | <empty> | — | — |
| Book Depth | spin | 30 | 0 | 100 |
| Book Variety | spin | 30 | 0 | 100 |
| UseNNUE | check | true | — | — |
| LmrQuietBase | spin | 85 | 0 | 300 |
| LmrQuietDivisor | spin | 220 | 100 | 500 |
| LmrNoisyBase | spin | 10 | 0 | 300 |
| LmrNoisyDivisor | spin | 340 | 100 | 800 |
| NullMoveMinDepth | spin | 3 | 1 | 10 |
| NullMoveBase | spin | 3 | 1 | 6 |
| NullMoveDepthDivisor | spin | 3 | 1 | 10 |
| NullMoveEvalDivisor | spin | 200 | 50 | 1000 |
| RfpDepth | spin | 8 | 0 | 15 |
| RfpMargin | spin | 72 | 10 | 300 |
| RfpImproving | spin | 40 | 0 | 200 |
| RazorDepth | spin | 2 | 0 | 6 |
| RazorBase | spin | 150 | 0 | 1000 |
| RazorMultiplier | spin | 350 | 0 | 1000 |
| FutilityDepth | spin | 7 | 0 | 15 |
| FutilityBase | spin | 100 | 0 | 500 |
| FutilityMultiplier | spin | 110 | 0 | 500 |
| LmpBase | spin | 4 | 0 | 20 |
| HistoryPruneDepth | spin | 3 | 0 | 10 |
| HistoryPruneMultiplier | spin | 2048 | 0 | 20000 |
| SeeQuietMultiplier | spin | 24 | 0 | 200 |
| SeeNoisyMultiplier | spin | 150 | 0 | 1000 |
| SingularDepth | spin | 7 | 2 | 20 |
| SingularMargin | spin | 2 | 0 | 10 |
| IirDepth | spin | 4 | 1 | 20 |
| ProbcutDepth | spin | 5 | 1 | 20 |
| ProbcutMargin | spin | 180 | 0 | 1000 |
| QsFutilityMargin | spin | 160 | 0 | 1000 |
| QsSeeMargin | spin | 40 | 0 | 500 |
| AspirationDelta | spin | 18 | 4 | 200 |
| HistoryBonusQuadratic | spin | 20 | 0 | 100 |
| HistoryBonusLinear | spin | 48 | 0 | 500 |
| HistoryBonusMax | spin | 2048 | 100 | 10000 |
| LmrHistoryDivisor | spin | 6000 | 1000 | 30000 |
| CheckExtensionDepth | spin | 2 | 1 | 30 |
| LmrCutoffThreshold | spin | 3 | 0 | 20 |
| MaterialCorrectionWeight | spin | 100 | 0 | 300 |
| TmSoftDivisor | spin | 22 | 5 | 80 |
| TmIncrementPercent | spin | 75 | 0 | 150 |
| TmHardPercent | spin | 60 | 10 | 95 |
| TmHardSoftMultiple | spin | 5 | 1 | 20 |
| TmStableFactor | spin | 60 | 20 | 150 |
| TmSemiStableFactor | spin | 80 | 20 | 150 |
| TmUnstableFactor | spin | 140 | 50 | 300 |
| TmEffortBase | spin | 155 | 100 | 250 |
| TmFallingEvalPercent | spin | 100 | 0 | 400 |
| TmMinFactorPercent | spin | 45 | 10 | 100 |
| CaptureFutilityBase | spin | 0 | 0 | 1000 |
| CaptureFutilityMultiplier | spin | 250 | 0 | 1000 |
| CaptureFutilityDepth | spin | 6 | 0 | 15 |
| FailLowContinuationBonus | spin | 0 | 0 | 300 |
| Clear Hash | button | — | — | — |

## Files changed

- `forge-combo29/src/uci.cpp` — unknown-option line, range message on the existing clamp, Clear Hash and UseNNUE rejection paths.
- `forge-combo29/tests_t16/options.in.txt` and `options.expected.txt` — one good value and one bad value for every option, three unknown names, an empty name, a name with no value. Exact stdout.
- `forge-combo29/tests_t16/clamp.in.txt` and `clamp.expected.txt` — `LmrQuietBase -1` clamps to 0, which the next `uci` line shows as `default 0`; `abc` leaves `default 85`.
- `forge-combo29/tests_t16/ownbook.in.txt` and `ownbook.spec.txt` — OwnBook off with the embedded book, with a book file loaded before OwnBook false, and with a book file loaded after OwnBook false. Also Book Depth and Book Variety clamps, and Ponder.
- `forge-combo29/tests_t16/search.in.txt` and `search.spec.txt` — `setoption` while `go infinite` and `go movetime 10000` are running.
- `forge-combo29/tests_t16/check_lines.cpp` — reads a transcript and a spec. It does not start a process or write a file.
- `forge-combo29/tests_t16/start h2h4.book` — 16-byte Polyglot book, one start-position entry, move h2h4, weight 100. Bytes: `463b96181691fc9c 03df 0064 00000000`.
- `forge-combo29/REPORT_t16.md` — this file.

## Commands and output

The machine's clang selects GCC 14. The first configure failed because `ld` could not find `-lstdc++`. Installing `g++-14` and `libstdc++-14-dev` provided `/usr/lib/gcc/x86_64-linux-gnu/14/libstdc++.so`. The CPU has AVX-512 (`avx512f` is in `lscpu`). The build still used the task's portable flags.

### Configure before the toolchain fix

`cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`

```
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

    Change Dir: '/agent/repos/dwqww/build/CMakeFiles/CMakeScratch/TryCompile-m7qZV2'
    
    Run Build Command(s): /usr/bin/cmake -E env VERBOSE=1 /usr/bin/gmake -f Makefile cmTC_a3741/fast
    /usr/bin/gmake  -f CMakeFiles/cmTC_a3741.dir/build.make CMakeFiles/cmTC_a3741.dir/build
    gmake[1]: Entering directory '/agent/repos/dwqww/build/CMakeFiles/CMakeScratch/TryCompile-m7qZV2'
    Building CXX object CMakeFiles/cmTC_a3741.dir/testCXXCompiler.cxx.o
    /usr/bin/c++    -MD -MT CMakeFiles/cmTC_a3741.dir/testCXXCompiler.cxx.o -MF CMakeFiles/cmTC_a3741.dir/testCXXCompiler.cxx.o.d -o CMakeFiles/cmTC_a3741.dir/testCXXCompiler.cxx.o -c /agent/repos/dwqww/build/CMakeFiles/CMakeScratch/TryCompile-m7qZV2/testCXXCompiler.cxx
    Linking CXX executable cmTC_a3741
    /usr/bin/cmake -E cmake_link_script CMakeFiles/cmTC_a3741.dir/link.txt --verbose=1
    /usr/bin/c++ CMakeFiles/cmTC_a3741.dir/testCXXCompiler.cxx.o -o cmTC_a3741 
    /usr/bin/ld: cannot find -lstdc++: No such file or directory
    c++: error: linker command failed with exit code 1 (use -v to see invocation)
    gmake[1]: *** [CMakeFiles/cmTC_a3741.dir/build.make:100: cmTC_a3741] Error 1
    gmake[1]: Leaving directory '/agent/repos/dwqww/build/CMakeFiles/CMakeScratch/TryCompile-m7qZV2'
    gmake: *** [Makefile:127: cmTC_a3741/fast] Error 2

  CMake will not be able to correctly generate this project.
Call Stack (most recent call first):
  CMakeLists.txt:5 (project)
```


### Configure and build after `g++-14` and `libstdc++-14-dev`

`rm -rf build && cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 && cmake --build build -j`

```
-- The CXX compiler identification is Clang 18.1.3
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Check for working CXX compiler: /usr/bin/c++ - skipped
-- Detecting CXX compile features
-- Detecting CXX compile features - done
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD - Success
-- Found Threads: TRUE  
-- Configuring done (0.4s)
-- Generating done (0.0s)
-- Build files have been written to: /agent/repos/dwqww/build
[ 11%] Building CXX object CMakeFiles/forge.dir/src/bitboard.cpp.o
[ 22%] Building CXX object CMakeFiles/forge.dir/src/board.cpp.o
[ 33%] Building CXX object CMakeFiles/forge.dir/src/eval.cpp.o
[ 44%] Building CXX object CMakeFiles/forge.dir/src/book.cpp.o
[ 55%] Building CXX object CMakeFiles/forge.dir/src/nnue.cpp.o
[ 66%] Building CXX object CMakeFiles/forge.dir/src/eval_params.cpp.o
[ 77%] Building CXX object CMakeFiles/forge.dir/src/search.cpp.o
[ 88%] Building CXX object CMakeFiles/forge.dir/src/uci.cpp.o
[100%] Linking CXX executable forge
[100%] Built target forge
```


### Reference numbers before any engine edit

`printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build/forge`

```
info string bench depth 11 nodes 312866 time 157 nps 1992777
info string bench depth 13 nodes 862329 time 420 nps 2053164
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


bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609.

### Reference numbers after the change

Same command, final source (including the comment under `FORGE_EXPOSE_TUNABLES`). Time and nps move between runs. The node counts do not.

```
info string bench depth 11 nodes 312866 time 186 nps 1682075
info string bench depth 13 nodes 862329 time 501 nps 1721215
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


bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609.

### Option transcript

`./build/forge < forge-combo29/tests_t16/options.in.txt > /tmp/t16_options.out`

`diff -u forge-combo29/tests_t16/options.expected.txt /tmp/t16_options.out`

`diff` produced no output and exited 0. Full engine stdout:

```
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
info string invalid value for option Hash
info string invalid value for option Hash
info string invalid value for option Hash
info string invalid value for option Threads
info string invalid value for option Threads
info string invalid value for option Threads
info string invalid value for option Move Overhead
info string invalid value for option Move Overhead
info string invalid value for option Ponder
info string invalid value for option OwnBook
info string loaded book forge-combo29/tests_t16/start h2h4.book with 1 entries
info string cannot load book forge-combo29/tests_t16/no-such-book
info string invalid value for option Book Depth
info string invalid value for option Book Depth
info string invalid value for option Book Variety
info string invalid value for option Book Variety
info string invalid value for option UseNNUE
info string invalid value for option LmrQuietBase
info string invalid value for option LmrQuietDivisor
info string invalid value for option LmrNoisyBase
info string invalid value for option LmrNoisyDivisor
info string invalid value for option NullMoveMinDepth
info string invalid value for option NullMoveBase
info string invalid value for option NullMoveDepthDivisor
info string invalid value for option NullMoveEvalDivisor
info string invalid value for option RfpDepth
info string invalid value for option RfpMargin
info string invalid value for option RfpImproving
info string invalid value for option RazorDepth
info string invalid value for option RazorBase
info string invalid value for option RazorMultiplier
info string invalid value for option FutilityDepth
info string invalid value for option FutilityBase
info string invalid value for option FutilityMultiplier
info string invalid value for option LmpBase
info string invalid value for option HistoryPruneDepth
info string invalid value for option HistoryPruneMultiplier
info string invalid value for option SeeQuietMultiplier
info string invalid value for option SeeNoisyMultiplier
info string invalid value for option SingularDepth
info string invalid value for option SingularMargin
info string invalid value for option IirDepth
info string invalid value for option ProbcutDepth
info string invalid value for option ProbcutMargin
info string invalid value for option QsFutilityMargin
info string invalid value for option QsSeeMargin
info string invalid value for option AspirationDelta
info string invalid value for option HistoryBonusQuadratic
info string invalid value for option HistoryBonusLinear
info string invalid value for option HistoryBonusMax
info string invalid value for option LmrHistoryDivisor
info string invalid value for option CheckExtensionDepth
info string invalid value for option LmrCutoffThreshold
info string invalid value for option MaterialCorrectionWeight
info string invalid value for option TmSoftDivisor
info string invalid value for option TmIncrementPercent
info string invalid value for option TmHardPercent
info string invalid value for option TmHardSoftMultiple
info string invalid value for option TmStableFactor
info string invalid value for option TmSemiStableFactor
info string invalid value for option TmUnstableFactor
info string invalid value for option TmEffortBase
info string invalid value for option TmFallingEvalPercent
info string invalid value for option TmMinFactorPercent
info string invalid value for option CaptureFutilityBase
info string invalid value for option CaptureFutilityMultiplier
info string invalid value for option CaptureFutilityDepth
info string invalid value for option FailLowContinuationBonus
info string invalid value for option Clear Hash
info string unknown option hash
info string unknown option Not An Option
info string unknown option FooBar
info string unknown option 
info string unknown option 
info string unknown option 
info string invalid value for option Threads
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


The three `info string unknown option ` lines (trailing space, empty name) are `setoption name`, `setoption`, and `setoption name value 1`. `setoption name Threads` with no value is `info string invalid value for option Threads`. The second `uci` block matches the first, so every tunable was restored to the default the first block advertised. Good values (Hash 1, 16, and 2048, Threads 1, 2, and 256, Move Overhead 0, 10, and 1000, both check states, Book File `<empty>`, each tunable's default, Clear Hash with no value) produced no `invalid` or `unknown` line.

### Tunable clamp visible on the next `uci`

`./build/forge < forge-combo29/tests_t16/clamp.in.txt > /tmp/t16_clamp.out`

`diff -u forge-combo29/tests_t16/clamp.expected.txt /tmp/t16_clamp.out`

`diff` produced no output and exited 0. The expected file was built from the pre-change `uci` text by changing `LmrQuietBase` `default 85` to `default 0` in the first banner only. Full stdout:

```
info string invalid value for option LmrQuietBase
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
option name LmrQuietBase type spin default 0 min 0 max 300
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
info string invalid value for option LmrQuietBase
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
```


`LmrQuietBase -1` prints the invalid line and the following `uci` says `default 0` (the minimum). Restoring 85 prints nothing and the next `uci` says `default 85`. `abc` prints the invalid line and the following `uci` still says `default 85`.

### OwnBook and Book File

`c++ -std=c++20 -Wall -Wextra -o /tmp/t16_check forge-combo29/tests_t16/check_lines.cpp`

That compile printed nothing and exited 0.

`./build/forge < forge-combo29/tests_t16/ownbook.in.txt > /tmp/t16_ownbook.out`

`/tmp/t16_check /tmp/t16_ownbook.out forge-combo29/tests_t16/ownbook.spec.txt`

```
ok 54 lines
```

Full stdout:

```
info string book move e2e4
bestmove e2e4
bestmove a2a3
info string invalid value for option Book Depth
bestmove a2a3
info string book move e2e4
bestmove e2e4
info string invalid value for option Book Depth
info string book move e2e4
bestmove e2e4
info string invalid value for option Book Variety
info string book move e2e4
bestmove e2e4
info string book move e2e4
bestmove e2e4
info string book move e2e4
bestmove e2e4
info string book move e2e4
bestmove e2e4
info string book move e2e4
bestmove e2e4
info string book move e2e4
bestmove e2e4
info string book move e2e4
bestmove e2e4
info string book move e2e4
bestmove e2e4
info string loaded book forge-combo29/tests_t16/start h2h4.book with 1 entries
bestmove a2a3
info string book move h2h4
bestmove h2h4
bestmove a2a3
info string book move e2e4
bestmove e2e4
info string loaded book forge-combo29/tests_t16/start h2h4.book with 1 entries
info string book move h2h4
bestmove h2h4
bestmove a2a3
info string cannot load book forge-combo29/tests_t16/no-such-book
info string book move h2h4
bestmove h2h4
info string book move e2e4
bestmove e2e4
info string book move e2e4
bestmove e2e4 ponder c7c5
info string invalid value for option Ponder
info string book move e2e4
bestmove e2e4 ponder c7c5
info string book move e2e4
bestmove e2e4
info string invalid value for option OwnBook
info string book move e2e4
bestmove e2e4
bestmove a2a3
```


Reading that log: embedded book with variety 0 plays `e2e4`. OwnBook false then plays no book move. Book Depth -1 prints invalid and, with OwnBook true, still plays no book move, which is the clamp to 0 (a rejected -1 would have left depth 30 and played `e2e4`). Depth 1 plays `e2e4` again. Depth 101 prints invalid and still plays `e2e4` (clamp to 100). Variety -1 after variety 100 prints invalid, then eight probes are `e2e4`, the heaviest embedded move (variety 0). The file `start h2h4.book` loaded while OwnBook is false prints `loaded book ... with 1 entries` and the next search has no book move; OwnBook true then plays `h2h4`. OwnBook false after that load has no book move. `<empty>` restores `e2e4`. Loading the same file while OwnBook is already true plays `h2h4`, and OwnBook false afterwards has no book move. `no-such-book` prints `cannot load book` and the next search still plays `h2h4`. Ponder true adds `ponder c7c5`; `yes` prints invalid and the ponder reply stays; `false` removes it. OwnBook `yes` prints invalid and the book still plays; OwnBook false then has no book move.

The same ownbook and search checks were run four more times on this binary. Each ownbook check printed `ok 54 lines` and each search check printed `ok 7 lines`.

### setoption during search

`./build/forge < forge-combo29/tests_t16/search.in.txt > /tmp/t16_search.out`

`/tmp/t16_check /tmp/t16_search.out forge-combo29/tests_t16/search.spec.txt`

```
ok 7 lines
```

Full stdout:

```
bestmove a2a3
bestmove a2a3
info string invalid value for option Threads
bestmove a2a3
info string unknown option Not During Search
bestmove a2a3
bestmove a2a3
```


`setoption` is still the call that joins the search thread before the option is applied, so `bestmove` is printed, then the invalid or unknown line. Hash 32 and Move Overhead 10 and Threads 1 produce no such line. Exit status was 0. These runs stopped before an `info depth` line; the spec allows those lines if a search prints them. `bestmove a2a3` here is the first legal root move returned when the search is stopped before it finishes an iteration. The spec checks the `bestmove` prefix, and it checks that a book-off answer is not labelled `book move`.

### Sanitizer build

The first sanitizer configure failed until `libclang-rt-18-dev` was installed:

```
/usr/bin/ld: cannot find /usr/lib/llvm-18/lib/clang/18/lib/linux/libclang_rt.asan_static-x86_64.a: No such file or directory
/usr/bin/ld: cannot find /usr/lib/llvm-18/lib/clang/18/lib/linux/libclang_rt.asan-x86_64.a: No such file or directory
/usr/bin/ld: cannot find /usr/lib/llvm-18/lib/clang/18/lib/linux/libclang_rt.asan_cxx-x86_64.a: No such file or directory
c++: error: linker command failed with exit code 1 (use -v to see invocation)
```


Then:

`rm -rf build-san && cmake -S forge-combo29 -B build-san -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer" -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined" && cmake --build build-san -j`

Configure succeeded. `build-san/CMakeFiles/forge.dir/flags.make` contains `-fsanitize=address,undefined -fno-omit-frame-pointer`. `nm build-san/forge` shows `__asan_*` and `__ubsan_*`.

```
export ASAN_OPTIONS=halt_on_error=1:detect_leaks=1:abort_on_error=1
export UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1:abort_on_error=1
./build-san/forge < forge-combo29/tests_t16/options.in.txt > /tmp/t16_san_options.out 2>/tmp/t16_san_options.err
diff -q forge-combo29/tests_t16/options.expected.txt /tmp/t16_san_options.out
./build-san/forge < forge-combo29/tests_t16/clamp.in.txt > /tmp/t16_san_clamp.out 2>/tmp/t16_san_clamp.err
diff -q forge-combo29/tests_t16/clamp.expected.txt /tmp/t16_san_clamp.out
./build-san/forge < forge-combo29/tests_t16/ownbook.in.txt > /tmp/t16_san_ownbook.out 2>/tmp/t16_san_ownbook.err
/tmp/t16_check /tmp/t16_san_ownbook.out forge-combo29/tests_t16/ownbook.spec.txt
./build-san/forge < forge-combo29/tests_t16/search.in.txt > /tmp/t16_san_search.out 2>/tmp/t16_san_search.err
/tmp/t16_check /tmp/t16_san_search.out forge-combo29/tests_t16/search.spec.txt
wc -c /tmp/t16_san_options.err /tmp/t16_san_clamp.err /tmp/t16_san_ownbook.err /tmp/t16_san_search.err
```

Output of that run:

```
SAN_OPTIONS_OK
SAN_CLAMP_OK
ok 54 lines
ok 7 lines
0 /tmp/t16_san_options.err
0 /tmp/t16_san_clamp.err
0 /tmp/t16_san_ownbook.err
0 /tmp/t16_san_search.err
0 total
```

Each `diff -q` was empty (exit 0), so the sanitizer stdout is the same bytes as the release transcripts above. stderr was empty. Leak detection was on. No ASan or UBSan report.

`c++ -std=c++20 -Wall -Wextra -Wpedantic` on `src/uci.cpp` (same `FORGE_*` defines as the release build) and on `tests_t16/check_lines.cpp` printed no warnings.

## What I could not verify

- The live Hash, Threads, and Move Overhead values after a clamp. `uci` prints a fixed default for those three, and nothing else prints the size, the thread count, or the overhead. `LmrQuietBase`, Book Depth, and Book Variety go through the same clamp-and-report helper, and those three are visible in the transcripts above.
- Whether Clear Hash with no value removes table entries, and whether a rejected Clear Hash value leaves them in place. These runs never printed `hashfull`, because the following command stopped the search first.
- Whether UseNNUE true or false changes the score, and whether a rejected UseNNUE value leaves the table untouched. Accepted `true` and `false` still call `clear_hash`. A pinned score line was not taken: `info` lines carry time and nps, and the next piped command stops the search.
- `setoption` overlapping a search that has already reached depth 1 or more, and `setoption` with Threads greater than 1 while workers are still inside `search`. The search transcript joins the worker first; the recorded answers are the early `bestmove a2a3`.
- A book file that exists and is shorter than 16 bytes. The missing path `no-such-book` was run. `Book::load_file` returns false when the file is under 16 bytes and leaves the previous book in place; that branch was not given its own transcript.
- A GUI, and the non-portable AVX-512 kernel (`-DFORGE_PORTABLE=OFF`, `-march=x86-64-v4`). The numbers above are from the portable x86-64-v3 build the task named.
