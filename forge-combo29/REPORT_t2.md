# Task 2: capture list overflow

## What was wrong

`MovePicker` in `src/search.cpp` keeps SEE-losing captures in `bad_captures_` while it walks the capture list. Both declarations of that array had 64 slots, and the store was `bad_captures_[bad_count_++] = move` with no bound check. The lock build leaves `FORGE_SDK_BADCAP_PREFIX` at 0 and sets `FORGE_SPD_NO_ZERO_MOVELISTS` to 2, so the live array is the uninitialized 64-slot one.

This position is legal, and neither king is in check:

```
3rQ2K/1n1Q1p2/1Q1n1Qp1/1p1Q1pRB/1Q1b1QpN/2bQ1pRB/4pQpN/kr3q2 w - - 0 1
```

It has 66 pseudo-legal captures, and `see_ge(move, 0)` is false for every one of them. A depth-1 search uses the main picker, so those captures are written into `bad_captures_`. On the unchanged lock the process dies during that search.

## The fix

Both `bad_captures_` arrays are now `MoveList::Capacity` (256) entries, the same bound as `moves_`, which already holds every generated capture. Every losing capture is still stored, in the same order. The bench and perft node counts measured below match the lock. A finite search that is not ponder now finishes when stdin closes, so `forge < tests_t2/losing_captures.uci` reaches the picker. `stop`, `quit`, `go infinite`, and ponder still abort.

## Files changed

- `forge-combo29/src/search.cpp`
- `forge-combo29/src/uci.cpp`
- `forge-combo29/tests_t2/losing_captures.uci`
- `forge-combo29/tests_t2/losing_captures.expected.txt`
- `forge-combo29/tests_t2/losing_captures.cpp`
- `forge-combo29/REPORT_t2.md`

The engine diff is the two array bounds, the comment above them, and the stdin wait in `uci.cpp`.

## Build

`/usr/bin/c++` on this machine is clang 18 and the link fails looking for `-lstdc++`. The builds below use `/usr/bin/g++` (g++ 13.3.0). The CPU supports AVX-512, so the lock's default `-march=x86-64-v4` was left as is.

Release:

```
cmake -S forge-combo29 -B /tmp/forge-lock-rel -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/forge-lock-rel -j
```

AddressSanitizer and UBSan (same sources, extra flags):

```
cmake -S forge-combo29 -B /tmp/forge-lock-asan -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ \
  -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g" \
  -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined"
cmake --build /tmp/forge-lock-asan -j
```

`go` starts the search on a worker and returns to the UCI loop. On the lock, a following `quit` or a closed stdin calls `stop_search()` before that worker reaches the move picker, and the overflow position then prints `bestmove h2f1`. The redirected run in "Redirected UCI fixture" is the check that the search now happens. The lock crash logs below used a pipe that stayed open until `bestmove` or the process died, because the lock itself aborts on EOF.

## Losing-capture count

Throwaway counter linked against the lock `board.cpp` objects. It calls `set_fen`, `generate_pseudo_legal(moves, true)`, and `see_ge(move, 0)`. It is not part of the commit.

```
/tmp/count_bad "3rQ2K/1n1Q1p2/1Q1n1Qp1/1p1Q1pRB/1Q1b1QpN/2bQ1pRB/4pQpN/kr3q2 w - - 0 1"
```

```
ok=1 stm_check=0 white_check=0 black_check=0 captures=66 losing=66 good=0 err= fen=3rQ2K/1n1Q1p2/1Q1n1Qp1/1p1Q1pRB/1Q1b1QpN/2bQ1pRB/4pQpN/kr3q2 w - - 0 1
```

## Unchanged lock, release

The release binary built from `lock/combo29-20261110` at `16833ecc`, before the edit. The shell reported `Segmentation fault` and exit status 139. stderr was empty. stdout:

