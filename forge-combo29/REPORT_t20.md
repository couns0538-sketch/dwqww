# t20: what changed, what was found, what was wrong

## What changed

No engine source changed. `forge-combo29/src` and `forge-combo29/include` are the lock. The branch adds:

- `forge-combo29/tests_t20/repeat_mate_test.cpp`
- `forge-combo29/REPORT_t20.md`

`ucinewgame` already calls `Searcher::clear()` (`src/uci.cpp`). That is the reset. It was not moved to the start of every search, because history carried from move to move inside one game is what the search is built to use. Bench 11, bench 13 and perft 5 are unchanged: 312866, 862329, 4865609.

## What was found

One process, one thread, hash 16 MiB, book off, the same `go` entry the UCI loop uses (`TTAccess::Exclusive`).

Search a position from a cleared engine. Then search other positions. Then search the first position again **without** `ucinewgame`. The answer changes. Do the same three times **with** `ucinewgame` (`Searcher::clear()`) between them and the move, the score and the node count match. That held for all 30 positions at `go depth 10` and at `go nodes 5000`.

A second `go depth 10` on the start position, still inside the same game, is a different search: 13102 nodes the first time, 1774 the second. After `ucinewgame` it is 13102 again. So the tables are doing their job between moves, and they are the thing that makes two games disagree when they are not cleared.

## What was wrong

The failure is one `Searcher` remembering the previous game. `go` does not wipe that memory. Only `ucinewgame` does. A GUI or a match runner that sends `position` and `go` for a new game without `ucinewgame` gets a different move in an ending, on one thread, with a fixed depth or a fixed node limit. Nothing about the clock is involved.

### Measured move changes

Each line is: clear, `go` the position, `go` the other nine positions, `go` the position again with the tables still warm. Hash 16, Threads 1, exclusive table access.

`go depth 10` on `8/8/4k3/8/8/8/3K4/7Q w - - 0 1` (king and queen versus king):

- cleared: `d2c3`, score 1142, 40691 nodes
- warm: `h1h4`, score 1138, 5741 nodes

The best move changed. The node count fell by about seven times because the old hash and the old history cut and ordered the tree differently.

`go nodes 5000` on `6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1`:

- cleared: `g7g6`, score -856
- warm: `g7g5`, score -946

`go nodes 5000` on the same king-and-queen position:

- cleared: `d2d3`, score 994
- warm: `d2c2`, score 982

On the positions where the move stayed, the score or the node count still moved. Start position, depth 10: `d2d4` both times, score 24 and 13102 nodes when cleared, score 32 and 6625 nodes when warm. After `ucinewgame` those pairs match again.

That table was this program, linked against the release objects of the unchanged engine (`TTAccess::Exclusive`, the same access `go` uses). Full output:

```
g++ -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4 -DNDEBUG \
  -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_NNUE_HIDDEN=256 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_NNUE_ZMM=1 \
  -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_TT_NOTLS=1 \
  -I forge-combo29/include /tmp/t20_wrong.cpp \
  build/CMakeFiles/forge.dir/src/board.cpp.o \
  build/CMakeFiles/forge.dir/src/bitboard.cpp.o \
  build/CMakeFiles/forge.dir/src/eval.cpp.o \
  build/CMakeFiles/forge.dir/src/eval_params.cpp.o \
  build/CMakeFiles/forge.dir/src/nnue.cpp.o \
  build/CMakeFiles/forge.dir/src/search.cpp.o \
  -pthread -o /tmp/t20_wrong
/tmp/t20_wrong
```

```
DEPTH
0 DIFFER clean d2d4 24 13102 stale d2d4 32 6625
1 DIFFER clean e2a6 -130 33339 stale e2a6 -130 13284
2 DIFFER clean b4f4 129 12301 stale b4f4 176 7317
3 DIFFER clean h7h5 -989 25590 stale h7h5 -985 4435
4 DIFFER clean h1f1 404 15206 stale h1f1 477 13917
5 DIFFER clean d2c3 1142 40691 stale h1h4 1138 5741
6 DIFFER clean a3b3 105 4115 stale a3b3 105 878
7 DIFFER clean e1f2 251 3436 stale e1f2 343 5311
8 DIFFER clean d1e2 -1 34821 stale d1e2 -2 5327
9 DIFFER clean h1d1 31997 369 stale h1d1 31997 234
NODES
0 DIFFER clean d2d4 26 5000 stale d2d4 33 5000
1 DIFFER clean e2a6 -170 5000 stale e2a6 -186 5000
2 DIFFER clean b4f4 121 5000 stale b4f4 120 5000
3 DIFFER clean g7g6 -856 5000 stale g7g5 -946 5000
4 DIFFER clean h1f1 424 5000 stale h1f1 425 5000
5 DIFFER clean d2d3 994 5000 stale d2c2 982 5000
6 same clean a3b3 105 5000 stale a3b3 105 5000
7 DIFFER clean e1f2 251 5000 stale e1f2 321 5000
8 DIFFER clean g1f3 45 5000 stale g1f3 23 5000
9 DIFFER clean h1d1 31997 2600 stale h1d1 31997 1481
```

