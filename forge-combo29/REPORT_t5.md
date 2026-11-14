# Task 5: two-thread KRK mate, and stale history

## What was wrong

With `Threads 2`, a depth-14 search of a king-and-rook ending does not stay on the mate that `Threads 1` proves. Helper threads write the shared transposition table. A PV node may skip legal moves (late-move pruning, history pruning, futility, SEE) and still store `BoundExact` or `BoundUpper`. `BoundExact` replaces the existing entry at any depth, so a helper store overwrites the main thread's mate score. The main thread then cuts off and reports a different move, sometimes a centipawn score. Helper probes also rewrite an entry's generation, which changes which slot the main thread replaces.

With `Threads 1`, the history tables live until `ucinewgame`. They are indexed by from-square and to-square, not by position. After another search, and after `Clear Hash` has wiped the table, the same ending can play a different move and lose the mate score. `ucinewgame` hides this because it clears the histories.

## Fix

Helper threads still read the table and still search, but they no longer store entries and they no longer refresh generation on a probe. The main thread's stores are unchanged, so a one-thread search builds the same table as before. Every search, on every worker, clears that worker's history tables before the root. Bench already clears those tables before each position, and the depth-11 and depth-13 node counts stayed on the lock pins.

## Files

- `forge-combo29/include/forge/search.hpp`
- `forge-combo29/src/search.cpp`
- `forge-combo29/tests_t5/krk_mate_test.cpp`
- `forge-combo29/REPORT_t5.md`

Engine diff: 38 insertions, 16 deletions (`git diff --numstat`). No change to `CMakeLists.txt`.

The test links `Searcher` directly (`TTAccess::Exclusive`, Hash 16). It fails on the lock sources and passes after the change. `UseNNUE` is off for the mate checks. One extra block leaves the net on and only checks that two threads repeat the one-thread move and score.

## Commands