```
rm -f /tmp/uci-lockrel.in
mkfifo /tmp/uci-lockrel.in
/tmp/forge-lock-rel/forge < /tmp/uci-lockrel.in > /tmp/forge-out/lock-rel-go.out 2>/tmp/forge-out/lock-rel-go.err &
echo $! > /tmp/uci-lockrel.pid
exec 3>/tmp/uci-lockrel.in
printf '%s\n' \
  'uci' 'isready' \
  'setoption name Threads value 1' \
  'setoption name Hash value 16' \
  'setoption name OwnBook value false' \
  'position fen 3rQ2K/1n1Q1p2/1Q1n1Qp1/1p1Q1pRB/1Q1b1QpN/2bQ1pRB/4pQpN/kr3q2 w - - 0 1' \
  'go depth 1' >&3
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
```

No `bestmove` line. Exit status 139.

## Unchanged lock, AddressSanitizer + UBSan

Same UCI input against the lock sources built with `-fsanitize=address,undefined`. The process aborted. stdout:

```
ASAN_OPTIONS=halt_on_error=1:abort_on_error=1:detect_leaks=0:symbolize=1 \
UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 \
/tmp/forge-lock-asan/forge
```

(stdin held open with the same `uci` / `isready` / `setoption` / `position` / `go depth 1` sequence as above)

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
```

stderr:

```
AddressSanitizer:DEADLYSIGNAL
=================================================================
==3922==ERROR: AddressSanitizer: SEGV on unknown address 0x7fa45ad33800 (pc 0x560aec81a9fb bp 0x7fa4559efa00 sp 0x7fa4559ef810 T1)
==3922==The signal is caused by a READ memory access.
    #0 0x560aec81a9fb in forge::nnue::update(forge::nnue::Accumulator const&, forge::nnue::Accumulator&, forge::nnue::DirtyPieces const&) /agent/repos/dwqww/forge-combo29/src/nnue.cpp:150
    #1 0x560aec835563 in forge::Worker::static_evaluate(forge::Board const&, forge::SearchStack*) /agent/repos/dwqww/forge-combo29/src/search.cpp:823
    #2 0x560aec855533 in forge::Worker::qsearch(forge::Board&, forge::SearchStack*, int, int) /agent/repos/dwqww/forge-combo29/src/search.cpp:1030
    #3 0x560aec85fc32 in forge::Worker::search(forge::Board&, forge::SearchStack*, int, int, int, bool) /agent/repos/dwqww/forge-combo29/src/search.cpp:1120
    #4 0x560aec86055b in forge::Worker::search(forge::Board&, forge::SearchStack*, int, int, int, bool) /agent/repos/dwqww/forge-combo29/src/search.cpp:1430
    #5 0x560aec874132 in forge::Worker::search(forge::Board, forge::SearchLimits const&, bool, std::vector<forge::Worker*, std::allocator<forge::Worker*> > const&) /agent/repos/dwqww/forge-combo29/src/search.cpp:1665
    #6 0x560aec8842b7 in forge::Searcher::search(forge::Board, forge::SearchLimits const&, bool, forge::Searcher::TTAccess) /agent/repos/dwqww/forge-combo29/src/search.cpp:1809
    #7 0x560aec8ca9fd in operator() /agent/repos/dwqww/forge-combo29/src/uci.cpp:357
    #8 0x7fa45c0ecdb3  (/lib/x86_64-linux-gnu/libstdc++.so.6+0xecdb3) (BuildId: 753c6c8608b61d4e67be8f0c890e03e0aa046b8b)
    #9 0x7fa45c45ea41 in asan_thread_start ../../../../src/libsanitizer/asan/asan_interceptors.cpp:234
    #10 0x7fa45b49cb83  (/lib/x86_64-linux-gnu/libc.so.6+0x9cb83) (BuildId: a4a7992a8e66555c8141ab2a08a8465ff6e0ea65)
    #11 0x7fa45b529ecb  (/lib/x86_64-linux-gnu/libc.so.6+0x129ecb) (BuildId: a4a7992a8e66555c8141ab2a08a8465ff6e0ea65)

