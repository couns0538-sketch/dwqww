# t20 report: repeatable search and mate scores

## What was found

`ucinewgame` already calls `Searcher::clear()`. That zeros the transposition table (every cluster, the generation age counter back to 0, and the epoch), the pawn-evaluation cache, the main / capture / continuation histories, both correction tables, the counter-move table, and the per-thread search stack (killers included). It does not run at the start of every search. A second `go depth 10` on the start position in the same game, with no `ucinewgame` between them, changes the node count (13102, then 1774). After `ucinewgame` the move, score and node count match the first search again.

Skipping that clear is what the reports describe. With one thread, Hash 16 and the book off, stale history and a stale hash change the move or the score on later searches (measured on the same 30 positions). `Searcher::clear()` removes that. Node counters, time limits and the root-effort table are assigned at the start of `Worker::search` before they are read, so they do not leak into the next search. The shared stop flag is not cleared by `ucinewgame`; the next `go` calls `reset_stop()` before searching, and the test does the same. The book RNG in `uci.cpp` is not reset. It is not used when `OwnBook` is false, and depth / nodes searches do not probe the book.

No engine source was changed. The reset already sits on `ucinewgame`, and state from one move to the next inside a game is still there.

## Clear Hash (not changed)

`setoption name Clear Hash` calls `Searcher::clear_hash()`:

- `TranspositionTable::clear()` writes an empty cluster over every slot, sets `generation_` to 0 and increments `epoch_` (old probe handles cannot store).
- `Worker::clear_caches()` clears each thread's pawn-evaluation cache.

It does not clear main history, capture history, continuation history, correction tables, counter moves, killers or node counters. The test filled the table, called `clear_hash()`, and saw generation 0, a probe miss, and history still non-zero.

## Hash resize

`setoption name Hash value N` calls `Searcher::resize_hash`. That allocates a new zero-filled table, sets `generation_` to 0 and increments `epoch_`. It does not clear histories or the pawn cache. The next search calls `new_search()`, which advances generation from 0 to 1, the same first generation as the first search after `ucinewgame`. Resizing to the same 16 MiB already drops old entries. The test also resized 16 → 32 → 16 from a cleared history and the following `go depth 10` matched the search after `ucinewgame` (start position, 13102 nodes, `d2d4`, `cp 24`).

## `go mate N`

The engine accepts `mate`. `parse_limits` stores `SearchLimits::mate_moves` (clamped to 0..32). The search depth cap is `min(depth, 2*N-1)` (default depth 64, so the cap is `2*N-1`). After an iteration whose score is a mate and `MateValue - abs(score)` is at most that cap, iteration stops. That is a mate in N moves or shorter.

If reductions have not produced that mate score yet, the search runs to the cap and returns the best line it has, which may not be a mate. Observed on the KRK mate in 2 `8/8/8/8/2R5/k7/8/1K6 w - - 0 1`:

- `go mate 1` is not this position. On the KRK mate in 1, `go mate 1` stops at depth 1 with `score mate 1`.
- `go mate 2` stops at depth 3 (the cap) with `score cp 483`, move `c4g4`, not a mate.
- `go mate 6` (cap 11) stops at depth 5 with `score mate 2`, move `b1c2`, once that mate is in the score.
- `go mate 1` from the start position stops at depth 1 with `score cp 1`, move `d2d4`.

## Stalemate and checkmate at the root

A position with no legal move never enters the search loop that walks the tree. The driver emits one info line per depth up to the depth cap and returns. `best_move` stays the empty move (`from == to`). The UCI loop prints that as `bestmove 0000`. It does not crash or hang. Bare `go` uses depth 64, so the test's depth-64 search is that answer.

- Stalemate `4k3/4P3/4K3/8/8/8/8/8 b - - 0 1` and `7k/5K2/6Q1/8/8/8/8/8 b - - 0 1`: `bestmove 0000`, `score cp 0`.
- Checkmate `k7/1Q6/1K6/8/8/8/8/8 b - - 0 1`: `bestmove 0000`, score `-MateValue`, printed as `score mate 0`.

## Mate scores

Twelve positions, two for each of mate +1, +2, +3, -1, -2, -3. Six are KRK and six are KQK. An independent minimax in the test (not the engine score) is the ground truth. `go depth 8` printed `score mate N` with that sign and distance, and the move it played kept that distance (a mate in 1 checkmated; otherwise the resulting position had the remaining distance).