Index 5 is `8/8/4k3/8/8/8/3K4/7Q w - - 0 1`. Index 3 is `6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1`. Index 0 is the start position. The source of that probe was not committed. The committed test is the one that checks the three repeats match after `clear()`.

### How the leftover state changes the move

`Searcher::search` calls `TranspositionTable::new_search()` before the workers run. That only does `generation_ = (generation_ + 1) & 31`. It does not empty the table. Entries from the previous search stay. A later search of the same position takes those scores, bounds, depths and hash moves as cutoffs and as the first move tried. A search of a different position still collides into the same clusters, and the replacement decision uses depth minus four times the generation age. Old entries therefore change which line is stored and which line is cut. That is why the warm depth-10 search of the start position visits 6625 nodes instead of 13102.

The history tables are not touched at the start of a search either. They are updated on cutoffs and on new PV moves (`update_quiet_stats`, `update_capture_stats`, `update_continuation`, and the fail-low continuation update). The next search orders quiets by that history and changes late-move reduction by `history / LmrHistoryDivisor`, clamped to -2..2 (`src/search.cpp` around the reduction). A quiet that was good in the previous game is tried earlier and reduced less. In a king ending that is enough to swap `g6` and `g5`, or `Kc3` and `Qh4`.

The correction tables are added onto the static evaluation (`corrected_eval`). A pawn key or a material key filled by the previous game shifts the eval, which moves the futility, razoring and null-move margins. The counter-move table is tried by the move picker before the quiet list, so a reply learned in another game is inserted into this one when the previous piece and square match.

Those four stores (hash, history, correction, counters) are the leak. They are exactly what `Worker::clear` and `TranspositionTable::clear` wipe, and `ucinewgame` calls both through `Searcher::clear()`:

- hash clusters zeroed, `generation_` set to 0, `epoch_` incremented so an old probe cannot write back
- pawn-evaluation cache
- main history, capture history, continuation history
- correction history and material correction
- counter moves
- the search stack, killers included

After that clear, the next search's `new_search()` sets generation to 1, the same value as the first search of a fresh engine. The test checked that: three repeats, unrelated searches in between, identical move, score and nodes.

### What is not the leak

Killers live on the search stack. `Worker::search` sets `ss.killers = {}` before iterative deepening, and `clear()` assigns a fresh stack as well. A killer from the previous search is not still there.

Node counters, seldepth, null-move statistics, the root-effort array and the soft and hard time limits are assigned at the top of `Worker::search` before they are read. A depth or nodes search does not stop on a time limit left behind by an older `go`.

`ucinewgame` does leave `shared_.stop` set, because `stop_search()` raises it and `clear()` does not lower it. The next `go` calls `reset_stop()` before `search()`. The test does the same. A search that forgot `reset_stop()` would abort on the first node-check and return a shallow move. The UCI `go` path does not forget it.

The book RNG in `main` is not cleared. `OwnBook false` never reads it, and a depth or nodes `go` does not ask the book even when the book is on (`game_search` requires a clock or a movetime).

### Clear Hash does not fix it

`setoption name Clear Hash` calls `Searcher::clear_hash()` only. That empties the transposition table (generation 0, epoch bumped) and the pawn cache (`Worker::clear_caches`). It leaves history, continuation, correction, counter moves and killers. After a search, `clear_hash()` was observed with generation 0, a miss on the position just searched, and 95 main-history entries still non-zero. A new game that only presses Clear Hash still has the history leak above.

### Hash resize does fix the table, and only the table

`setoption name Hash value N` always reallocates (`TranspositionTable::resize`), even when N is already the current size. The new clusters are value-initialised empty, generation is 0, epoch increments. History is kept on purpose. From a cleared engine, resize 16 to 32 and back to 16, then `go depth 10` on the start position, matched the search after `ucinewgame`: `d2d4`, score 24, 13102 nodes.

### The mate score is wrong on some forced mates

`go depth 8` is deep enough for mate in 3 (five plies) when the search actually reaches the mating move at full depth. It does not always do that.

`8/8/8/8/8/8/8/k1KR4 w - - 0 1` is white king c1, black king a1, rook d1. This line checkmates in three white moves, checked with the legal-move generator:

1. `c1c2` (check, one legal reply) `a1a2`
2. `d1d3` (one legal reply) `a2a1`
3. `d3a3` checkmate, zero legal moves

`go depth 8` on `./build/forge`, after `ucinewgame`, printed this. The command was `setoption name Threads value 1`, `setoption name Hash value 16`, `setoption name OwnBook value false`, `ucinewgame`, `position fen 8/8/8/8/8/8/8/k1KR4 w - - 0 1`, `go depth 8`. The `uciok` option list is omitted:

```
info depth 1 seldepth 2 score cp 474 nodes 18 nps 0 hashfull 0 time 0 pv d1h1
info depth 2 seldepth 2 score cp 422 nodes 48 nps 0 hashfull 0 time 0 pv d1d5 a1a2
info depth 3 seldepth 4 score cp 436 nodes 85 nps 0 hashfull 0 time 0 pv d1d5 a1a2 d5a5 a2b3
info depth 4 seldepth 6 score cp 427 nodes 170 nps 0 hashfull 0 time 0 pv d1d5 a1a2 d5a5 a2b3 a5b5 b3c3
info depth 5 seldepth 8 score cp 454 nodes 392 nps 0 hashfull 0 time 0 pv c1c2 a1a2 d1d5 a2a3 d5a5 a3b4
info depth 6 seldepth 9 score cp 464 nodes 702 nps 0 hashfull 0 time 0 pv c1c2 a1a2 d1d7 a2a3 d7a7 a3b4 a7b7 b4a3
info depth 7 seldepth 10 score mate 4 nodes 848 nps 848000 hashfull 0 time 1 pv c1c2 a1a2 d1d7 a2a3 d7d4 a3a2 d4a4
info depth 8 seldepth 10 score mate 4 nodes 933 nps 933000 hashfull 0 time 1 pv c1c2 a1a2 d1d7 a2a3 d7d4 a3a2 d4a4
bestmove c1c2
```

`c1c2` is the right first move. The PV then plays `d1d7` and mates on the seventh ply (`d4a4`), which `format_score` prints as mate 4 (`(distance + 1) / 2` with distance 7). The three-move mate `d1d3` is absent from every depth. Mate 4 is a real win. It is not the distance.

The search is built so that miss can happen at this depth. Late-move reduction at the root applies when `depth >= 2` and `move_count > 2` (`move_count > 1 + (root_node ? 1 : 0)`). A reduced move is searched again at full depth only when the reduced score beats alpha. Check extension requires `!root_node`, so the checking root move `c1c2` is not extended. Depth 5 is the first iteration that plays `c1c2`, and it follows `d1d5`, still a centipawn score. Depth 7 is the first mate score, and it is the longer mate.

The twelve mates in the test are positions where an independent minimax and `go depth 8` agree, and the played move leaves that same distance. The miss above is still in the lock. Search was not edited, because changing reduction or extensions changes the bench node counts.

Root checkmate is a separate score bug. `k7/1Q6/1K6/8/8/8/8/8 b - - 0 1` has no legal move and the king is in check. The driver sets `score = -MateValue` (`-32000`) and never searches. `format_score` does `distance = 32000 - 32000 = 0`, `mate = 1/2 = 0`, and prints `mate 0` because `-0` for an `int` is `0`. The side to move is already mated, so the distance is not a one-move mate and not a drawn score. `bestmove` is still `0000` (`from == to` in `src/uci.cpp`). Stalemate on the same path uses score 0 and prints `cp 0`, also `bestmove 0000`. Neither case hangs: the loop emits depths 1..64 and returns.

### `go mate N` gives up before the mate is proved

The command is accepted. `mate_moves` is clamped to 0..32. The depth cap is `min(depth, 2*N-1)`. With the default depth 64 that cap is `2*N-1`, the ply length of a mate in N. The loop also breaks when the score is already a mate and `MateValue - abs(score)` is within that cap.

On the KRK mate in 2 `8/8/8/8/2R5/k7/8/1K6 w - - 0 1` the mate is `b1c2 a3a2 c4a4`. `go depth 8` finds `score mate 2`. `go mate 2` caps the search at depth 3. At depth 3 the reductions have not proved the mate, so it stops on the cap with `score cp 483` and `bestmove c4g4`. `go mate 6` (cap 11) does prove it and stops at depth 5 with `score mate 2` and `b1c2`, short of the cap. `go mate 1` on the mate-in-1 rook position stops at depth 1 with `score mate 1`. `go mate 1` on the start position stops at depth 1 with `score cp 1` and `d2d4`, because there is no mate inside one ply.

So `go mate N` stops when it has a mate in N or shorter inside the iterations it ran. It also stops at ply `2*N-1` when it does not have one yet, and then the best move need not be a mating move.

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