AddressSanitizer can not provide additional info.
SUMMARY: AddressSanitizer: SEGV /agent/repos/dwqww/forge-combo29/src/nnue.cpp:150 in forge::nnue::update(forge::nnue::Accumulator const&, forge::nnue::Accumulator&, forge::nnue::DirtyPieces const&)
Thread T1 created by T0 here:
    #0 0x7fa45c4f51f9 in pthread_create ../../../../src/libsanitizer/asan/asan_interceptors.cpp:245
    #1 0x7fa45c0eceb0 in std::thread::_M_start_thread(std::unique_ptr<std::thread::_State, std::default_delete<std::thread::_State> >, void (*)()) (/lib/x86_64-linux-gnu/libstdc++.so.6+0xeceb0) (BuildId: 753c6c8608b61d4e67be8f0c890e03e0aa046b8b)
    #2 0x560aec69dd84 in thread<main()::<lambda()> > /usr/include/c++/13/bits/std_thread.h:164
    #3 0x560aec69dd84 in main /agent/repos/dwqww/forge-combo29/src/uci.cpp:354
    #4 0x7fa45b42a1c9  (/lib/x86_64-linux-gnu/libc.so.6+0x2a1c9) (BuildId: a4a7992a8e66555c8141ab2a08a8465ff6e0ea65)
    #5 0x7fa45b42a28a in __libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: a4a7992a8e66555c8141ab2a08a8465ff6e0ea65)
    #6 0x560aec6a67e4 in _start (/tmp/forge-lock-asan/forge+0x3597e4) (BuildId: 32f8e68f9c4b80b7376926c11c70e6f63be32aed)

==3922==ABORTING
```

## bench 11

Fixed release binary.

```
/tmp/forge-lock-rel/forge
```

stdin:

```
uci
isready
setoption name Threads value 1
setoption name Hash value 16
setoption name OwnBook value false
bench 11
quit
```

stdout:

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
info string bench depth 11 nodes 312866 time 159 nps 1967710
```

`bench depth 11 nodes 312866`. That is the lock pin.

## bench 13

Same options, then `bench 13` and `quit`.

stdout:

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
info string bench depth 13 nodes 862329 time 425 nps 2029009
```

`bench depth 13 nodes 862329`. That is the lock pin.

## perft 5

Same options, then `position startpos`, `go perft 5`, and `quit`.

stdout:

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

`nodes 4865609`. That is the lock pin.

These three commands were run again after the stdin change below. Node counts were the same: bench 11 `312866` (time 158), bench 13 `862329` (time 427), perft 5 `4865609`.

## Redirected UCI fixture

Closing stdin used to call `stop_search()` at the end of the UCI loop, which cancelled a finite `go` before the worker reached the move picker. `forge < tests_t2/losing_captures.uci` then printed `bestmove h2f1`. A finite search (not `infinite`, not `ponder`) now finishes when stdin closes. `stop` and `quit` still abort. `go infinite` still stops on EOF: that command printed `bestmove a2a3` and exited 0. `go depth 20` followed by `quit` also returned immediately with `bestmove a2a3` and no completed `info depth` line.

```
/tmp/forge-lock-rel/forge < forge-combo29/tests_t2/losing_captures.uci
```

Exit status 0. stderr was empty. The option list matches the bench runs above. The search lines were:

```
info depth 1 seldepth 9 score mate 1 nodes 186 nps 0 hashfull 0 time 0 pv b4a3
bestmove b4a3
```

`grep '^bestmove '` of that stdout compared equal to `tests_t2/losing_captures.expected.txt`.

The same command linked against `search.cpp` from `16833ecc` and the other release objects (including this `uci.cpp`) died with `Segmentation fault`, exit status 139. stdout stopped at `readyok`. There was no `bestmove` line. stderr was empty.

The same redirection under AddressSanitizer and UBSan (`ASAN_OPTIONS=halt_on_error=1:abort_on_error=1:detect_leaks=0:symbolize=1`, `UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1`) exited 0, stderr empty, and printed:

```
info depth 1 seldepth 9 score mate 1 nodes 186 nps 46500 hashfull 0 time 4 pv b4a3
bestmove b4a3
```

## In-process test

`tests_t2/losing_captures.cpp` calls `Searcher::search` at depth 1 with a 16 MB hash and one thread. It does not go through the UCI loop.

Objects come from the release build above, excluding `uci.cpp.o` (that file defines `main`). Same defines as `flags.make`.

```
DEFS="-DFORGE_EXPOSE_TUNABLES=1 -DFORGE_NNUE_HIDDEN=256 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_TT_NOTLS=1 -DNDEBUG"
FLAGS="-std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4"
g++ $FLAGS $DEFS -Iforge-combo29/include -c forge-combo29/tests_t2/losing_captures.cpp -o /tmp/losing_captures.o
g++ -o /tmp/losing_captures /tmp/losing_captures.o \
  /tmp/forge-lock-rel/CMakeFiles/forge.dir/src/bitboard.cpp.o \
  /tmp/forge-lock-rel/CMakeFiles/forge.dir/src/board.cpp.o \
  /tmp/forge-lock-rel/CMakeFiles/forge.dir/src/book.cpp.o \
  /tmp/forge-lock-rel/CMakeFiles/forge.dir/src/eval.cpp.o \
  /tmp/forge-lock-rel/CMakeFiles/forge.dir/src/eval_params.cpp.o \
  /tmp/forge-lock-rel/CMakeFiles/forge.dir/src/nnue.cpp.o \
  /tmp/forge-lock-rel/CMakeFiles/forge.dir/src/search.cpp.o -pthread