Working directory: `/agent/repos/dwqww`. Compiler: `g++-13` (this machine's Clang 18 does not link). CPU supports the lock `-march=x86-64-v4` build. The test binary is not part of the branch.

### Test linked to the unchanged lock (`16833ecc`)

This was compiled and run before the source edit. Exit status 1.

```
g++-13 -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4 \
  -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 \
  -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
  -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 \
  -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 \
  -I forge-combo29/include \
  forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp \
  forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp \
  forge-combo29/src/nnue.cpp forge-combo29/src/book.cpp \
  forge-combo29/src/search.cpp \
  forge-combo29/tests_t5/krk_mate_test.cpp \
  -pthread -o /tmp/krk_mate_test_lock && /tmp/krk_mate_test_lock; echo EXIT:$?
```

```
fresh 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 mate 7 c4c6
after-startpos 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 cp 433 c4b4
history FAIL
fresh 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 mate 17 b3f3
after-startpos 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 cp 539 b3f3
history FAIL
fresh 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 mate 3 d1d4
after-startpos 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 mate 3 d1d4
history ok
t1 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 mate 7 c4c6
threads2 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 runs 30 mismatches 19 first mate 9 e8d7
threads FAIL
t1 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 mate 17 b3f3
threads2 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 runs 30 mismatches 29 first cp 481 b3b8
threads FAIL
t1 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 mate 3 d1d4
threads2 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 runs 30 mismatches 1 first mate 3 d1e1
threads FAIL
nnue-t1 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 cp 476 e8e7
nnue-threads2 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 runs 20 mismatches 20 first cp 496 c4c5
threads FAIL
FAILED 6
EXIT:1
```

`3k4/8/3K4/8/8/8/8/3R4` did not change after a start-position search on the lock. The other two history cases did. Two threads missed or changed the one-thread result on every position, including with the net left on (there the one-thread score is a centipawn score, not a mate).

### Test linked to this change

Same command, output `/tmp/krk_mate_test`. Exit status 0.

```
g++-13 -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4 \
  -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 \
  -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
  -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 \
  -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 \
  -I forge-combo29/include \
  forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp \
  forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp \
  forge-combo29/src/nnue.cpp forge-combo29/src/book.cpp \
  forge-combo29/src/search.cpp \
  forge-combo29/tests_t5/krk_mate_test.cpp \
  -pthread -o /tmp/krk_mate_test && /tmp/krk_mate_test; echo EXIT:$?
```

```
fresh 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 mate 7 c4c6
after-startpos 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 mate 7 c4c6
history ok
fresh 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 mate 17 b3f3
after-startpos 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 mate 17 b3f3
history ok
fresh 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 mate 3 d1d4
after-startpos 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 mate 3 d1d4
history ok
t1 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 mate 7 c4c6
threads2 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 runs 30 mismatches 0
threads ok
t1 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 mate 17 b3f3
threads2 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 runs 30 mismatches 0
threads ok
t1 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 mate 3 d1d4
threads2 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 runs 30 mismatches 0
threads ok
nnue-t1 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 cp 476 e8e7
nnue-threads2 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 runs 20 mismatches 0
threads ok
ok
EXIT:0
```

### AddressSanitizer and UndefinedBehaviorSanitizer

`-O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer`, same defines. No sanitizer diagnostic. Exit status 0.

```
g++-13 -std=c++20 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
  -ffp-contract=off -fno-fast-math -march=x86-64-v4 \
  -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 \
  -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
  -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 \
  -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 \
  -I forge-combo29/include \
  forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp \
  forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp \
  forge-combo29/src/nnue.cpp forge-combo29/src/book.cpp \
  forge-combo29/src/search.cpp \
  forge-combo29/tests_t5/krk_mate_test.cpp \
  -pthread -o /tmp/krk_mate_test_asan && /tmp/krk_mate_test_asan; echo EXIT:$?
```

```
fresh 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 mate 7 c4c6
after-startpos 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 mate 7 c4c6
history ok
fresh 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 mate 17 b3f3
after-startpos 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 mate 17 b3f3
history ok
fresh 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 mate 3 d1d4
after-startpos 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 mate 3 d1d4
history ok
t1 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 mate 7 c4c6
threads2 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 runs 30 mismatches 0
threads ok
t1 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 mate 17 b3f3
threads2 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 runs 30 mismatches 0
threads ok
t1 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 mate 3 d1d4
threads2 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 runs 30 mismatches 0
threads ok
nnue-t1 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 cp 476 e8e7
nnue-threads2 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 runs 20 mismatches 0
threads ok
ok
EXIT:0
```

### Engine build, bench 11, bench 13, perft 5

`Threads 1`, `Hash 16`, `OwnBook false`. Bench builds its own 16 MB, one-thread searcher. Perft is from the start position.

```
cmake -S forge-combo29 -B /tmp/forge-t5 -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++-13 && cmake --build /tmp/forge-t5 -j4
```

Configure and compile completed. The link line ended with `[100%] Built target forge`.

```
printf 'uci\nsetoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/forge-t5/forge
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
info string bench depth 11 nodes 312866 time 160 nps 1955412
info string bench depth 13 nodes 862329 time 421 nps 2048287
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

Pins: `bench 11` = 312866, `bench 13` = 862329, `go perft 5` = 4865609.

## Helper stores and node-limited depth

A review of the first patch asked for helper threads to publish results again. Sharing every fail-high was measured, and it brings the mate miss back. On the same three positions, with helpers storing only `BoundLower` and not replacing a current-generation exact entry, two threads missed the mate 10 of 30 and 16 of 30 times (`cp 438 c4b4`, `cp 494 b3e3`). Ignoring those centipawn scores in the main thread, and refusing to overwrite a main-thread entry, still missed (11 of 30 and 18 of 30). The entries occupy cluster slots and change which entry the main thread keeps. The patch therefore still drops helper stores.

`go nodes 1000000` from the start position, Hash 16, `UseNNUE true`, `OwnBook false`, one run each:

| threads | lock depth | this patch |
| --- | --- | --- |
| 1 | 19 cp 15 d2d4 | 19 cp 15 d2d4 |
| 2 | 17 cp 22 e2e4 | 16 cp 35 e2e4 |
| 4 | 17 cp 11 d2d4 | 15 cp 27 e2e4 |

The lock already searches a lower depth once helper nodes count toward the limit. This patch is one ply lower at two threads and two plies lower at four, because those nodes no longer fill the table. One thread is unchanged. This is not a speed claim.

## Not verified

- The reported 57 of 400 and 0 of 100 counts. No position list came with the task. The counts above are the runs in `tests_t5/krk_mate_test.cpp` only.
- A king-and-rook position where `UseNNUE true` and `Threads 1` at depth 14 already prints a mate, and `Threads 2` used to miss it. On `4K3/k7/8/8/2R5/8/8/8 w - - 0 1` the net-on one-thread search scores `cp 476`, not a mate. Two threads now repeat that same score and move (0 mismatches in 20). The missed-mate runs are with `UseNNUE false`.
- More than two threads.
- Clock-limited games. History is cleared at the start of those searches too. Bench and perft do not cover a timed game.
- Whether helper threads still change the main search under a node limit. `should_stop` on the main thread counts helper nodes, and this task did not change that. The depth-14 tests set no node limit.
- Playing strength or speed. Nothing here is an Elo or NPS claim. The bench `nps` lines are the raw timer output.
- The release binary under AddressSanitizer. The sanitizer run is the test at `-O1`. The `#else` path of `FORGE_SPD_TT_NOTLS` is compiled out of this build (`FORGE_SPD_TT_NOTLS=1`); it has the same helper-write guards in source and was not linked.
- Clang, and any non-Linux host.