Not every short KRK mate is seen at depth 8. `8/8/8/8/8/8/8/k1KR4 w - - 0 1` is mate in 3 (1.Kc2 Ka2 2.Rd3 Ka1 3.Ra3#), and `go depth 8` on the UCI binary reported `score mate 4`. Search was not changed, so that miss is still there. The twelve positions in the test are ones both the minimax and the engine call the same mate.

## Files changed

- `forge-combo29/tests_t20/repeat_mate_test.cpp` (added)
- `forge-combo29/REPORT_t20.md` (added)

No file under `forge-combo29/src` or `forge-combo29/include` was edited. Engine diff is empty.

## Commands and output

The machine's `c++` is Clang 18, which selects GCC 14 and then fails to link `-lstdc++` (that library is present for GCC 13). CMake was pointed at `g++`. The CPU has AVX-512, so the portable switches were left off and `-march` stayed the CMake default `x86-64-v4`.

### Build

```
rm -rf build && cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ && cmake --build build -j
```

```
-- The CXX compiler identification is GNU 13.3.0
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Check for working CXX compiler: /usr/bin/g++ - skipped
-- Detecting CXX compile features
-- Detecting CXX compile features - done
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD - Success
-- Found Threads: TRUE
-- Configuring done (0.4s)
-- Generating done (0.0s)
-- Build files have been written to: /agent/repos/dwqww/build
[ 11%] Building CXX object CMakeFiles/forge.dir/src/board.cpp.o
[ 22%] Building CXX object CMakeFiles/forge.dir/src/book.cpp.o
[ 33%] Building CXX object CMakeFiles/forge.dir/src/bitboard.cpp.o
[ 44%] Building CXX object CMakeFiles/forge.dir/src/eval.cpp.o
[ 55%] Building CXX object CMakeFiles/forge.dir/src/eval_params.cpp.o
[ 66%] Building CXX object CMakeFiles/forge.dir/src/search.cpp.o
[ 77%] Building CXX object CMakeFiles/forge.dir/src/nnue.cpp.o
[ 88%] Building CXX object CMakeFiles/forge.dir/src/uci.cpp.o
[100%] Linking CXX executable forge
[100%] Built target forge
```

### Rule 7 numbers after this work

The engine binary is the one built above. Nothing under `src/` or `include/` changed after this build. The same three node counts were printed by this command before the test file existed (312866, 862329, 4865609). Times differ; the node counts do not.

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build/forge
```

```
info string bench depth 11 nodes 312866 time 166 nps 1884734
info string bench depth 13 nodes 862329 time 452 nps 1907807
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

Exit code 0.

### Tests (release objects, same defines as the engine)

```
g++ -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4 -Wall -Wextra -Wpedantic \
  -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_NNUE_HIDDEN=256 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_NNUE_ZMM=1 \
  -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 \
  -DFORGE_SPD_TT_NOTLS=1 -DNDEBUG \
  -I forge-combo29/include \
  forge-combo29/tests_t20/repeat_mate_test.cpp \
  build/CMakeFiles/forge.dir/src/board.cpp.o \
  build/CMakeFiles/forge.dir/src/bitboard.cpp.o \
  build/CMakeFiles/forge.dir/src/eval.cpp.o \
  build/CMakeFiles/forge.dir/src/eval_params.cpp.o \
  build/CMakeFiles/forge.dir/src/nnue.cpp.o \
  build/CMakeFiles/forge.dir/src/search.cpp.o \
  -pthread -o /tmp/t20_test
/tmp/t20_test
```

The compiler printed nothing. Exit code 0. Program output:

```
t20 Searcher threads 1 hash 16 book off
PASS repeat depth 10 [0] move d2d4 score cp 24 nodes 13102
PASS repeat depth 10 [1] move e2a6 score cp -130 nodes 33339
PASS repeat depth 10 [2] move c3d5 score cp -13 nodes 21512
PASS repeat depth 10 [3] move b4f4 score cp 129 nodes 12301
PASS repeat depth 10 [4] move a2a3 score cp -332 nodes 21762
PASS repeat depth 10 [5] move f6h5 score cp 687 nodes 9722
PASS repeat depth 10 [6] move h7h5 score cp -989 nodes 25590
PASS repeat depth 10 [7] move f3e5 score cp 115 nodes 34753
PASS repeat depth 10 [8] move h2f2 score cp 455 nodes 15572
PASS repeat depth 10 [9] move d2c3 score cp 1142 nodes 40691
PASS repeat depth 10 [10] move a3b3 score cp 105 nodes 4115
PASS repeat depth 10 [11] move e1f2 score cp 251 nodes 3436
PASS repeat depth 10 [12] move d1e2 score cp -1 nodes 34821
PASS repeat depth 10 [13] move b1c3 score cp 29 nodes 23472
PASS repeat depth 10 [14] move c2c4 score cp 576 nodes 6102
PASS repeat depth 10 [15] move h1d1 score mate 2 nodes 369
PASS repeat depth 10 [16] move g1f1 score mate -2 nodes 134
PASS repeat depth 10 [17] move a1a8 score mate 1 nodes 180
PASS repeat depth 10 [18] move 0000 score mate 0 nodes 0
PASS repeat depth 10 [19] move e1g1 score cp 467 nodes 8240
PASS repeat depth 10 [20] move e2d3 score cp 415 nodes 29144
PASS repeat depth 10 [21] move b5c6 score mate 4 nodes 4109
PASS repeat depth 10 [22] move g1g7 score mate 1 nodes 294
PASS repeat depth 10 [23] move d1a4 score cp 981 nodes 21156
PASS repeat depth 10 [24] move c1c6 score cp 418 nodes 15764
PASS repeat depth 10 [25] move c2c3 score cp 335 nodes 5530
PASS repeat depth 10 [26] move d6d1 score mate 3 nodes 1823
PASS repeat depth 10 [27] move c3d5 score cp 244 nodes 30054
PASS repeat depth 10 [28] move b3a3 score mate 1 nodes 182
PASS repeat depth 10 [29] move b1c2 score mate 2 nodes 1268
PASS repeat nodes 5000 [0] move d2d4 score cp 26 nodes 5000
PASS repeat nodes 5000 [1] move e2a6 score cp -170 nodes 5000
PASS repeat nodes 5000 [2] move h2h3 score cp -37 nodes 5000
PASS repeat nodes 5000 [3] move b4f4 score cp 121 nodes 5000
PASS repeat nodes 5000 [4] move a2a3 score cp -327 nodes 5000
PASS repeat nodes 5000 [5] move f6h5 score cp 517 nodes 5000
PASS repeat nodes 5000 [6] move g7g6 score cp -856 nodes 5000
PASS repeat nodes 5000 [7] move d4c5 score cp 171 nodes 5000
PASS repeat nodes 5000 [8] move h2f2 score cp 454 nodes 5000
PASS repeat nodes 5000 [9] move d2d3 score cp 994 nodes 5000
PASS repeat nodes 5000 [10] move a3b3 score cp 105 nodes 5000
PASS repeat nodes 5000 [11] move e1f2 score cp 251 nodes 5000
PASS repeat nodes 5000 [12] move g1f3 score cp 45 nodes 5000
PASS repeat nodes 5000 [13] move b1c3 score cp 37 nodes 5000
PASS repeat nodes 5000 [14] move c2c4 score cp 362 nodes 5000
PASS repeat nodes 5000 [15] move h1d1 score mate 2 nodes 2600
PASS repeat nodes 5000 [16] move g1f1 score mate -2 nodes 4514
PASS repeat nodes 5000 [17] move a1a8 score mate 1 nodes 1152
PASS repeat nodes 5000 [18] move 0000 score mate 0 nodes 0
PASS repeat nodes 5000 [19] move e1g1 score cp 469 nodes 5000
PASS repeat nodes 5000 [20] move e2f3 score cp 437 nodes 5000
PASS repeat nodes 5000 [21] move b5c6 score mate 3 nodes 5000
PASS repeat nodes 5000 [22] move g1g7 score mate 1 nodes 1860
PASS repeat nodes 5000 [23] move d1a4 score cp 1036 nodes 5000
PASS repeat nodes 5000 [24] move c1c8 score cp 444 nodes 5000
PASS repeat nodes 5000 [25] move c2c3 score cp 286 nodes 5000
PASS repeat nodes 5000 [26] move d6d1 score mate 3 nodes 5000
PASS repeat nodes 5000 [27] move c3d5 score cp 91 nodes 5000
PASS repeat nodes 5000 [28] move b3a3 score mate 1 nodes 1154
PASS repeat nodes 5000 [29] move b1c2 score mate 2 nodes 4610
PASS in-game state carries: nodes 13102 then 1774, after ucinewgame 13102
PASS hash resize: generation 2 -> 0, probe miss, hashfull 0, history kept (76 entries); Clear Hash generation 0 probe miss, history kept (95); depth 10 after resize matches ucinewgame, nodes 13102
PASS KRK mate 1 score mate 1 move b3a3 keeps the mate
PASS KQK mate 1 score mate 1 move d1a4 keeps the mate
PASS KRK mate 2 score mate 2 move b1c2 keeps the mate
PASS KQK mate 2 score mate 2 move b1c2 keeps the mate
PASS KRK mate 3 score mate 3 move e1e5 keeps the mate
PASS KQK mate 3 score mate 3 move a1b2 keeps the mate
PASS KRK mate -1 score mate -1 move a2a1 keeps the mate
PASS KQK mate -1 score mate -1 move a1a2 keeps the mate
PASS KRK mate -2 score mate -2 move a1a2 keeps the mate
PASS KQK mate -2 score mate -2 move a1a2 keeps the mate
PASS KRK mate -3 score mate -3 move a1a2 keeps the mate
PASS KQK mate -3 score mate -3 move c1d1 keeps the mate
go mate 1 KRK mate in 1: depth 1 cap 1 score mate 1 move b3a3 nodes 20
go mate 6 KRK mate in 2: depth 5 cap 11 score mate 2 move b1c2 nodes 437
go mate 2 KRK mate in 2: depth 3 cap 3 score cp 483 move c4g4 nodes 141
go mate 1 startpos: depth 1 cap 1 score cp 1 move d2d4 nodes 26
PASS go mate
PASS stalemate KPk bestmove 0000 score cp 0 depth 64
PASS stalemate KQk bestmove 0000 score cp 0 depth 64
PASS checkmate KQk bestmove 0000 score mate 0 depth 64
t20 result: PASS
```

### Tests built with `-fsanitize=address,undefined`

```
g++ -std=c++20 -O1 -g -fno-omit-frame-pointer -fsanitize=address,undefined -ffp-contract=off -fno-fast-math -march=x86-64-v4 -Wall -Wextra \
  -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_NNUE_HIDDEN=256 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_NNUE_ZMM=1 \
  -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 \
  -DFORGE_SPD_TT_NOTLS=1 -DNDEBUG \
  -I forge-combo29/include \
  forge-combo29/tests_t20/repeat_mate_test.cpp \
  forge-combo29/src/board.cpp \
  forge-combo29/src/bitboard.cpp \
  forge-combo29/src/eval.cpp \
  forge-combo29/src/eval_params.cpp \
  forge-combo29/src/nnue.cpp \
  forge-combo29/src/search.cpp \
  -pthread -o /tmp/t20_test_asan
/tmp/t20_test_asan
```

The compiler printed nothing. The process printed the same bytes as the release run above (`diff` against that output was empty) and nothing on stderr. AddressSanitizer and UndefinedBehaviorSanitizer reported no error. Exit code 0. Last line: `t20 result: PASS`.

## What was not verified

- Searches with more than one thread.
- Clock searches (`wtime`, `movetime`). Those stop on the clock, so the node count is not a function of the position alone.
- `OwnBook true`. The book RNG in `uci.cpp` is not cleared by `ucinewgame`. Depth and nodes searches do not ask the book.
- Ponder and `searchmoves`.
- That every KRK or KQK mate in 3 is the score at depth 8. One counterexample is recorded above; search was left as it is.
- That `go mate N` returns a mate whenever a mate in N exists. `go mate 2` on the tested mate in 2 stops at the depth cap with a centipawn score.
- A byte-level compare of the pawn cache after `Clear Hash` versus after `Hash`. The source clears that cache only in `clear_hash` / `ucinewgame`, not in `resize_hash`. The test checked the transposition table and the history table.
- The `forge` process reading UCI text for the 30 positions. The test calls `Searcher::clear`, `reset_stop` and `search(..., TTAccess::Exclusive)`, which is what `ucinewgame` and `go` call. Bench and perft were run through the `forge` binary.