/tmp/losing_captures
```

Fixed sources, stdout:

```
bestmove b4a3
```

Exit status 0. stderr was empty. `cmp` against `tests_t2/losing_captures.expected.txt` exited 0.

The same test linked with `search.cpp.o` compiled from `16833ecc` (the lock) and the other release objects produced no stdout and no stderr. The shell reported `Segmentation fault` and exit status 139.

AddressSanitizer + UBSan, test and engine objects built with `-fsanitize=address,undefined -fno-omit-frame-pointer -g`, then:

```
ASAN_OPTIONS=halt_on_error=1:abort_on_error=1:detect_leaks=0:symbolize=1 \
UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 \
/tmp/losing_captures_asan
```

stdout:

```
bestmove b4a3
```

Exit status 0. stderr was empty (0 bytes).

## Test, release

Fixed release binary. The same UCI commands as `tests_t2/losing_captures.uci`, with stdin held open until `bestmove` and then `quit`. The redirected run above is the form that matches the file.

```
grep '^bestmove ' /tmp/forge-out/rel-go.out | cmp - forge-combo29/tests_t2/losing_captures.expected.txt
```

`cmp` exited 0.

stdout:

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
info depth 1 seldepth 9 score mate 1 nodes 186 nps 0 hashfull 0 time 0 pv b4a3
bestmove b4a3
```

stderr was empty (0 bytes).

## Test, AddressSanitizer + UBSan

Fixed sources, same sanitizer flags and the same UCI input.

```
ASAN_OPTIONS=halt_on_error=1:abort_on_error=1:detect_leaks=0:symbolize=1 \
UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 \
/tmp/forge-lock-asan/forge
```

```
grep '^bestmove ' /tmp/forge-out/asan-go.out | cmp - forge-combo29/tests_t2/losing_captures.expected.txt
```

`cmp` exited 0.

stdout:

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
info depth 1 seldepth 9 score mate 1 nodes 186 nps 46500 hashfull 0 time 4 pv b4a3
bestmove b4a3
```

stderr was empty (0 bytes). The search printed `score mate 1` and `bestmove b4a3` with 186 nodes. No AddressSanitizer or UBSan diagnostic.

## What could not be verified

- A build with `FORGE_SDK_BADCAP_PREFIX` enabled, or with `FORGE_SPD_NO_ZERO_MOVELISTS` left at 0, was not run. The lock defines the prefix as 0 and `FORGE_SPD_NO_ZERO_MOVELISTS` as 2, and that is the array that was rebuilt and searched.
- No position with more than 66 losing captures was searched. The new array has 256 slots, matching `moves_`. This position uses 66.
- clang was not used. `/usr/bin/c++` is clang 18 and does not link `-lstdc++` here.
- `windows/forge_clang_combo29_trial_w6.exe` was not rebuilt. This task allows text under `src`, `include`, `tests_t2`, and `REPORT_t2.md` only, and the commit cannot contain an executable.
- Nothing here is an Elo or speed claim. The `nps` and `time` fields above are the engine's own lines.
