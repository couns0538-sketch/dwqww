# Task 1: capture list overflow

## What was wrong

`MovePicker` keeps SEE-losing captures in `bad_captures_`, a `std::array<Move, 64>`, and stores them with `bad_captures_[bad_count_++] = move` (`src/search.cpp`, the write at line 469 on the lock). Nothing stops `bad_count_` at 64. The move generator can emit more than 64 captures in a legal position, and the main-search picker stores every capture that fails `see_ge(move, 0)`.

The position `3r4/Pn1Q1p2/1Q1n1QpN/1p1Q1pRB/1Qbp1QpN/2bQ1pRB/3r1QpK/2k2q2 w - - 0 1` is legal, not in check, and has 68 pseudo-legal captures with negative SEE. A depth-1 search of that position writes past the array.

## The fix

`bad_captures_` is now `std::array<Move, MoveList::Capacity>`. `MoveList::Capacity` is 256, the same bound as the generator that fills the picker. Both the uninitialized and the zero-initialized declarations were changed, so a build that does not define `FORGE_SPD_NO_ZERO_MOVELISTS` is covered too. The picker still stores every losing capture and still returns them in the same order. Positions that never pass 64 losing captures, including the bench set, walk the same prefix of the array.

## Files changed

- `forge-combo29/src/search.cpp`
- `forge-combo29/tests_t1/bad_capture_overflow.cpp`
- `forge-combo29/REPORT_t1.md`

Engine source diff: 4 insertions, 2 deletions.

## Commands and output

`/usr/bin/c++` on this machine is Clang 18.1.3 and cannot link a CMake probe (`cannot find -lstdc++`). The release build below uses `/usr/bin/g++` (GCC 13.3.0). The machine has AVX-512, so `FORGE_PORTABLE` was left off.

### Release build

```
cmake -S /agent/repos/dwqww/forge-combo29 -B /tmp/forge-t1/release -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ && cmake --build /tmp/forge-t1/release -j
```

The build completed and produced `/tmp/forge-t1/release/forge`.

### bench 11, bench 13, perft 5

```
printf '%s\n' 'uci' 'setoption name Threads value 1' 'setoption name Hash value 16' 'setoption name OwnBook value false' 'isready' 'bench 11' 'bench 13' 'position startpos' 'go perft 5' 'quit' | /tmp/forge-t1/release/forge
```

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
info string bench depth 11 nodes 312866 time 163 nps 1919423
info string bench depth 13 nodes 862329 time 428 nps 2014787
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

`bench 11` is 312866. `bench 13` is 862329. `go perft 5` from the start position is 4865609. Exit status 0.

### Overflow test on the unchanged lock

The lock file is `forge-combo29/src/search.cpp` at `16833ecc03b425586f91f4c8834dea8807bf4c22`, compiled from a temporary copy. The other objects and `tests_t1/bad_capture_overflow.cpp` are the ones used below. Flags: `-std=c++20 -O1 -g -fno-omit-frame-pointer -ffp-contract=off -fno-fast-math -march=x86-64-v4 -fsanitize=address,undefined -fno-sanitize-recover=address,undefined` and the lock defines `NDEBUG`, `FORGE_NNUE_HIDDEN=256`, `FORGE_EXPOSE_TUNABLES=1`, `FORGE_SPD_TT_NOTLS=1`, `FORGE_SPD_NO_ZERO_MOVELISTS=2`, `FORGE_SEARCH_SPEED2=1`, `FORGE_SPD_PREFETCH_EARLY=1`, `FORGE_SPD_SLIDER_PEXT=1`, `FORGE_SPD_NNUE_ZMM=1`.

```
ASAN_OPTIONS=halt_on_error=1:detect_leaks=0 UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 /tmp/forge-t1/asan/bad_capture_overflow_lock
```

```
in_check 0
losing_captures 68
AddressSanitizer:DEADLYSIGNAL
=================================================================
==13612==ERROR: AddressSanitizer: SEGV on unknown address 0x7f2230108c34 (pc 0x55a1513725b3 bp 0x7ffc95755b30 sp 0x7ffc95755a00 T0)
==13612==The signal is caused by a WRITE memory access.
    #0 0x55a1513725b3 in forge::MovePicker::next(bool) /tmp/forge-t1/search-lock.cpp:469
    #1 0x55a15135079a in forge::Worker::search(forge::Board&, forge::SearchStack*, int, int, int, bool) /tmp/forge-t1/search-lock.cpp:1305
    #2 0x55a151359d35 in forge::Worker::search(forge::Board, forge::SearchLimits const&, bool, std::vector<forge::Worker*, std::allocator<forge::Worker*> > const&) /tmp/forge-t1/search-lock.cpp:1665
    #3 0x55a151360048 in forge::Searcher::search(forge::Board, forge::SearchLimits const&, bool, forge::Searcher::TTAccess) /tmp/forge-t1/search-lock.cpp:1809
    #4 0x55a1513751ae in main /agent/repos/dwqww/forge-combo29/tests_t1/bad_capture_overflow.cpp:42
    #5 0x7f222da2a1c9  (/lib/x86_64-linux-gnu/libc.so.6+0x2a1c9) (BuildId: a4a7992a8e66555c8141ab2a08a8465ff6e0ea65)
    #6 0x7f222da2a28a in __libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: a4a7992a8e66555c8141ab2a08a8465ff6e0ea65)
    #7 0x55a1512a8f64 in _start (/tmp/forge-t1/asan/bad_capture_overflow_lock+0x12af64) (BuildId: 5019e3fe6e161d24d95a687e1ef8841ae2e45781)

AddressSanitizer can not provide additional info.
SUMMARY: AddressSanitizer: SEGV /tmp/forge-t1/search-lock.cpp:469 in forge::MovePicker::next(bool)
==13612==ABORTING
EXIT:1
```

### AddressSanitizer and UndefinedBehaviorSanitizer on the fixed test

Same flags and defines, with `src/search.cpp` from this branch.

```
ASAN_OPTIONS=halt_on_error=1:detect_leaks=0 UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 /tmp/forge-t1/asan/bad_capture_overflow
```

```
in_check 0
losing_captures 68
bestmove d3b1
nodes 176
EXIT:0
```

No ASan or UBSan diagnostic. The search returned the legal move `d3b1`.

## Not verified

- The release binary was not itself rebuilt with ASan. The sanitizer run is the test program.
- No Elo and no speed comparison. The `nps` lines above are the timing of this one release run.
- `FORGE_SDK_BADCAP_PREFIX` stays 0. That switch stores losing captures in the consumed front of `moves_` instead of `bad_captures_`. It was not enabled and not benched.
- A position that generated more than 256 captures was not run. The generator stores at most `MoveList::Capacity` moves, and with `NDEBUG` its `assert` is compiled out. This change makes the capture list as large as that generator buffer. It does not add a new check inside `MoveList::push_back`.
